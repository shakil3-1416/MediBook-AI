from typing import Literal

from pydantic import BaseModel


class MediBookIntent(BaseModel):
    intent: Literal[
        "greeting",
        "search_doctor",
        "check_availability",
        "book_appointment",
        "list_appointments",
        "cancel_appointment",
        "reschedule_appointment",
        "general_help",
        "medical_request",
        "unknown",
    ]

    doctor_name: str | None = None

    specialty: str | None = None

    location: str | None = None

    gender: Literal[
        "male",
        "female",
    ] | None = None

    date: str | None = None

    time: str | None = None

    confidence: float
