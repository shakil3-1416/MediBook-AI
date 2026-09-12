from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.database import AsyncSessionFactory
from app.services.availability_service import AvailabilityService
from app.services.doctor_service import DoctorService


SPECIALTY_ALIASES = {
    "cardiologist": "cardiology",
    "cardiologists": "cardiology",
    "heart doctor": "cardiology",
    "heart specialist": "cardiology",

    "dermatologist": "dermatology",
    "dermatologists": "dermatology",
    "skin doctor": "dermatology",
    "skin specialist": "dermatology",

    "neurologist": "neurology",
    "neurologists": "neurology",
    "brain doctor": "neurology",
    "brain specialist": "neurology",
}


def normalize_specialty(
    value: str | None,
) -> str | None:

    if not value:
        return None

    cleaned = value.strip().lower()

    return SPECIALTY_ALIASES.get(
        cleaned,
        cleaned,
    )


def serialize_doctor(
    doctor: Any,
) -> dict[str, Any]:

    return {
        "id": str(doctor.id),
        "full_name": doctor.full_name,
        "specialty": doctor.specialty.name,
        "gender": doctor.gender,
        "qualification": doctor.qualification,
        "experience_years": doctor.experience_years,
        "clinic_name": doctor.clinic_name,
        "clinic_location": doctor.clinic_location,
        "consultation_fee": float(
            doctor.consultation_fee
        ),
    }


async def search_doctors(
    specialty: str | None = None,
    location: str | None = None,
    gender: str | None = None,
    max_fee: float | None = None,
    name: str | None = None,
) -> dict[str, Any]:

    specialty = normalize_specialty(
        specialty
    )

    fee = (
        Decimal(str(max_fee))
        if max_fee is not None
        else None
    )

    async with AsyncSessionFactory() as session:
        service = DoctorService(session)

        doctors = await service.search_doctors(
            specialty=specialty,
            location=location,
            gender=gender,
            max_fee=fee,
            name=name,
        )

        return {
            "count": len(doctors),
            "doctors": [
                serialize_doctor(doctor)
                for doctor in doctors
            ],
        }


async def get_doctor_slots(
    doctor_id: str,
    date: str,
) -> dict[str, Any]:

    try:
        parsed_doctor_id = UUID(
            doctor_id
        )

        parsed_date = (
            __import__("datetime")
            .date.fromisoformat(date)
        )

    except ValueError:
        return {
            "error": "invalid_input",
        }

    async with AsyncSessionFactory() as session:
        service = AvailabilityService(session)

        result = await service.get_doctor_availability(
            doctor_id=parsed_doctor_id,
            slot_date=parsed_date,
        )

        return result


TOOL_REGISTRY = {
    "search_doctors": search_doctors,
    "get_doctor_slots": get_doctor_slots,
}
