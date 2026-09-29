from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class HospitalStaffAddRequest(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=320,
    )
    role: str = Field(
        min_length=1,
        max_length=64,
    )


class HospitalStaffUpdateRequest(BaseModel):
    role: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
    )
    is_active: bool | None = None


class HospitalStaffMutationResponse(BaseModel):
    membership_id: uuid.UUID
    user_id: uuid.UUID
    email: str
    role: str
    is_active: bool
