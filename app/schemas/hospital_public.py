from __future__ import annotations

import uuid
from datetime import date, time

from pydantic import BaseModel


class PublicHospitalDoctor(BaseModel):
    id: uuid.UUID
    full_name: str
    gender: str
    qualification: str
    experience_years: int
    specialty: str
    clinic_name: str
    clinic_location: str
    consultation_fee: float


class PublicDoctorSlot(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    slot_date: date
    start_time: time
    is_available: bool
