"""Direct answers from the hospital's own data, without the language model.

These cover questions the small local model answered slowly or wrongly:
free appointment times, booking requests by specialty, consultation fees,
hospital information and off-topic questions. Every answer is limited to
the hospital the patient is chatting with.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chatbot.hospital_grounded_directory import _doctor_payload
from app.models.hospital import HospitalDoctor
from app.models.schedule import DoctorSlot
from app.services.hospital_directory_service import HospitalDirectoryService

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
WINDOWS = {
    "morning": (time(6, 0), time(12, 0)),
    "afternoon": (time(12, 0), time(17, 0)),
    "evening": (time(17, 0), time(21, 30)),
    "night": (time(19, 0), time(23, 59)),
}
SPECIALTY_HINTS = (
    (r"\bcardi\w*|\bheart\b", "cardio", "cardiology"),
    (r"\bdermat\w*|\bskin\b", "dermat", "dermatology"),
    (r"\bneuro\w*|\bbrain\b", "neuro", "neurology"),
    (r"\bgyn\w*|\bgynae\w*|\bobstet\w*|\bpregnan\w*", "gyn", "gynecology"),
    (r"\bpa?ediatric\w*|\bchild(ren)?\b|\bbaby\b", "pediatric", "pediatrics"),
    (r"\borthop\w*|\bbones?\b|\bjoints?\b", "ortho", "orthopedics"),
    (r"\bophthalm\w*|\beyes?\b", "ophthalm", "eye care"),
    (r"\bent\b|\bears?\b|\bthroat\b|\bnose\b", "ent", "ENT"),
    (r"\boncolog\w*|\bcancer\b", "oncolog", "oncology"),
    (r"\bpulmon\w*|\blungs?\b|\bchest specialist\b", "pulmon", "pulmonology"),
    (r"\bsurg\w*", "surg", "surgery"),
    (r"\bphysical medicine\b|\bphysio\w*|\brehab\w*", "physical", "physical medicine"),
    (r"\bpsychiat\w*|\bmental health\b", "psychiat", "psychiatry"),
    (r"\burolog\w*|\bkidney\b", "urolog", "urology"),
    (r"\bgastro\w*|\bstomach\b", "gastro", "gastroenterology"),
    (r"\bmedicine specialist\b|\binternal medicine\b|\bgeneral physician\b", "medicine", "medicine"),
)

_OFF_TOPIC = re.compile(r"\b(weather|rain today|news|cricket|football|score|joke|movie|song|lyrics|stock|bitcoin|crypto|recipe|politics|election)\b")
_CARE_WORDS = re.compile(r"\b(doctor|doctors|appointment|appointments|book|clinic|hospital|pain|sick|ill|medicine|fever)\b")
_HOSPITAL_INFO = re.compile(r"\b(where|address|location|located|directions|reach|contact|phone|hotline|call you|visiting hours|opening hours|open hours)\b")
_HOSPITAL_WORDS = re.compile(r"\b(hospital|clinic|you|your|this place|centre|center)\b")
_FEE = re.compile(r"\b(fee|fees|cost|costs|charge|charges|price|prices|how much)\b")
_AVAILABILITY = re.compile(r"\b(available|availability|free (slot|slots|time|times)|open (slot|slots)|earliest|soonest|when can i see)\b")
_BOOK = re.compile(r"\b(book|booking|make an appointment|get an appointment|schedule an appointment|need an appointment|want an appointment)\b")
_MANAGE = re.compile(r"\b(cancel|reschedule|my appointment|my appointments|my booking|my bookings)\b")
_NAMED_DOCTOR = re.compile(r"\b(dr|doctor)\.?\s+[a-z]{3,}\s+[a-z]{3,}")


@dataclass
class Question:
    kind: str
    specialty_key: str | None = None
    specialty_label: str | None = None
    start: date | None = None
    end: date | None = None
    window: str | None = None
    when_label: str = "in the next 7 days"
    extra: dict = field(default_factory=dict)


def _normalize(message: str) -> str:
    return " ".join(message.lower().replace("’", "'").split())


def _specialty(text: str) -> tuple[str | None, str | None]:
    for pattern, key, label in SPECIALTY_HINTS:
        if re.search(pattern, text):
            return key, label
    return None, None


def specialty_matches(name: str | None, key: str) -> bool:
    value = (name or "").strip().lower()
    if key == "ent":
        return value in {"ent", "otolaryngology", "ear, nose and throat"} or value.startswith("ent ")
    return key in value


def _dates(text: str, today: date) -> tuple[date, date, str]:
    if "day after tomorrow" in text:
        day = today + timedelta(days=2)
        return day, day, f"on {day:%A}"
    if re.search(r"\b(tomorrow|tmrw|tomorow)\b", text):
        day = today + timedelta(days=1)
        return day, day, "tomorrow"
    if re.search(r"\b(today|tonight)\b", text):
        return today, today, "today"
    for index, name in enumerate(WEEKDAYS):
        if re.search(rf"\b{name}\b", text):
            day = today + timedelta(days=(index - today.weekday()) % 7)
            return day, day, f"on {name.title()}"
    return today, today + timedelta(days=6), "in the next 7 days"


def classify(message: str, today: date) -> Question | None:
    """Decide whether a message gets a direct answer. Pure, so it is easy to test."""
    text = _normalize(message)
    if text == "":
        return None
    if _OFF_TOPIC.search(text) and _CARE_WORDS.search(text) is None:
        return Question(kind="off_topic")
    if _HOSPITAL_INFO.search(text) and _HOSPITAL_WORDS.search(text) and _NAMED_DOCTOR.search(text) is None:
        return Question(kind="hospital_info")
    if _MANAGE.search(text) or _NAMED_DOCTOR.search(text):
        return None
    key, label = _specialty(text)
    if _FEE.search(text):
        return Question(kind="fees", specialty_key=key, specialty_label=label)
    if _AVAILABILITY.search(text) or _BOOK.search(text):
        start, end, when = _dates(text, today)
        window = next((name for name in WINDOWS if re.search(rf"\b{name}\b", text)), None)
        if window:
            when = f"{when} in the {window}" if when != "in the next 7 days" else f"in the {window}s over the next 7 days"
        return Question(kind="availability", specialty_key=key, specialty_label=label, start=start, end=end, window=window, when_label=when)
    return None


def _clock(value: time) -> str:
    return f"{value.hour % 12 or 12}:{value.minute:02d} {'am' if value.hour < 12 else 'pm'}"


def _day(value: date) -> str:
    return f"{value:%a} {value.day} {value:%b}"


def _taka(value) -> str:
    try:
        return f"Tk {int(value):,}"
    except (TypeError, ValueError):
        return "fee not listed"


def _specialty_name(doctor) -> str | None:
    return getattr(getattr(doctor, "specialty", None), "name", None)


def _cards(doctors: list) -> tuple[list[dict], list[dict]]:
    references, actions = [], []
    for index, doctor in enumerate(doctors, 1):
        specialty = _specialty_name(doctor)
        references.append({
            "position": index,
            "id": str(doctor.id),
            "doctor_id": str(doctor.id),
            "doctor_name": doctor.full_name,
            "full_name": doctor.full_name,
            "specialty": specialty,
        })
        actions.append({
            "id": f"doctor:{doctor.id}",
            "type": "send_message",
            "label": doctor.full_name,
            "message": f"Tell me about {doctor.full_name}",
            "variant": "secondary",
            "payload": _doctor_payload(doctor),
        })
    return references, actions


async def direct_answer(session: AsyncSession, *, hospital, message: str) -> dict | None:
    """Answer from the hospital's data, or return None to let the normal flow continue."""
    zone = ZoneInfo(getattr(hospital, "timezone", None) or "Asia/Dhaka")
    now = datetime.now(zone)
    question = classify(message, now.date())
    if question is None:
        return None
    name = hospital.name

    if question.kind == "off_topic":
        return {"response": (
            f"I’m the appointment assistant for {name}, so I can’t help with that. "
            "I can find a doctor, show free appointment times, or book and manage your appointments."
        ), "actions": [], "references": []}

    if question.kind == "hospital_info":
        return {"response": (
            f"You’re chatting with {name}. Its address and contact details aren’t in MediBook yet, "
            "so please check the hospital’s website or call the hospital for directions. "
            "I can find a doctor here, show free appointment times or book an appointment."
        ), "actions": [], "references": []}

    doctors = await HospitalDirectoryService(session).list_doctors(hospital_id=hospital.id, limit=500)
    if question.specialty_key:
        doctors = [doctor for doctor in doctors if specialty_matches(_specialty_name(doctor), question.specialty_key)]
    label = f"{question.specialty_label} " if question.specialty_label else ""
    if not doctors:
        return {"response": (
            f"I couldn’t find {label}doctors at {name}. Ask me to show all doctors here and I’ll list the specialties available."
        ), "actions": [], "references": []}

    if question.kind == "fees":
        priced = sorted(doctors, key=lambda doctor: (getattr(doctor, "consultation_fee", None) is None, getattr(doctor, "consultation_fee", 0) or 0))[:8]
        lines = [
            f"{index}. {doctor.full_name} ({_specialty_name(doctor) or 'specialty not listed'}): {_taka(getattr(doctor, 'consultation_fee', None))}"
            for index, doctor in enumerate(priced, 1)
        ]
        references, actions = _cards(priced)
        return {"response": (
            f"Consultation fees for {label}doctors at {name}:\n" + "\n".join(lines)
            + "\n\nThe hospital confirms the final fee at your visit. Tap a doctor to see their free times."
        ), "actions": actions, "references": references}

    by_id = {doctor.id: doctor for doctor in doctors}
    rows = (await session.execute(
        select(DoctorSlot.doctor_id, DoctorSlot.slot_date, DoctorSlot.start_time)
        .join(HospitalDoctor, HospitalDoctor.id == DoctorSlot.hospital_doctor_id)
        .where(
            HospitalDoctor.hospital_id == hospital.id,
            HospitalDoctor.is_active.is_(True),
            DoctorSlot.slot_date >= question.start,
            DoctorSlot.slot_date <= question.end,
            DoctorSlot.is_enabled.is_(True),
            DoctorSlot.is_available.is_(True),
            DoctorSlot.doctor_id.in_(list(by_id)),
        )
        .order_by(DoctorSlot.slot_date, DoctorSlot.start_time)
        .limit(3000)
    )).all()
    window = WINDOWS.get(question.window) if question.window else None
    soonest = (now + timedelta(minutes=15)).time()
    first: dict = {}
    for doctor_id, slot_date, start_time in rows:
        if window and (start_time < window[0] or start_time >= window[1]):
            continue
        if slot_date == now.date() and start_time <= soonest:
            continue
        entry = first.setdefault(doctor_id, {"day": slot_date, "times": []})
        if entry["day"] == slot_date and len(entry["times"]) < 3:
            entry["times"].append(start_time)
    if not first:
        return {"response": (
            f"I couldn’t find free {label}appointment times {question.when_label} at {name}. "
            "Try another day, or ask me to show the doctors here."
        ), "actions": [], "references": []}
    chosen = [by_id[doctor_id] for doctor_id in list(first)[:6]]
    lines = [
        f"{index}. {doctor.full_name} ({_specialty_name(doctor) or 'specialty not listed'}): "
        f"{_day(first[doctor.id]['day'])} at {', '.join(_clock(value) for value in first[doctor.id]['times'])}"
        for index, doctor in enumerate(chosen, 1)
    ]
    references, actions = _cards(chosen)
    return {"response": (
        f"Free {label}appointment times {question.when_label} at {name}:\n" + "\n".join(lines)
        + "\n\nTap a doctor, or reply with their name and the time you want, and I’ll book it."
    ), "actions": actions, "references": references}
