from __future__ import annotations

from pydantic import (
    BaseModel,
    Field,
)


class ProviderCapabilityView(
    BaseModel
):
    provider: str

    executable: bool

    supports_pull: list[str] = Field(
        default_factory=list,
    )

    supports_push: list[str] = Field(
        default_factory=list,
    )

    supports_webhooks: bool = False

    supports_health_check: bool = False

    notes: str


class IntegrationContractView(
    BaseModel
):
    source_mode: str

    ownership: dict[str, str]

    executable: bool

    supported_resources: list[str]

    provider: ProviderCapabilityView

    warnings: list[str] = Field(
        default_factory=list,
    )
