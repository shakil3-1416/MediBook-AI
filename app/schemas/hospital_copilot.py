from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class HospitalCopilotIntent(StrEnum):
    OVERVIEW = "overview"
    APPOINTMENTS = "appointments"
    DOCTORS = "doctors"
    CAPACITY = "capacity"
    SCHEDULES = "schedules"
    INTEGRATIONS = "integrations"
    STAFF = "staff"
    RECENT_CHANGES = "recent_changes"

    PROPOSE_CAPACITY = "propose_capacity"
    PROPOSE_CLOSURE = "propose_closure"

    HELP = "help"
    UNKNOWN = "unknown"


class HospitalCopilotActionType(StrEnum):
    SCHEDULE_CAPACITY_CHANGE = (
        "schedule_capacity_change"
    )

    SCHEDULE_CLOSURE = (
        "schedule_closure"
    )


class HospitalCopilotRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
    )


class HospitalCopilotToolResult(BaseModel):
    tool: str

    available: bool = True

    data: dict[str, Any] = Field(
        default_factory=dict,
    )

    note: str | None = None


class CapacityProposalPayload(BaseModel):
    schedule_rule_id: str = Field(
        min_length=1,
        max_length=128,
    )

    new_capacity: int = Field(
        ge=1,
        le=500,
    )


class ClosureProposalPayload(BaseModel):
    hospital_doctor_id: str = Field(
        min_length=1,
        max_length=128,
    )

    date: str = Field(
        min_length=8,
        max_length=32,
    )

    reason: str = Field(
        min_length=1,
        max_length=500,
    )


class HospitalCopilotProposalCreate(BaseModel):
    action_type: HospitalCopilotActionType

    payload: dict[str, Any]


class HospitalCopilotProposal(BaseModel):
    id: str

    action_type: HospitalCopilotActionType

    payload: dict[str, Any]

    impact: dict[str, Any]

    status: str

    execution_supported: bool

    execution_result: (
        dict[str, Any] | None
    ) = None


class HospitalCopilotProposalConfirmation(
    BaseModel
):
    confirm: bool


class HospitalCopilotResponse(BaseModel):
    intent: HospitalCopilotIntent

    answer: str

    mode: Literal[
        "deterministic",
        "llm_grounded",
    ] = "deterministic"

    tools: list[
        HospitalCopilotToolResult
    ] = Field(
        default_factory=list,
    )

    proposal_required: bool = False

    proposal_id: str | None = None

    proposal: (
        HospitalCopilotProposal
        | None
    ) = None

    warnings: list[str] = Field(
        default_factory=list,
    )
