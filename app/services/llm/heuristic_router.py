import re
from dataclasses import dataclass
from typing import Literal


HeuristicIntent = Literal[
    "search_doctor",
    "check_availability",
    "book_appointment",
    "list_appointments",
    "cancel_appointment",
    "reschedule_appointment",
    "general_help",
    "unknown",
]


@dataclass(slots=True)
class HeuristicResult:
    matched: bool
    intent: HeuristicIntent
    confidence: float
    entities: dict | None = None


SEARCH_HINTS = (
    "find doctor",
    "find a doctor",
    "find me",
    "looking for",
    "someone who",
    "specialist",
    "doctor for",
    "prefer a",
    "preferably",
)

AVAILABILITY_HINTS = (
    "available",
    "availability",
    "free slot",
    "free time",
    "appointment time",
    "open slot",
    "tomorrow evening",
    "tomorrow morning",
    "schedule",
)

BOOKING_HINTS = (
    "book",
    "make an appointment",
    "schedule an appointment",
    "reserve",
)

LIST_HINTS = (
    "my appointment",
    "my appointments",
    "my booking",
    "my bookings",
    "appointments do i have",
    "what did i book",
    "upcoming appointment",
)

CANCEL_HINTS = (
    "cancel",
    "get rid of the booking",
    "remove my booking",
    "remove appointment",
    "don't want the appointment",
)

RESCHEDULE_HINTS = (
    "reschedule",
    "move the appointment",
    "move my appointment",
    "move the visit",
    "change the appointment",
    "change my appointment",
    "change the date",
    "change the time",
    "another day",
)

HELP_HINTS = (
    "what can medibook",
    "how does medibook",
    "how can medibook",
    "what can you do",
)


def normalize(
    message: str,
) -> str:
    return " ".join(
        message.lower().strip().split()
    )


def contains_any(
    text: str,
    hints: tuple[str, ...],
) -> bool:
    return any(
        hint in text
        for hint in hints
    )


def extract_date_words(
    text: str,
) -> str | None:

    for value in (
        "today",
        "tomorrow",
        "day after tomorrow",
    ):
        if value in text:
            return value

    match = re.search(
        r"\b20\d{2}-\d{2}-\d{2}\b",
        text,
    )

    return (
        match.group(0)
        if match
        else None
    )


def extract_time(
    text: str,
) -> str | None:

    match = re.search(
        r"\b(?:1[0-2]|0?[1-9])"
        r"(?::[0-5]\d)?\s*(?:am|pm)\b",
        text,
    )

    if match:
        return match.group(0)

    match = re.search(
        r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b",
        text,
    )

    return (
        match.group(0)
        if match
        else None
    )


def route_heuristically(
    message: str,
) -> HeuristicResult:

    text = normalize(
        message
    )

    entities = {
        "date": extract_date_words(
            text
        ),
        "time": extract_time(
            text
        ),
    }

    # More specific intents first.

    if contains_any(
        text,
        CANCEL_HINTS,
    ):
        return HeuristicResult(
            matched=True,
            intent="cancel_appointment",
            confidence=0.97,
            entities=entities,
        )

    if contains_any(
        text,
        RESCHEDULE_HINTS,
    ):
        return HeuristicResult(
            matched=True,
            intent="reschedule_appointment",
            confidence=0.96,
            entities=entities,
        )

    if contains_any(
        text,
        LIST_HINTS,
    ):
        return HeuristicResult(
            matched=True,
            intent="list_appointments",
            confidence=0.97,
            entities=entities,
        )

    if contains_any(
        text,
        BOOKING_HINTS,
    ):
        return HeuristicResult(
            matched=True,
            intent="book_appointment",
            confidence=0.95,
            entities=entities,
        )

    if contains_any(
        text,
        AVAILABILITY_HINTS,
    ):
        return HeuristicResult(
            matched=True,
            intent="check_availability",
            confidence=0.90,
            entities=entities,
        )

    if contains_any(
        text,
        SEARCH_HINTS,
    ):
        return HeuristicResult(
            matched=True,
            intent="search_doctor",
            confidence=0.88,
            entities=entities,
        )

    if contains_any(
        text,
        HELP_HINTS,
    ):
        return HeuristicResult(
            matched=True,
            intent="general_help",
            confidence=1.0,
        )

    return HeuristicResult(
        matched=False,
        intent="unknown",
        confidence=0.0,
    )
