import re
from dataclasses import dataclass
from typing import Literal

from app.services.llm.policy import (
    MEDIBOOK_CAPABILITIES_RESPONSE,
)


FastRouteType = Literal[
    "capabilities",
    "greeting",
    "search_doctor",
    "none",
]


@dataclass(slots=True)
class FastRouteResult:
    matched: bool
    route: FastRouteType
    response: str | None = None
    entities: dict | None = None


CAPABILITY_PATTERNS = (
    r"\bwhat can medibook do\b",
    r"\bwhat can you do\b",
    r"\bhow can medibook help\b",
    r"\bhow can you help\b",
    r"\bmedibook features\b",
    r"\bwhat does medibook do\b",
    r"\bwhat are your capabilities\b",
)


GREETING_PATTERNS = (
    r"^hi[!. ]*$",
    r"^hello[!. ]*$",
    r"^hey[!. ]*$",
    r"^good morning[!. ]*$",
    r"^good afternoon[!. ]*$",
    r"^good evening[!. ]*$",
)


SPECIALTY_ALIASES = {
    "cardiology": (
        "cardiology",
        "cardiologist",
        "heart",
        "heart problem",
        "heart problems",
        "heart specialist",
        "cardiac",
    ),
    "dermatology": (
        "dermatology",
        "dermatologist",
        "skin",
        "skin problem",
        "skin problems",
        "skin specialist",
    ),
    "neurology": (
        "neurology",
        "neurologist",
        "brain",
        "nerve",
        "neurological",
        "brain specialist",
    ),
}


KNOWN_LOCATIONS = (
    "dhanmondi",
    "mirpur",
    "uttara",
)


FEMALE_HINTS = (
    "female",
    "woman",
    "women",
    "lady doctor",
)


MALE_HINTS = (
    "male",
    "man",
    "men",
)


DOCTOR_SEARCH_HINTS = (
    "find",
    "doctor",
    "specialist",
    "someone who treats",
    "someone for",
    "looking for",
    "preferably",
)


GREETING_RESPONSE = (
    "Hi! I can help you find a doctor, check real appointment "
    "availability, book a visit, or manage an existing MediBook appointment."
)


def detect_specialty(
    text: str,
) -> str | None:

    for specialty, aliases in SPECIALTY_ALIASES.items():
        if any(
            alias in text
            for alias in aliases
        ):
            return specialty

    return None


def detect_location(
    text: str,
) -> str | None:

    for location in KNOWN_LOCATIONS:
        if location in text:
            return location.title()

    return None


def detect_gender(
    text: str,
) -> str | None:

    if any(
        hint in text
        for hint in FEMALE_HINTS
    ):
        return "female"

    if any(
        hint in text
        for hint in MALE_HINTS
    ):
        return "male"

    return None


def fast_route(
    message: str,
) -> FastRouteResult:

    text = " ".join(
        message.lower().strip().split()
    )

    for pattern in CAPABILITY_PATTERNS:
        if re.search(pattern, text):
            return FastRouteResult(
                matched=True,
                route="capabilities",
                response=MEDIBOOK_CAPABILITIES_RESPONSE,
            )

    for pattern in GREETING_PATTERNS:
        if re.search(pattern, text):
            return FastRouteResult(
                matched=True,
                route="greeting",
                response=GREETING_RESPONSE,
            )

    specialty = detect_specialty(
        text
    )

    location = detect_location(
        text
    )

    gender = detect_gender(
        text
    )

    looks_like_search = any(
        hint in text
        for hint in DOCTOR_SEARCH_HINTS
    )

    if specialty and (
        looks_like_search
        or location
        or gender
    ):
        return FastRouteResult(
            matched=True,
            route="search_doctor",
            entities={
                "specialty": specialty,
                "location": location,
                "gender": gender,
            },
        )

    return FastRouteResult(
        matched=False,
        route="none",
    )
