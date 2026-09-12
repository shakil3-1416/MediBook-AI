from __future__ import annotations

import re
import uuid
from datetime import date, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.hospital_directory_service import (
    HospitalDirectoryService,
)


DHAKA = ZoneInfo(
    "Asia/Dhaka"
)


ORDINALS = {
    "first": 1,
    "1st": 1,
    "second": 2,
    "2nd": 2,
    "third": 3,
    "3rd": 3,
    "fourth": 4,
    "4th": 4,
    "fifth": 5,
    "5th": 5,
    "sixth": 6,
    "6th": 6,
}


PROFILE_PHRASES = (
    "tell me about",
    "more about",
    "details about",
    "information about",
    "doctor details",
    "doctor profile",
)


AVAILABILITY_WORDS = (
    "available",
    "availability",
    "schedule",
    "slots",
    "slot",
    "available times",
    "appointment times",
)


def normalize(
    value: str,
) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        value.lower(),
    ).strip()


def _contains_term(
    value: str,
    term: str,
) -> bool:

    return (
        re.search(
            rf"\b{re.escape(term)}\b",
            value,
        )
        is not None
    )


def _doctor_references(
    state: dict[str, Any],
) -> list[dict[str, Any]]:

    for key in (
        "last_doctors",
        "grounded_doctor_results",
        "doctor_results",
    ):
        value = state.get(
            key
        )

        if isinstance(
            value,
            list,
        ):
            rows = [
                item
                for item in value
                if isinstance(
                    item,
                    dict,
                )
            ]

            if rows:
                return rows

    return []


def resolve_doctor_reference(
    message: str,
    state: dict[str, Any],
) -> dict[str, Any] | None:

    value = normalize(
        message
    )

    doctors = _doctor_references(
        state
    )

    # Exact doctor-name reference.
    for doctor in doctors:

        name = (
            doctor.get(
                "doctor_name"
            )
            or
            doctor.get(
                "full_name"
            )
            or
            ""
        )

        normalized_name = normalize(
            str(name)
        )

        if (
            normalized_name
            and
            normalized_name in value
        ):
            return doctor

    # Ordinal references:
    # "the second one", "2nd doctor", etc.
    for token, position in ORDINALS.items():

        if re.search(
            rf"\b{re.escape(token)}\b",
            value,
        ):
            index = (
                position - 1
            )

            if (
                0
                <= index
                < len(doctors)
            ):
                return doctors[
                    index
                ]

    selected = state.get(
        "grounded_selected_doctor"
    )

    if isinstance(
        selected,
        dict,
    ):
        contextual_phrases = (
            "this doctor",
            "that doctor",
            "the doctor",
            "her",
            "him",
            "their",
            "she",
            "he",
        )

        if any(
            phrase in value
            for phrase
            in contextual_phrases
        ):
            return selected

        if any(
            _contains_term(
                value,
                word,
            )
            for word
            in AVAILABILITY_WORDS
        ):
            return selected

    # If exactly one doctor is in context,
    # generic doctor follow-up is unambiguous.
    if (
        len(doctors) == 1
        and
        (
            any(
                phrase in value
                for phrase
                in PROFILE_PHRASES
            )
            or
            any(
                word in value
                for word
                in AVAILABILITY_WORDS
            )
        )
    ):
        return doctors[0]

    return None


def is_profile_followup(
    message: str,
) -> bool:

    value = normalize(
        message
    )

    return any(
        phrase in value
        for phrase
        in PROFILE_PHRASES
    )


def is_availability_followup(
    message: str,
) -> bool:

    value = normalize(
        message
    )

    mutation_terms = (
        "reschedule",
        "cancel",
        "confirm",
        "book",
    )

    if any(
        _contains_term(
            value,
            term,
        )
        for term
        in mutation_terms
    ):
        return False

    return any(
        _contains_term(
            value,
            word,
        )
        for word
        in AVAILABILITY_WORDS
    )


def _today_dhaka() -> date:

    from datetime import datetime

    return datetime.now(
        DHAKA
    ).date()


def availability_window(
    message: str,
) -> tuple[
    date,
    date,
    str,
]:

    value = normalize(
        message
    )

    today = _today_dhaka()

    iso_match = re.search(
        r"\b(20\d{2}-\d{2}-\d{2})\b",
        message,
    )

    if iso_match:
        try:
            target = date.fromisoformat(
                iso_match.group(1)
            )
        except ValueError:
            target = None

        if target is not None:
            return (
                target,
                target,
                target.isoformat(),
            )

    if "tomorrow" in value:

        target = (
            today
            + timedelta(
                days=1
            )
        )

        return (
            target,
            target,
            "tomorrow",
        )

    if "today" in value:

        return (
            today,
            today,
            "today",
        )

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    for name, weekday in weekdays.items():

        if name not in value:
            continue

        days = (
            weekday
            - today.weekday()
        ) % 7

        if days == 0:
            days = 7

        target = (
            today
            + timedelta(
                days=days
            )
        )

        return (
            target,
            target,
            name.capitalize(),
        )

    # No explicit date:
    # show useful upcoming availability.
    end = (
        today
        + timedelta(
            days=30
        )
    )

    return (
        today,
        end,
        "the next 30 days",
    )


def _doctor_payload(
    doctor: Any,
) -> dict[str, Any]:

    specialty = getattr(
        doctor,
        "specialty",
        None,
    )

    return {
        "component":
            "doctor_card",

        "doctor_name":
            doctor.full_name,

        "specialty":
            getattr(
                specialty,
                "name",
                None,
            ),

        "qualification":
            getattr(
                doctor,
                "qualification",
                None,
            ),

        "experience_years":
            getattr(
                doctor,
                "experience_years",
                None,
            ),

        "clinic_name":
            getattr(
                doctor,
                "clinic_name",
                None,
            ),

        "clinic_location":
            getattr(
                doctor,
                "clinic_location",
                None,
            ),

        "professional_interests":
            getattr(
                doctor,
                "professional_interests",
                None,
            ),

        "profile_image_url":
            getattr(
                doctor,
                "profile_image_url",
                None,
            ),
    }


def _doctor_reference(
    doctor: Any,
) -> dict[str, Any]:

    specialty = getattr(
        doctor,
        "specialty",
        None,
    )

    return {
        "id":
            str(
                doctor.id
            ),

        "doctor_id":
            str(
                doctor.id
            ),

        "doctor_name":
            doctor.full_name,

        "full_name":
            doctor.full_name,

        "specialty":
            getattr(
                specialty,
                "name",
                None,
            ),
    }


async def grounded_doctor_followup_result(
    session: AsyncSession,
    *,
    hospital_id: uuid.UUID,
    message: str,
    state: dict[str, Any],
) -> dict[str, Any] | None:

    profile_request = (
        is_profile_followup(
            message
        )
    )

    availability_request = (
        is_availability_followup(
            message
        )
    )

    if not (
        profile_request
        or
        availability_request
    ):
        return None

    reference = (
        resolve_doctor_reference(
            message,
            state,
        )
    )

    if reference is None:
        return None

    doctor_id_value = (
        reference.get(
            "doctor_id"
        )
        or
        reference.get(
            "id"
        )
    )

    if not doctor_id_value:
        return None

    try:
        doctor_id = uuid.UUID(
            str(
                doctor_id_value
            )
        )
    except ValueError:
        return None

    service = HospitalDirectoryService(
        session
    )

    try:
        doctor = await service.doctor(
            hospital_id=hospital_id,
            doctor_id=doctor_id,
        )
    except Exception:
        return None

    if doctor is None:
        return None

    selected = _doctor_reference(
        doctor
    )

    if profile_request:

        specialty_name = (
            selected.get(
                "specialty"
            )
            or
            "doctor"
        )

        qualification = getattr(
            doctor,
            "qualification",
            None,
        )

        experience = getattr(
            doctor,
            "experience_years",
            None,
        )

        clinic = getattr(
            doctor,
            "clinic_name",
            None,
        )

        location = getattr(
            doctor,
            "clinic_location",
            None,
        )

        parts = [
            (
                f"{doctor.full_name} "
                f"is a {specialty_name} specialist."
            )
        ]

        if qualification:
            parts.append(
                f"Qualifications: {qualification}."
            )

        if experience is not None:
            parts.append(
                f"Experience: {experience} years."
            )

        if clinic:
            if location:
                parts.append(
                    (
                        f"Chamber: {clinic}, "
                        f"{location}."
                    )
                )
            else:
                parts.append(
                    f"Chamber: {clinic}."
                )

        parts.append(
            (
                "You can ask me about this "
                "doctor's availability or schedule."
            )
        )

        return {
            "response":
                " ".join(
                    parts
                ),

            "actions": [
                {
                    "id":
                        f"doctor:{doctor.id}",

                    "type":
                        "send_message",

                    "label":
                        doctor.full_name,

                    "message":
                        (
                            "Tell me about "
                            f"{doctor.full_name}"
                        ),

                    "variant":
                        "secondary",

                    "payload":
                        _doctor_payload(
                            doctor
                        ),
                }
            ],

            "state_updates": {
                "grounded_selected_doctor":
                    selected,

                "selected_doctor":
                    selected,
            },
        }

    start_date, end_date, label = (
        availability_window(
            message
        )
    )

    try:
        slots = await service.availability(
            hospital_id=hospital_id,
            doctor_id=doctor.id,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception:
        return None

    # Keep cards useful rather than dumping
    # every slot for the next month.
    visible = slots[:12]

    slot_references = [
        {
            "slot_id":
                str(
                    slot.id
                ),

            "doctor_slot_id":
                str(
                    slot.id
                ),

            "doctor_id":
                str(
                    doctor.id
                ),

            "doctor_name":
                doctor.full_name,

            "date":
                slot.slot_date.isoformat(),

            "slot_date":
                slot.slot_date.isoformat(),

            "time":
                slot.start_time.strftime(
                    "%H:%M"
                ),

            "start_time":
                slot.start_time.strftime(
                    "%H:%M"
                ),
        }
        for slot in visible
    ]

    actions = [
        {
            "id":
                f"slot:{slot.id}",

            "type":
                "book_slot",

            "label":
                slot.start_time.strftime(
                    "%H:%M"
                ),

            "message":
                (
                    "Book "
                    f"{slot.start_time.strftime('%H:%M')} "
                    f"with {doctor.full_name} "
                    f"on {slot.slot_date.isoformat()}"
                ),

            "variant":
                "secondary",

            "payload": {
                "component":
                    "availability_slot",

                "doctor_name":
                    doctor.full_name,

                "date":
                    slot.slot_date.isoformat(),

                "start_time":
                    slot.start_time.strftime(
                        "%H:%M"
                    ),

                "clinic_name":
                    getattr(
                        doctor,
                        "clinic_name",
                        None,
                    ),
            },
        }
        for slot in visible
    ]

    if visible:

        response = (
            f"I found {len(visible)} available "
            f"{'time' if len(visible) == 1 else 'times'} "
            f"for {doctor.full_name} during {label}. "
            "Tell me which time you prefer."
        )

    else:

        response = (
            f"I could not find an available slot "
            f"for {doctor.full_name} during {label}."
        )

    return {
        "response":
            response,

        "actions":
            actions,

        "state_updates": {
            "grounded_selected_doctor":
                selected,

            "selected_doctor":
                selected,

            "grounded_available_slots":
                slot_references,

            "available_slots":
                slot_references,
        },
    }
