from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import (
    BaseModel,
    Field,
)


class IntegrationSyncDirection(
    StrEnum
):
    PULL = "pull"
    PUSH = "push"


class IntegrationSyncStatus(
    StrEnum
):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


class IntegrationSyncTrigger(
    BaseModel
):
    direction: IntegrationSyncDirection

    resource: str = Field(
        min_length=1,
        max_length=80,
    )

    idempotency_key: str | None = Field(
        default=None,
        min_length=8,
        max_length=200,
    )


class IntegrationSyncRunView(
    BaseModel
):
    id: str

    hospital_id: str

    integration_id: str

    provider: str

    resource: str

    direction: IntegrationSyncDirection

    status: IntegrationSyncStatus

    idempotency_key: str

    attempt: int

    max_attempts: int = 3

    next_attempt_at: str | None = None

    heartbeat_at: str | None = None

    claimed_by: str | None = None

    records_seen: int = 0

    records_changed: int = 0

    last_error: str | None = None

    created_at: str

    started_at: str | None = None

    completed_at: str | None = None

    result: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict,
    )
