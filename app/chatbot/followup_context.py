from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Optional

import redis


@dataclass
class FollowupState:
    intent: Optional[str] = None
    doctor_name: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None


def _redis_client():
    url = os.getenv(
        "REDIS_URL",
        "redis://127.0.0.1:6379/0",
    )

    return redis.Redis.from_url(
        url,
        decode_responses=True,
    )


def _key(
    conversation_id: str,
) -> str:
    return (
        "medibook:followup:"
        + conversation_id
    )


def load(
    conversation_id: str | None,
) -> FollowupState:
    if not conversation_id:
        return FollowupState()

    try:
        raw = _redis_client().get(
            _key(conversation_id)
        )

        if not raw:
            return FollowupState()

        payload = json.loads(raw)

        return FollowupState(
            intent=payload.get("intent"),
            doctor_name=payload.get(
                "doctor_name"
            ),
            date=payload.get("date"),
            time=payload.get("time"),
        )

    except Exception:
        return FollowupState()


def save(
    conversation_id: str | None,
    state: FollowupState,
) -> None:
    if not conversation_id:
        return

    try:
        _redis_client().setex(
            _key(conversation_id),
            60 * 60 * 6,
            json.dumps(
                asdict(state)
            ),
        )
    except Exception:
        # Do not fail the patient request solely
        # because auxiliary follow-up state failed.
        return


def extract_doctor_name(
    message: str,
) -> str | None:
    # Works with examples such as:
    # Dr. Farhana Ahmed
    # Dr. Abid Ahmed 093
    pattern = re.compile(
        r"\bDr\.?\s+"
        r"([A-Za-z][A-Za-z .'-]*?"
        r"(?:\s+\d{1,4})?)"
        r"(?="
        r"[,.!?]"
        r"|$"
        r"|\s+(?:on|at|for|tomorrow|today|"
        r"check|book|give|show|appointment|"
        r"availability|available)\b"
        r")",
        re.IGNORECASE,
    )

    match = pattern.search(message)

    if not match:
        return None

    value = " ".join(
        match.group(1).split()
    )

    return f"Dr. {value}"


def extract_date(
    message: str,
) -> str | None:
    match = re.search(
        r"\b(20\d{2}-\d{2}-\d{2})\b",
        message,
    )

    return (
        match.group(1)
        if match
        else None
    )


def extract_time(
    message: str,
) -> str | None:
    match = re.search(
        r"\b([01]?\d|2[0-3]):([0-5]\d)\b",
        message,
    )

    if not match:
        return None

    return (
        f"{int(match.group(1)):02d}:"
        f"{match.group(2)}"
    )


FOLLOWUP_PHRASES = {
    "do it",
    "do it.",
    "yes do it",
    "yes, do it",
    "go ahead",
    "go ahead.",
    "please do",
    "please do it",
    "proceed",
    "continue",
    "check it",
    "book it",
}


def _compact(
    message: str,
) -> str:
    return " ".join(
        message.lower().strip().split()
    )


def normalize_for_context(
    message: str,
    conversation_id: str | None,
) -> str:
    """
    Deterministic continuity bridge.

    The LLM is not asked to guess what "do it"
    refers to. We reconstruct a complete request
    from conversation-scoped state.
    """

    state = load(
        conversation_id
    )

    compact = _compact(
        message
    )

    if (
        conversation_id
        and compact
        in FOLLOWUP_PHRASES
    ):
        if (
            state.intent == "book"
            and state.doctor_name
            and state.date
            and state.time
        ):
            # "Do it" after a fully specified booking
            # means confirmation.
            return "Confirm"

        if (
            state.intent == "book"
            and state.doctor_name
        ):
            command = (
                "Continue booking exactly "
                f"{state.doctor_name}."
            )

            if state.date:
                command += (
                    f" Requested date: "
                    f"{state.date}."
                )

            return command

        if (
            state.intent
            == "availability"
            and state.doctor_name
        ):
            # If the prior request already contained a date,
            # "do it" after "I can check another date" should
            # advance rather than repeat the unavailable date.
            if state.date:
                return (
                    "Find the next real available "
                    "appointment slots after "
                    f"{state.date} for exactly "
                    f"{state.doctor_name}. "
                    "Do not substitute another doctor."
                )

            return (
                "Check real appointment availability "
                f"for exactly {state.doctor_name}. "
                "Do not substitute another doctor."
            )

    # Explicit doctor requests are strengthened so the
    # model/router must not silently substitute a doctor.
    doctor_name = extract_doctor_name(
        message
    )

    normalized = message

    if doctor_name:
        normalized = (
            message.rstrip()
            + "\n\n"
            + "Exact doctor constraint: use exactly "
            + doctor_name
            + ". Do not substitute a different doctor."
        )

    return normalized


def capture_context(
    message: str,
    conversation_id: str | None,
) -> None:
    if not conversation_id:
        return

    # Never replace useful state with "do it".
    if _compact(message) in FOLLOWUP_PHRASES:
        return

    state = load(
        conversation_id
    )

    doctor = extract_doctor_name(
        message
    )

    date = extract_date(
        message
    )

    time = extract_time(
        message
    )

    if doctor:
        state.doctor_name = doctor

    if date:
        state.date = date

    if time:
        state.time = time

    lower = message.lower()

    booking_words = (
        "book",
        "appointment with",
        "give me an appointment",
        "make an appointment",
    )

    availability_words = (
        "availability",
        "available",
        "check availability",
        "check the real",
    )

    if any(
        phrase in lower
        for phrase in booking_words
    ):
        state.intent = "book"

    elif any(
        phrase in lower
        for phrase in availability_words
    ):
        state.intent = "availability"

    save(
        conversation_id,
        state,
    )
