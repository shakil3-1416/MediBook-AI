from datetime import date
from uuid import UUID

from pydantic import BaseModel


class AvailabilitySlotResponse(BaseModel):
    start_time: str


class DoctorAvailabilityResponse(BaseModel):
    doctor_id: UUID
    doctor_name: str
    date: date
    available_slots: list[str]
