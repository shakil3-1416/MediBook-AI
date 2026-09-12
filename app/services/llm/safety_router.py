import re
from dataclasses import dataclass
from typing import Literal


SafetyRoute = Literal[
    "medical",
    "emergency",
    "none",
]


@dataclass(slots=True)
class SafetyResult:
    matched: bool
    route: SafetyRoute
    response: str | None = None


MEDICAL_PATTERNS = (
    r"\bwhat medicine\b",
    r"\bwhich medicine\b",
    r"\bwhat medication\b",
    r"\bwhich medication\b",
    r"\bwhat dosage\b",
    r"\bwhat dose\b",
    r"\bhow much .* should i take\b",
    r"\bdiagnose\b",
    r"\bdo i have\b",
    r"\bwhat disease\b",
    r"\binterpret .* report\b",
    r"\binterpret .* result\b",
    r"\bwhat treatment\b",
    r"\btreatment for\b",
)


EMERGENCY_PATTERNS = (
    r"\bchest pain\b",
    r"\bcan't breathe\b",
    r"\bcannot breathe\b",
    r"\bsevere bleeding\b",
    r"\bunconscious\b",
    r"\bpassed out\b",
    r"\bstroke\b",
    r"\bheart attack\b",
)


MEDICAL_RESPONSE = (
    "MediBook does not diagnose conditions, recommend treatment, "
    "prescribe medication, provide dosage advice, or interpret medical "
    "reports. I can help you find and book an appropriate doctor."
)


EMERGENCY_RESPONSE = (
    "This may require urgent medical attention. MediBook cannot provide "
    "emergency diagnosis or treatment. Please seek urgent in-person medical "
    "care. I can also help you find an appropriate doctor through MediBook."
)


def safety_route(
    message: str,
) -> SafetyResult:

    text = " ".join(
        message.lower().strip().split()
    )

    for pattern in EMERGENCY_PATTERNS:
        if re.search(pattern, text):
            return SafetyResult(
                matched=True,
                route="emergency",
                response=EMERGENCY_RESPONSE,
            )

    for pattern in MEDICAL_PATTERNS:
        if re.search(pattern, text):
            return SafetyResult(
                matched=True,
                route="medical",
                response=MEDICAL_RESPONSE,
            )

    return SafetyResult(
        matched=False,
        route="none",
    )
