from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


DoctorSourceMode = Literal["managed", "connected", "hybrid"]


class DoctorCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    specialty_id: UUID
    gender: str | None = Field(default=None, max_length=30)
    qualification: str | None = Field(default=None, max_length=500)
    experience_years: int = Field(default=0, ge=0, le=80)

    clinic_name: str = Field(min_length=2, max_length=200)
    clinic_location: str = Field(min_length=2, max_length=250)
    consultation_fee: Decimal = Field(ge=0)

    source_mode: DoctorSourceMode = "managed"
    external_doctor_id: str | None = Field(default=None, max_length=255)

    public_profile: dict[str, Any] = Field(default_factory=dict)
    operational_metadata: dict[str, Any] = Field(default_factory=dict)


class DoctorUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    specialty_id: UUID | None = None
    gender: str | None = Field(default=None, max_length=30)
    qualification: str | None = Field(default=None, max_length=500)
    experience_years: int | None = Field(default=None, ge=0, le=80)

    clinic_name: str | None = Field(default=None, min_length=2, max_length=200)
    clinic_location: str | None = Field(default=None, min_length=2, max_length=250)
    consultation_fee: Decimal | None = Field(default=None, ge=0)

    source_mode: DoctorSourceMode | None = None
    external_doctor_id: str | None = Field(default=None, max_length=255)

    public_profile: dict[str, Any] | None = None
    operational_metadata: dict[str, Any] | None = None


class DoctorActivationUpdate(BaseModel):
    is_active: bool


class DoctorRegistryItem(BaseModel):
    hospital_doctor_id: UUID
    doctor_id: UUID

    full_name: str
    specialty_id: UUID
    specialty_name: str | None = None

    gender: str | None = None
    qualification: str | None = None
    experience_years: int

    clinic_name: str | None = None
    clinic_location: str | None = None
    consultation_fee: Decimal | None = None

    source_mode: DoctorSourceMode
    external_doctor_id: str | None = None
    is_active: bool

    public_profile: dict[str, Any]
    operational_metadata: dict[str, Any]


class DoctorRegistryList(BaseModel):
    count: int
    doctors: list[DoctorRegistryItem]
