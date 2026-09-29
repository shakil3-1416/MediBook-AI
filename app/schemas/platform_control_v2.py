from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import (
    BaseModel,
    Field,
)


class HospitalDataMode(StrEnum):
    MANAGED = "managed"
    CONNECTED = "connected"
    HYBRID = "hybrid"


class PlatformHospitalStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class PlatformHospitalProvisionRequest(
    BaseModel
):
    name: str = Field(
        min_length=2,
        max_length=200,
    )

    slug: str = Field(
        min_length=2,
        max_length=120,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )

    timezone: str = Field(
        min_length=2,
        max_length=100,
    )

    initial_admin_email: str = Field(
        min_length=3,
        max_length=320,
    )

    data_mode: HospitalDataMode = (
        HospitalDataMode.MANAGED
    )

    activate: bool = False


class PlatformHospitalStatusUpdate(
    BaseModel
):
    status: PlatformHospitalStatus

    reason: str = Field(
        min_length=2,
        max_length=500,
    )


class PlatformControlHospitalSummary(
    BaseModel
):
    id: str

    slug: str

    name: str

    timezone: str | None = None

    status: str

    data_mode: str | None = None

    doctors: int = 0

    appointments: int = 0

    staff: int = 0

    integrations: int = 0

    schedule_rules: int = 0

    schedule_exceptions: int = 0

    integration_health: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict,
    )

    security: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict,
    )

    usage: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict,
    )


class PlatformControlHospitalDetail(
    PlatformControlHospitalSummary
):
    recent_integrations: list[
        dict[
            str,
            Any,
        ]
    ] = Field(
        default_factory=list,
    )

    recent_appointments: list[
        dict[
            str,
            Any,
        ]
    ] = Field(
        default_factory=list,
    )

    recent_platform_events: list[
        dict[
            str,
            Any,
        ]
    ] = Field(
        default_factory=list,
    )


class PlatformControlOverview(
    BaseModel
):
    hospitals_total: int

    hospitals_active: int

    hospitals_suspended: int

    appointments_total: int

    doctors_total: int

    staff_total: int

    integrations_total: int

    unhealthy_integrations: int

    copilot_proposals_total: int

    copilot_failed_executions: int
