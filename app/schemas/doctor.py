from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SpecialtyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    gender: str | None
    qualification: str | None
    experience_years: int

    specialty: SpecialtyResponse

    clinic_name: str
    clinic_location: str
    consultation_fee: Decimal


class DoctorSearchResponse(BaseModel):
    count: int
    doctors: list[DoctorResponse]
