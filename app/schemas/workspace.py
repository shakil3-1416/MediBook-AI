from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
)


class PlatformHospitalSummary(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID
    slug: str
    name: str
    status: str
    timezone: str
    is_active: bool
    created_at: datetime


class WorkspaceSummary(BaseModel):

    id: uuid.UUID
    slug: str
    name: str
    status: str
    timezone: str
    role: str


class HospitalDoctorSummary(BaseModel):

    id: uuid.UUID
    full_name: str
    gender: str
    qualification: str
    experience_years: int
    clinic_name: str
    clinic_location: str
    consultation_fee: float
    is_active: bool
