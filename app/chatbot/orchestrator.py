import re
from datetime import date, datetime, time, timedelta
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.chatbot.time_utils import resolve_booking_time
from app.services.llm.conversation import (
    generate_safe_response,
)

from app.services.llm.fast_router import (
    fast_route,
)

from app.services.llm.safety_router import (
    safety_route,
)

from app.chatbot.session import (
    load_session,
    save_session,
)
from app.core.database import AsyncSessionFactory
from app.models.doctor import Doctor
from app.models.schedule import DoctorSlot
from app.services.appointment_service import (
    AppointmentNotFoundError,
    AppointmentService,
    AppointmentStateError,
    BookingError,
    SlotUnavailableError,
)
from app.services.availability_service import AvailabilityService
from app.services.doctor_service import DoctorService

# MEDIBOOK_FOLLOWUP_CONTEXT_PATCH_V2
from app.chatbot.followup_context import (
    capture_context as _mb_capture_context_v2,
    normalize_for_context as _mb_normalize_context_v2,
)


DHAKA = ZoneInfo("Asia/Dhaka")


CONFIRM_PHRASES = {
    "confirm",
    "yes",
    "yes confirm",
    "yes, confirm",
    "confirm it",
    "go ahead",
    "yes do it",
    "do it",
}


ABORT_PHRASES = {
    "cancel",
    "stop",
    "never mind",
    "nevermind",
    "don't",
    "do not",
    "keep it",
    "keep appointment",
    "keep the appointment",
}


BOOKING_HINTS = (
    "book",
    "reserve",
    "make appointment",
    "schedule appointment",
)


AVAILABILITY_HINTS = (
    "available",
    "availability",
    "free",
    "slots",
    "slot",
    "times",
    "schedule",
)


LIST_APPOINTMENT_HINTS = (
    "my appointments",
    "my appointment",
    "appointments do i have",
    "appointment do i have",
    "show appointments",
    "show my booking",
    "show my bookings",
    "my bookings",
    "what did i book",
    "upcoming appointment",
)


CANCEL_APPOINTMENT_HINTS = (
    "cancel",
    "cancel my appointment",
    "cancel appointment",
    "cancel booking",
    "cancel it",
    "remove appointment",
)


RESCHEDULE_HINTS = (
    "reschedule",
    "move my appointment",
    "move appointment",
    "change appointment",
    "change the time",
    "change time",
    "change the date",
    "move it to",
)


def normalize(text: str) -> str:
    return " ".join(
        text.lower().strip().split()
    )


def today_dhaka() -> date:
    return datetime.now(
        DHAKA
    ).date()


def contains_any(
    message: str,
    values: tuple[str, ...],
) -> bool:
    text = normalize(message)

    return any(
        value in text
        for value in values
    )


def resolve_date(
    message: str,
    remembered_date: str | None = None,
) -> date | None:

    text = normalize(message)

    today = today_dhaka()

    if "day after tomorrow" in text:
        return today + timedelta(days=2)

    if "tomorrow" in text:
        return today + timedelta(days=1)

    if "today" in text:
        return today

    iso = re.search(
        r"\b(20\d{2}-\d{2}-\d{2})\b",
        message,
    )

    if iso:
        try:
            return date.fromisoformat(
                iso.group(1)
            )
        except ValueError:
            pass

    if remembered_date:
        try:
            return date.fromisoformat(
                remembered_date
            )
        except ValueError:
            pass

    return None


def resolve_time(
    message: str,
) -> time | None:

    text = normalize(message)

    match_24 = re.search(
        r"\b([01]?\d|2[0-3]):([0-5]\d)\b",
        text,
    )

    if match_24:
        return time(
            int(match_24.group(1)),
            int(match_24.group(2)),
        )

    match_12 = re.search(
        r"\b(1[0-2]|0?[1-9])"
        r"(?::([0-5]\d))?"
        r"\s*(am|pm)\b",
        text,
    )

    if match_12:
        hour = int(
            match_12.group(1)
        )

        minute = int(
            match_12.group(2) or 0
        )

        period = match_12.group(3)

        if period == "pm" and hour != 12:
            hour += 12

        if period == "am" and hour == 12:
            hour = 0

        return time(
            hour,
            minute,
        )

    return None


def format_time(
    value: str | time,
) -> str:

    if isinstance(value, str):
        parsed = time.fromisoformat(
            value
        )
    else:
        parsed = value

    return parsed.strftime(
        "%I:%M %p"
    ).lstrip("0")


def format_date(
    value: str,
) -> str:

    parsed = date.fromisoformat(
        value
    )

    return parsed.strftime(
        "%d %b %Y"
    )


def parse_phone(
    message: str,
) -> str | None:

    match = re.search(
        r"(?:\+?88)?01[3-9]\d{8}",
        message,
    )

    if not match:
        return None

    phone = match.group(0)

    if phone.startswith("+88"):
        phone = phone[3:]

    elif (
        phone.startswith("88")
        and len(phone) == 13
    ):
        phone = phone[2:]

    return phone


def parse_patient_details(
    message: str,
) -> tuple[str, str] | None:

    phone = parse_phone(
        message
    )

    if not phone:
        return None

    name = re.sub(
        r"(?:\+?88)?01[3-9]\d{8}",
        "",
        message,
    )

    name = re.sub(
        r"\b(my name is|name is|i am|i'm)\b",
        "",
        name,
        flags=re.IGNORECASE,
    )

    name = name.replace(
        ",",
        " ",
    )

    name = " ".join(
        name.split()
    ).strip()

    if len(name) < 2:
        return None

    return name, phone


def extract_confirmation_code(
    message: str,
) -> str | None:
    """
    Extract a MediBook confirmation code robustly.

    Supports both the canonical form:

        MED-1E3D139C96

    and normalized conversational forms such as:

        MED 1E3D139C96
        med 1e3d139c96

    This matters because router normalization may replace punctuation
    before appointment-selection logic runs.
    """

    match = re.search(
        r"\bMED(?:[-\s]+)([A-Z0-9]+)\b",
        message.upper(),
    )

    if not match:
        return None

    return (
        "MED-"
        + match.group(1)
    )


async def get_doctor_by_id(
    doctor_id: str,
) -> Doctor | None:

    async with AsyncSessionFactory() as session:
        return await session.get(
            Doctor,
            UUID(doctor_id),
        )


async def find_doctor_from_message(
    message: str,
):
    """
    Resolve an explicitly mentioned MediBook doctor
    deterministically from PostgreSQL.

    Doctor identity is NOT selected by the LLM.

    Resolution order:
    1. Exact full-name occurrence in the patient message.
    2. Exact full-name occurrence without the "Dr" prefix.
    3. Unique high-confidence partial-name match.
    4. Otherwise return None instead of guessing.
    """

    def normalize(
        value: str,
    ) -> str:
        cleaned = "".join(
            char.lower()
            if char.isalnum()
            else " "
            for char in value
        )

        return " ".join(
            cleaned.split()
        )


    def without_dr(
        value: str,
    ) -> str:
        normalized = normalize(
            value
        )

        if normalized.startswith(
            "dr "
        ):
            return normalized[3:].strip()

        return normalized


    normalized_message = normalize(
        message
    )


    async with AsyncSessionFactory() as session:

        result = await session.execute(
            select(Doctor)
        )

        doctors = list(
            result.scalars().all()
        )


    if not doctors:
        return None


    # --------------------------------------------------
    # 1. Exact full-name containment.
    #
    # Longest name first prevents a shorter overlapping
    # name from winning.
    # --------------------------------------------------

    exact_matches = []


    for doctor in doctors:

        full_name = str(
            doctor.full_name
        )

        normalized_name = normalize(
            full_name
        )

        normalized_without_dr = without_dr(
            full_name
        )


        if (
            normalized_name
            and normalized_name
            in normalized_message
        ):
            exact_matches.append(
                (
                    len(
                        normalized_name
                    ),
                    doctor,
                )
            )

            continue


        if (
            normalized_without_dr
            and normalized_without_dr
            in normalized_message
        ):
            exact_matches.append(
                (
                    len(
                        normalized_without_dr
                    ),
                    doctor,
                )
            )


    if exact_matches:

        exact_matches.sort(
            key=lambda item:
                item[0],
            reverse=True,
        )

        return exact_matches[0][1]


    # --------------------------------------------------
    # 2. Conservative unique partial matching.
    #
    # Never select a doctor from one common surname
    # such as "Ahmed".
    # --------------------------------------------------

    stop_tokens = {
        "dr",
        "doctor",
        "appointment",
        "appointments",
        "book",
        "booking",
        "available",
        "availability",
        "check",
        "give",
        "need",
        "want",
        "with",
        "tomorrow",
        "today",
        "please",
        "on",
        "at",
        "for",
        "the",
        "a",
        "an",
    }


    message_tokens = {
        token
        for token in normalized_message.split()
        if (
            token not in stop_tokens
            and len(token) >= 3
        )
    }


    candidates = []


    for doctor in doctors:

        doctor_tokens = [
            token
            for token in without_dr(
                str(
                    doctor.full_name
                )
            ).split()
            if (
                token not in stop_tokens
                and len(token) >= 3
            )
        ]


        overlap = [
            token
            for token in doctor_tokens
            if token
            in message_tokens
        ]


        # Require at least two identifying components.
        # One common surname is not enough.
        if len(overlap) >= 2:

            candidates.append(
                (
                    len(overlap),
                    len(
                        " ".join(
                            doctor_tokens
                        )
                    ),
                    doctor,
                )
            )


    if not candidates:
        return None


    candidates.sort(
        key=lambda item:
            (
                item[0],
                item[1],
            ),
        reverse=True,
    )


    best_score = candidates[0][0]


    best = [
        item
        for item in candidates
        if item[0]
        == best_score
    ]


    # Fail closed on ambiguity.
    if len(best) != 1:
        return None


    return best[0][2]




async def grounded_doctor_directory_search(
    message: str,
) -> str | None:
    """
    Handle high-confidence doctor discovery using the real
    MediBook directory.

    The LLM never creates doctor records here.
    """

    routed = fast_route(
        message
    )

    if not routed.matched:
        return None

    if routed.route == "capabilities":
        return routed.response

    if routed.route == "greeting":
        return routed.response

    if routed.route != "search_doctor":
        return None

    entities = (
        routed.entities
        or {}
    )

    specialty = entities.get(
        "specialty"
    )

    location = entities.get(
        "location"
    )

    gender = entities.get(
        "gender"
    )

    async with AsyncSessionFactory() as session:

        service = DoctorService(
            session
        )

        doctors = await service.search_doctors(
            specialty=specialty,
            location=location,
            gender=gender,
        )

    if not doctors:

        filters = []

        if specialty:
            filters.append(
                specialty.title()
            )

        if location:
            filters.append(
                location
            )

        if gender:
            filters.append(
                gender.title()
            )

        description = (
            ", ".join(filters)
            if filters
            else "those criteria"
        )

        return (
            "I couldn't find an active MediBook doctor "
            f"matching {description}. "
            "Try changing the specialty, location, or gender filter."
        )

    heading_parts = []

    if gender:
        heading_parts.append(
            gender
        )

    if specialty:
        heading_parts.append(
            specialty
        )

    heading = " ".join(
        heading_parts
    ).strip()

    if location:
        heading = (
            f"{heading} in {location}"
            if heading
            else f"doctors in {location}"
        )

    if not heading:
        heading = "matching doctors"

    lines = [
        (
            f"I found {len(doctors)} "
            f"MediBook {'doctor' if len(doctors) == 1 else 'doctors'} "
            f"matching {heading}:"
        ),
        "",
    ]

    for index, doctor in enumerate(
        doctors,
        start=1,
    ):
        specialty_name = (
            doctor.specialty.name
            if doctor.specialty
            else "Specialty not listed"
        )

        lines.append(
            f"{index}. {doctor.full_name} — "
            f"{specialty_name}, "
            f"{doctor.clinic_location}, "
            f"Tk {doctor.consultation_fee}"
        )

    if len(doctors) == 1:

        doctor = doctors[0]

        lines.extend(
            [
                "",
                (
                    f"I can check {doctor.full_name}'s "
                    "real appointment availability next."
                ),
            ]
        )

    else:

        lines.extend(
            [
                "",
                (
                    "Tell me which doctor you'd like, "
                    "and I can check their real MediBook availability."
                ),
            ]
        )

    return "\n".join(
        lines
    )


async def get_available_slots(
    doctor_id: str,
    slot_date: date,
) -> dict[str, Any]:

    async with AsyncSessionFactory() as session:

        service = AvailabilityService(
            session
        )

        return await service.get_doctor_availability(
            doctor_id=UUID(
                doctor_id
            ),
            slot_date=slot_date,
        )


async def resolve_slot(
    doctor_id: str,
    slot_date: date,
    requested_time: time,
) -> DoctorSlot | None:

    async with AsyncSessionFactory() as session:

        return await session.scalar(
            select(DoctorSlot)
            .where(
                DoctorSlot.doctor_id
                == UUID(doctor_id),
                DoctorSlot.slot_date
                == slot_date,
                DoctorSlot.start_time
                == requested_time,
                DoctorSlot.is_available
                .is_(True),
            )
        )


async def list_appointments_for_phone(
    phone: str,
    hospital_id: UUID,
) -> list[dict]:

    async with AsyncSessionFactory() as session:

        service = AppointmentService(
            session
        )

        return await service.list_for_phone(
            phone=phone,
            hospital_id=hospital_id,
        )


def appointment_summary(
    appointment: dict,
    *,
    numbered: int | None = None,
) -> str:

    prefix = (
        f"{numbered}. "
        if numbered is not None
        else ""
    )

    doctor = appointment[
        "doctor"
    ]

    return (
        f"{prefix}{doctor['name']} — "
        f"{format_date(appointment['date'])}, "
        f"{format_time(appointment['time'])}\n"
        f"   {doctor['clinic_name']}\n"
        f"   Confirmation: "
        f"{appointment['confirmation_code']}"
    )


async def remember_appointments(
    conversation_id: str,
    state: dict[str, Any],
    appointments: list[dict],
) -> None:

    state[
        "last_appointments"
    ] = appointments

    if len(appointments) == 1:
        state[
            "selected_appointment"
        ] = appointments[0]
    else:
        state[
            "selected_appointment"
        ] = None

    await save_session(
        conversation_id,
        state,
    )


async def handle_lookup(
    conversation_id: str,
    state: dict[str, Any],
    phone: str,
    hospital_id: UUID,
) -> str:

    appointments = (
        await list_appointments_for_phone(
            phone,
            hospital_id=hospital_id,
        )
    )

    state["patient_phone"] = phone

    state["awaiting"] = None

    await remember_appointments(
        conversation_id,
        state,
        appointments,
    )

    if not appointments:

        return (
            "I couldn't find any active MediBook appointments "
            f"for {phone}. "
            "I can help you find a doctor and make a new booking."
        )

    lines = [
        appointment_summary(
            appointment,
            numbered=index,
        )
        for index, appointment
        in enumerate(
            appointments,
            start=1,
        )
    ]

    if len(appointments) == 1:

        return (
            "You have one active appointment:\n\n"
            + "\n\n".join(lines)
            + "\n\nI can reschedule or cancel this appointment."
        )

    return (
        f"You have {len(appointments)} active appointments:\n\n"
        + "\n\n".join(lines)
        + "\n\nTell me which appointment you want to manage "
        "using its number or confirmation code."
    )


def choose_appointment(
    message: str,
    appointments: list[dict],
) -> dict | None:

    if not appointments:
        return None

    confirmation = extract_confirmation_code(
        message
    )

    if confirmation:

        for appointment in appointments:

            if (
                appointment[
                    "confirmation_code"
                ].upper()
                == confirmation.upper()
            ):
                return appointment

    number_match = re.search(
        r"\b(?:appointment\s*)?([1-9])\b",
        normalize(message),
    )

    if number_match:

        index = (
            int(number_match.group(1))
            - 1
        )

        if (
            0 <= index
            < len(appointments)
        ):
            return appointments[index]

    if len(appointments) == 1:
        return appointments[0]

    return None


async def prepare_cancel(
    conversation_id: str,
    state: dict[str, Any],
    appointment: dict,
) -> str:

    phone = state.get(
        "patient_phone"
    )

    if not phone:

        state["awaiting"] = (
            "cancel_phone"
        )

        state[
            "selected_appointment"
        ] = appointment

        await save_session(
            conversation_id,
            state,
        )

        return (
            "Before I cancel it, please send the patient's "
            "mobile number used for this appointment."
        )

    state["pending_action"] = {
        "type": "cancel",
        "confirmation_code": (
            appointment[
                "confirmation_code"
            ]
        ),
        "patient_phone": phone,
        "appointment": appointment,
    }

    await save_session(
        conversation_id,
        state,
    )

    return (
        "You're about to cancel this appointment:\n\n"
        f"{appointment_summary(appointment)}\n\n"
        "Reply \"Confirm\" to cancel it, "
        "or \"Keep Appointment\" to leave it unchanged."
    )


async def execute_cancel(
    conversation_id: str,
    state: dict[str, Any],
    pending: dict,
    hospital_id: UUID,
) -> str:

    patient_phone = (
        pending.get(
            "patient_phone"
        )
        or state.get(
            "patient_phone"
        )
        or (
            state.get(
                "patient"
            )
            or {}
        ).get(
            "phone"
        )
    )

    if not patient_phone:

        state["pending_action"] = None

        await save_session(
            conversation_id,
            state,
        )

        return (
            "I couldn't verify the patient identity for this "
            "appointment, so nothing was cancelled."
        )

    try:

        async with AsyncSessionFactory() as session:

            service = AppointmentService(
                session
            )

            result = (
                await service.cancel_appointment(
                    confirmation_code=(
                        pending[
                            "confirmation_code"
                        ]
                    ),
                    patient_phone=patient_phone,
                    hospital_id=hospital_id,
                )
            )

    except AppointmentNotFoundError:

        state["pending_action"] = None

        await save_session(
            conversation_id,
            state,
        )

        return (
            "I couldn't verify that appointment with the "
            "provided mobile number, so nothing was cancelled."
        )

    except AppointmentStateError as exc:

        state["pending_action"] = None

        await save_session(
            conversation_id,
            state,
        )

        return (
            f"I couldn't cancel that appointment: {exc}"
        )

    state["pending_action"] = None
    state["selected_appointment"] = None

    phone = state.get(
        "patient_phone"
    )

    if phone:

        remaining = (
            await list_appointments_for_phone(
                phone,
                hospital_id=hospital_id,
            )
        )

        state[
            "last_appointments"
        ] = remaining

    await save_session(
        conversation_id,
        state,
    )

    return (
        "The appointment has been cancelled successfully.\n\n"
        f"Confirmation: {result['confirmation_code']}\n"
        f"Doctor: {result['doctor_name']}\n\n"
        "The appointment slot has been released back "
        "into MediBook availability."
    )


async def prepare_reschedule(
    conversation_id: str,
    state: dict[str, Any],
    appointment: dict,
    message: str,
) -> str:

    new_date = resolve_date(
        message
    )

    new_time = resolve_time(
        message
    )

    if new_date is None:

        state["selected_appointment"] = (
            appointment
        )

        state["awaiting"] = (
            "reschedule_date"
        )

        await save_session(
            conversation_id,
            state,
        )

        return (
            f"When would you like to move the appointment with "
            f"{appointment['doctor']['name']}? "
            "You can say, for example, "
            "\"tomorrow at 7 PM\"."
        )

    doctor_id = appointment[
        "doctor"
    ][
        "id"
    ]

    availability = (
        await get_available_slots(
            doctor_id,
            new_date,
        )
    )

    available = availability.get(
        "available_slots",
        [],
    )

    if not available:

        state["selected_appointment"] = (
            appointment
        )

        state["awaiting"] = (
            "reschedule_date"
        )

        await save_session(
            conversation_id,
            state,
        )

        return (
            f"{appointment['doctor']['name']} has no available "
            f"MediBook slots on {format_date(new_date.isoformat())}. "
            "Choose another date and I'll check it."
        )

    if new_time is None:

        state[
            "selected_appointment"
        ] = appointment

        state[
            "reschedule_date"
        ] = new_date.isoformat()

        state["awaiting"] = (
            "reschedule_time"
        )

        await save_session(
            conversation_id,
            state,
        )

        formatted = ", ".join(
            format_time(value)
            for value in available
        )

        return (
            f"{appointment['doctor']['name']} is available on "
            f"{format_date(new_date.isoformat())} at:\n\n"
            f"{formatted}\n\n"
            "Which time would you like?"
        )

    slot = await resolve_slot(
        doctor_id,
        new_date,
        new_time,
    )

    if slot is None:

        formatted = ", ".join(
            format_time(value)
            for value in available
        )

        state[
            "selected_appointment"
        ] = appointment

        state[
            "reschedule_date"
        ] = new_date.isoformat()

        state["awaiting"] = (
            "reschedule_time"
        )

        await save_session(
            conversation_id,
            state,
        )

        return (
            f"{format_time(new_time)} is not available on "
            f"{format_date(new_date.isoformat())}.\n\n"
            f"Available times are: {formatted}.\n\n"
            "Choose one of those times."
        )

    phone = state.get(
        "patient_phone"
    )

    if not phone:

        state[
            "selected_appointment"
        ] = appointment

        state[
            "pending_reschedule_slot"
        ] = str(slot.id)

        state["awaiting"] = (
            "reschedule_phone"
        )

        await save_session(
            conversation_id,
            state,
        )

        return (
            "That new time is available. "
            "Please send the patient's mobile number "
            "to verify the appointment before rescheduling."
        )

    state["pending_action"] = {
        "type": "reschedule",
        "confirmation_code": (
            appointment[
                "confirmation_code"
            ]
        ),
        "patient_phone": phone,
        "new_slot_id": str(
            slot.id
        ),
        "appointment": appointment,
        "new_date": (
            new_date.isoformat()
        ),
        "new_time": (
            new_time.strftime(
                "%H:%M"
            )
        ),
    }

    state["awaiting"] = None

    await save_session(
        conversation_id,
        state,
    )

    return (
        "Please confirm this reschedule:\n\n"
        f"Doctor: {appointment['doctor']['name']}\n"
        f"Current: {format_date(appointment['date'])}, "
        f"{format_time(appointment['time'])}\n"
        f"New: {format_date(new_date.isoformat())}, "
        f"{format_time(new_time)}\n\n"
        "Reply \"Confirm\" to reschedule, "
        "or \"Keep Appointment\" to leave it unchanged."
    )


async def execute_reschedule(
    conversation_id: str,
    state: dict[str, Any],
    pending: dict,
    hospital_id: UUID,
) -> str:

    try:

        async with AsyncSessionFactory() as session:

            service = AppointmentService(
                session
            )

            result = (
                await service.reschedule_appointment(
                    confirmation_code=(
                        pending[
                            "confirmation_code"
                        ]
                    ),
                    patient_phone=(
                        pending[
                            "patient_phone"
                        ]
                    ),
                    new_slot_id=UUID(
                        pending[
                            "new_slot_id"
                        ]
                    ),
                    hospital_id=hospital_id,
                )
            )

    except SlotUnavailableError:

        state["pending_action"] = None

        await save_session(
            conversation_id,
            state,
        )

        return (
            "That new appointment time was just taken. "
            "Your original appointment has not been changed. "
            "I can show the remaining available times."
        )

    except (
        AppointmentNotFoundError,
        AppointmentStateError,
        BookingError,
    ) as exc:

        state["pending_action"] = None

        await save_session(
            conversation_id,
            state,
        )

        return (
            f"I couldn't safely reschedule that appointment: {exc}. "
            "Your existing appointment was left unchanged."
        )

    state["pending_action"] = None
    state["awaiting"] = None

    phone = state.get(
        "patient_phone"
    )

    if phone:

        appointments = (
            await list_appointments_for_phone(
                phone,
                hospital_id=hospital_id,
            )
        )

        await remember_appointments(
            conversation_id,
            state,
            appointments,
        )

    else:

        await save_session(
            conversation_id,
            state,
        )

    return (
        "Your appointment has been rescheduled successfully.\n\n"
        f"Confirmation: {result['confirmation_code']}\n"
        f"Doctor: {result['doctor_name']}\n"
        f"Clinic: {result['clinic_name']}\n"
        f"New date: {format_date(result['date'])}\n"
        f"New time: {format_time(result['time'])}\n"
        f"Fee: Tk {result['consultation_fee']:.0f}\n\n"
        "Your confirmation code remains the same."
    )


async def handle_conversation(
    conversation_id: str,
    message: str,
    hospital_id: UUID,
) -> str:

    # MEDIBOOK_CONTEXT_RUNTIME_V2
    message = _mb_normalize_context_v2(
        message,
        conversation_id,
    )
    _mb_capture_context_v2(
        message,
        conversation_id,
    )

    state = await load_session(
        conversation_id
    )

    text = normalize(
        message
    )

    pending_action = state.get(
        "pending_action"
    )

    # ====================================================
    # 1. Explicit confirmation of destructive/change action
    # ====================================================

    if (
        pending_action
        and text in CONFIRM_PHRASES
    ):

        if (
            pending_action["type"]
            == "cancel"
        ):
            return await execute_cancel(
                conversation_id,
                state,
                pending_action,
                hospital_id=hospital_id,
            )

        if (
            pending_action["type"]
            == "reschedule"
        ):
            return await execute_reschedule(
                conversation_id,
                state,
                pending_action,
                hospital_id=hospital_id,
            )

    # ====================================================
    # 2. Abort pending change
    # ====================================================

    if (
        pending_action
        and text in ABORT_PHRASES
    ):

        state["pending_action"] = None

        await save_session(
            conversation_id,
            state,
        )

        return (
            "No changes were made. "
            "Your existing appointment remains unchanged."
        )

    # ====================================================
    # 3. Awaiting phone for appointment lookup
    # ====================================================

    awaiting = state.get(
        "awaiting"
    )

    if awaiting == "lookup_phone":

        phone = parse_phone(
            message
        )

        if not phone:

            return (
                "Please send the Bangladeshi mobile number "
                "used for the appointment, for example "
                "01712345678."
            )

        return await handle_lookup(
            conversation_id,
            state,
            phone,
            hospital_id=hospital_id,
        )

    # ====================================================
    # 4. Awaiting cancellation verification phone
    # ====================================================

    if awaiting == "cancel_phone":

        phone = parse_phone(
            message
        )

        if not phone:

            return (
                "Please send the mobile number used "
                "for this appointment."
            )

        state["patient_phone"] = phone
        state["awaiting"] = None

        appointment = state.get(
            "selected_appointment"
        )

        await save_session(
            conversation_id,
            state,
        )

        if appointment:

            return await prepare_cancel(
                conversation_id,
                state,
                appointment,
            )

    # ====================================================
    # 5. Awaiting reschedule phone
    # ====================================================

    if awaiting == "reschedule_phone":

        phone = parse_phone(
            message
        )

        if not phone:

            return (
                "Please send the mobile number used "
                "for this appointment."
            )

        state["patient_phone"] = phone

        appointment = state.get(
            "selected_appointment"
        )

        slot_id = state.get(
            "pending_reschedule_slot"
        )

        if (
            appointment
            and slot_id
        ):

            async with AsyncSessionFactory() as session:

                slot = await session.get(
                    DoctorSlot,
                    UUID(slot_id),
                )

            if (
                slot is None
                or not slot.is_available
            ):

                state["awaiting"] = None

                await save_session(
                    conversation_id,
                    state,
                )

                return (
                    "That new appointment time is no longer available. "
                    "Your existing appointment remains unchanged."
                )

            state["pending_action"] = {
                "type": "reschedule",
                "confirmation_code": (
                    appointment[
                        "confirmation_code"
                    ]
                ),
                "patient_phone": phone,
                "new_slot_id": str(
                    slot.id
                ),
                "appointment": appointment,
                "new_date": (
                    slot.slot_date.isoformat()
                ),
                "new_time": (
                    slot.start_time.strftime(
                        "%H:%M"
                    )
                ),
            }

            state["awaiting"] = None

            await save_session(
                conversation_id,
                state,
            )

            return (
                "Please confirm this reschedule:\n\n"
                f"Doctor: {appointment['doctor']['name']}\n"
                f"Current: {format_date(appointment['date'])}, "
                f"{format_time(appointment['time'])}\n"
                f"New: {format_date(slot.slot_date.isoformat())}, "
                f"{format_time(slot.start_time)}\n\n"
                "Reply \"Confirm\" to reschedule, "
                "or \"Keep Appointment\" to leave it unchanged."
            )

    # ====================================================
    # 6. Awaiting reschedule date
    # ====================================================

    if awaiting == "reschedule_date":

        appointment = state.get(
            "selected_appointment"
        )

        if appointment:

            return await prepare_reschedule(
                conversation_id,
                state,
                appointment,
                message,
            )

    # ====================================================
    # 7. Awaiting reschedule time
    # ====================================================

    if awaiting == "reschedule_time":

        appointment = state.get(
            "selected_appointment"
        )

        remembered_date = state.get(
            "reschedule_date"
        )

        requested_time = resolve_booking_time(message)

        if not requested_time:

            return (
                "Please choose one of the available times, "
                "for example \"7 PM\"."
            )

        if (
            appointment
            and remembered_date
        ):

            synthetic = (
                f"{remembered_date} "
                f"{requested_time.strftime('%H:%M')}"
            )

            return await prepare_reschedule(
                conversation_id,
                state,
                appointment,
                synthetic,
            )

    # ====================================================
    # 8. Patient details for booking from M4
    # ====================================================

    pending_booking = state.get(
        "pending_booking"
    )

    if pending_booking:

        patient = parse_patient_details(
            message
        )

        if patient:

            name, phone = patient

            state["patient"] = {
                "name": name,
                "phone": phone,
            }

            state["patient_phone"] = phone

            await save_session(
                conversation_id,
                state,
            )

            return (
                "Please confirm this appointment:\n\n"
                f"Doctor: {pending_booking['doctor_name']}\n"
                f"Specialty: {pending_booking['specialty']}\n"
                f"Clinic: {pending_booking['clinic_name']}\n"
                f"Date: {format_date(pending_booking['date'])}\n"
                f"Time: {format_time(pending_booking['time'])}\n"
                f"Fee: Tk {pending_booking['consultation_fee']:.0f}\n"
                f"Patient: {name}\n"
                f"Phone: {phone}\n\n"
                "Reply \"Confirm\" to complete the booking."
            )

    # ====================================================
    # 9. List appointments intent
    # ====================================================

    if contains_any(
        message,
        LIST_APPOINTMENT_HINTS,
    ):

        phone = (
            parse_phone(message)
            or state.get(
                "patient_phone"
            )
        )

        if not phone:

            state["awaiting"] = (
                "lookup_phone"
            )

            await save_session(
                conversation_id,
                state,
            )

            return (
                "Sure. Send the mobile number used for "
                "your MediBook appointments and I'll look them up."
            )

        return await handle_lookup(
            conversation_id,
            state,
            phone,
            hospital_id=hospital_id,
        )

    # ====================================================
    # 10. Cancel appointment intent
    # ====================================================

    if contains_any(
        message,
        CANCEL_APPOINTMENT_HINTS,
    ):

        appointments = state.get(
            "last_appointments",
            [],
        )

        phone = (
            parse_phone(message)
            or state.get(
                "patient_phone"
            )
        )

        confirmation = (
            extract_confirmation_code(
                message
            )
        )

        if confirmation and phone:

            appointments = (
                await list_appointments_for_phone(
                    phone,
                    hospital_id=hospital_id,
                )
            )

            await remember_appointments(
                conversation_id,
                state,
                appointments,
            )

        appointment = choose_appointment(
            message,
            appointments,
        )

        if appointment is None:

            if not phone:

                state["awaiting"] = (
                    "lookup_phone"
                )

                await save_session(
                    conversation_id,
                    state,
                )

                return (
                    "I can cancel the appointment directly. "
                    "First send the mobile number used for the booking."
                )

            if not appointments:

                return await handle_lookup(
                    conversation_id,
                    state,
                    phone,
                    hospital_id=hospital_id,
                )

            return (
                "You have more than one active appointment. "
                "Tell me which one to cancel using its number "
                "or confirmation code."
            )

        return await prepare_cancel(
            conversation_id,
            state,
            appointment,
        )

    # ====================================================
    # 11. Reschedule intent
    # ====================================================

    if contains_any(
        message,
        RESCHEDULE_HINTS,
    ):

        appointments = state.get(
            "last_appointments",
            [],
        )

        phone = (
            parse_phone(message)
            or state.get(
                "patient_phone"
            )
        )

        if not appointments:

            if not phone:

                state["awaiting"] = (
                    "lookup_phone"
                )

                await save_session(
                    conversation_id,
                    state,
                )

                return (
                    "I can reschedule it directly. "
                    "First send the mobile number used for the appointment."
                )

            appointments = (
                await list_appointments_for_phone(
                    phone,
                    hospital_id=hospital_id,
                )
            )

            state["patient_phone"] = phone

            await remember_appointments(
                conversation_id,
                state,
                appointments,
            )

        appointment = choose_appointment(
            message,
            appointments,
        )

        if appointment is None:

            return (
                "You have more than one active appointment. "
                "Tell me which one to reschedule using its "
                "number or confirmation code."
            )

        state[
            "selected_appointment"
        ] = appointment

        await save_session(
            conversation_id,
            state,
        )

        return await prepare_reschedule(
            conversation_id,
            state,
            appointment,
            message,
        )

    # ====================================================
    # 12. Existing booking confirmation from M4
    # ====================================================

    if (
        pending_booking
        and text in CONFIRM_PHRASES
    ):

        patient = state.get(
            "patient"
        )

        if not patient:

            return (
                "Please send the patient's full name and mobile number "
                "before confirming the appointment."
            )

        try:

            async with AsyncSessionFactory() as session:

                service = AppointmentService(
                    session
                )

                result = (
                    await service.confirm_booking(
                        slot_id=UUID(
                            pending_booking[
                                "slot_id"
                            ]
                        ),
                        patient_name=(
                            patient["name"]
                        ),
                        patient_phone=(
                            patient["phone"]
                        ),
                        hospital_id=hospital_id,
                    )
                )

        except SlotUnavailableError:

            state["pending_booking"] = None

            await save_session(
                conversation_id,
                state,
            )

            return (
                "That appointment time is no longer available. "
                "No booking was created. "
                "I can show the remaining real slots."
            )

        state["pending_booking"] = None
        state["last_slots"] = []

        state["patient_phone"] = (
            patient["phone"]
        )

        state["last_appointment"] = (
            result
        )

        await save_session(
            conversation_id,
            state,
        )

        return (
            "Your appointment is confirmed.\n\n"
            f"Confirmation: {result['confirmation_code']}\n"
            f"Doctor: {result['doctor_name']}\n"
            f"Clinic: {result['clinic_name']}\n"
            f"Date: {format_date(result['date'])}\n"
            f"Time: {format_time(result['time'])}\n"
            f"Fee: Tk {result['consultation_fee']:.0f}\n\n"
            "I can now help you view, reschedule, "
            "or cancel this appointment."
        )

    # ====================================================
    # 13. Doctor/date/booking logic from M4
    # ====================================================

    mentioned_doctor = (
        await find_doctor_from_message(
            message
        )
    )

    if mentioned_doctor:

        state["last_doctor"] = {
            "id": str(
                mentioned_doctor.id
            ),
            "name": (
                mentioned_doctor.full_name
            ),
        }

    remembered_doctor = state.get(
        "last_doctor"
    )

    doctor = mentioned_doctor

    if (
        doctor is None
        and remembered_doctor
    ):

        doctor = await get_doctor_by_id(
            remembered_doctor[
                "id"
            ]
        )

    resolved_date = resolve_date(
        message,
        state.get(
            "last_date"
        ),
    )

    is_booking = contains_any(
        message,
        BOOKING_HINTS,
    )

    is_availability = contains_any(
        message,
        AVAILABILITY_HINTS,
    )

    if (
        doctor
        and resolved_date
        and is_availability
        and not is_booking
    ):

        result = await get_available_slots(
            str(doctor.id),
            resolved_date,
        )

        slots = result.get(
            "available_slots",
            [],
        )

        state["last_date"] = (
            resolved_date.isoformat()
        )

        state["last_slots"] = slots

        await save_session(
            conversation_id,
            state,
        )

        if not slots:

            return (
                f"{doctor.full_name} has no available MediBook "
                f"slots on {format_date(resolved_date.isoformat())}. "
                "I can check another date."
            )

        formatted = ", ".join(
            format_time(slot)
            for slot in slots
        )

        return (
            f"{doctor.full_name} is available on "
            f"{format_date(resolved_date.isoformat())} at:\n\n"
            f"{formatted}\n\n"
            "Tell me which time you want, for example "
            "\"Book the 6 PM one.\""
        )

    if is_booking and doctor:

        if resolved_date is None:

            return (
                f"Which date would you like to book "
                f"{doctor.full_name}?"
            )

        requested_time = resolve_booking_time(message)

        if requested_time is None:

            availability = await get_available_slots(
                str(doctor.id),
                resolved_date,
            )

            slots = availability.get(
                "available_slots",
                [],
            )

            if not slots:

                return (
                    f"{doctor.full_name} has no available slots "
                    f"on {format_date(resolved_date.isoformat())}."
                )

            state["last_date"] = (
                resolved_date.isoformat()
            )

            state["last_slots"] = slots

            await save_session(
                conversation_id,
                state,
            )

            formatted = ", ".join(
                format_time(slot)
                for slot in slots
            )

            return (
                f"Available times are: {formatted}. "
                "Which one would you like?"
            )

        slot = await resolve_slot(
            str(doctor.id),
            resolved_date,
            requested_time,
        )

        if slot is None:

            availability = await get_available_slots(
                str(doctor.id),
                resolved_date,
            )

            alternatives = availability.get(
                "available_slots",
                [],
            )

            if alternatives:

                formatted = ", ".join(
                    format_time(value)
                    for value in alternatives
                )

                return (
                    f"{format_time(requested_time)} is unavailable. "
                    f"Available times are: {formatted}."
                )

            return (
                f"{doctor.full_name} has no available slots "
                f"on {format_date(resolved_date.isoformat())}."
            )

        async with AsyncSessionFactory() as session:

            service = AppointmentService(
                session
            )

            preview = await service.preview_booking(
                slot_id=slot.id,
                hospital_id=hospital_id,
            )

        state["pending_booking"] = (
            preview
        )

        state["last_date"] = (
            resolved_date.isoformat()
        )

        await save_session(
            conversation_id,
            state,
        )

        patient = state.get(
            "patient"
        )

        if patient:

            return (
                "Please confirm this appointment:\n\n"
                f"Doctor: {preview['doctor_name']}\n"
                f"Clinic: {preview['clinic_name']}\n"
                f"Date: {format_date(preview['date'])}\n"
                f"Time: {format_time(preview['time'])}\n"
                f"Fee: Tk {preview['consultation_fee']:.0f}\n"
                f"Patient: {patient['name']}\n\n"
                "Reply \"Confirm\" to book it."
            )

        return (
            f"I've selected {preview['doctor_name']} on "
            f"{format_date(preview['date'])} at "
            f"{format_time(preview['time'])}.\n\n"
            f"Clinic: {preview['clinic_name']}\n"
            f"Fee: Tk {preview['consultation_fee']:.0f}\n\n"
            "Please send the patient's full name and mobile number."
        )

    # ====================================================
    # 14. Generic fallback
    # ====================================================

    # --------------------------------------------------
    # Deterministic medical safety boundary.
    #
    # Clinical requests do not need the generative model.
    # --------------------------------------------------

    safety = safety_route(
        message
    )

    if safety.matched:
        return safety.response or (
            "MediBook does not provide diagnosis, treatment, "
            "medication, dosage advice, or clinical interpretation. "
            "I can help you find and book an appropriate doctor."
        )

    # --------------------------------------------------
    # Grounded doctor-directory / product fast path.
    #
    # This MUST execute before generative fallback so the
    # LLM can never invent doctor directory results.
    # --------------------------------------------------

    grounded_response = (
        await grounded_doctor_directory_search(
            message
        )
    )

    if grounded_response is not None:
        return grounded_response

    # Only genuinely conversational language reaches
    # the generative model.
    return await generate_safe_response(
        message
    )
