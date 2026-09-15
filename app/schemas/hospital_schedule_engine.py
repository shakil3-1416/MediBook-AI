from __future__ import annotations

from datetime import date, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


ExceptionKind = Literal[
    "leave",
    "closure",
    "override",
    "unavailable",
]


class ScheduleRuleCreate(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    slot_duration_minutes: int = Field(
        default=20,
        ge=5,
        le=240,
    )
    capacity: int = Field(
        default=1,
        ge=1,
        le=50,
    )
    valid_from: date | None = None
    valid_until: date | None = None


class ScheduleRuleUpdate(BaseModel):
    weekday: int | None = Field(
        default=None,
        ge=0,
        le=6,
    )
    start_time: time | None = None
    end_time: time | None = None
    slot_duration_minutes: int | None = Field(
        default=None,
        ge=5,
        le=240,
    )
    capacity: int | None = Field(
        default=None,
        ge=1,
        le=50,
    )
    valid_from: date | None = None
    valid_until: date | None = None
    is_active: bool | None = None


class ScheduleExceptionCreate(BaseModel):
    exception_date: date
    kind: ExceptionKind
    start_time: time | None = None
    end_time: time | None = None
    slot_duration_minutes: int | None = Field(
        default=None,
        ge=5,
        le=240,
    )
    capacity: int | None = Field(
        default=None,
        ge=1,
        le=50,
    )
    reason: str | None = Field(
        default=None,
        max_length=500,
    )


class ScheduleExceptionUpdate(BaseModel):
    exception_date: date | None = None
    kind: ExceptionKind | None = None
    start_time: time | None = None
    end_time: time | None = None
    slot_duration_minutes: int | None = Field(
        default=None,
        ge=5,
        le=240,
    )
    capacity: int | None = Field(
        default=None,
        ge=1,
        le=50,
    )
    reason: str | None = Field(
        default=None,
        max_length=500,
    )
    is_active: bool | None = None


class MaterializeRequest(BaseModel):
    start_date: date
    end_date: date


class MaterializedSlot(BaseModel):
    slot_date: date
    start_time: time
    capacity: int


class ScheduleConflict(BaseModel):
    slot_id: UUID
    slot_date: date
    start_time: time
    active_appointments: int
    reason: str


class SchedulePreview(BaseModel):
    doctor_id: UUID
    hospital_doctor_id: UUID
    start_date: date
    end_date: date
    desired_slots: int
    existing_slots: int
    conflicts: list[ScheduleConflict]


class ScheduleApplyResult(BaseModel):
    applied: bool
    created: int = 0
    updated: int = 0
    disabled: int = 0
    conflicts: list[ScheduleConflict] = []
