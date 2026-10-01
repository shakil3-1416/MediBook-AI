from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import event

from app.models.hospital import (
    HospitalIntegration,
)

from app.services.integration_ownership import (
    DataMode,
    IntegrationOwnershipError,
    SUPPORTED_SYNC_RESOURCES,
    normalize_mode,
    normalize_ownership,
)

from app.services.integration_provider_contracts import (
    ProviderCapabilityContract,
    contracts,
)


@dataclass(
    frozen=True,
    slots=True,
)
class IntegrationContractValidation:
    source_mode: str

    ownership: dict[str, str]

    provider_contract: ProviderCapabilityContract

    executable: bool

    warnings: tuple[str, ...]


def validate_integration_contract(
    *,
    source_mode: Any,
    provider: Any,
    ownership: dict[str, Any] | None,
) -> IntegrationContractValidation:
    mode = normalize_mode(
        source_mode
    )

    normalized_ownership = (
        normalize_ownership(
            source_mode=
                mode,

            ownership=
                ownership,
        )
    )


    provider_name = str(
        provider
        or ""
    ).strip().lower()


    if (
        mode != DataMode.MANAGED
        and not provider_name
    ):
        raise IntegrationOwnershipError(
            "Connected and Hybrid modes "
            "require a provider identifier."
        )


    provider_contract = contracts.resolve(
        provider_name
    )


    warnings: list[
        str
    ] = []


    if mode == DataMode.MANAGED:
        executable = False

    else:
        executable = (
            provider_contract.executable
        )

        if not executable:
            warnings.append(
                "Provider configuration is valid, "
                "but no executable adapter is "
                "registered yet."
            )


    if mode == DataMode.HYBRID:
        missing = (
            SUPPORTED_SYNC_RESOURCES
            -
            normalized_ownership.keys()
        )

        if missing:
            warnings.append(
                "Hybrid ownership is only defined "
                "for: "
                + ", ".join(
                    sorted(
                        normalized_ownership
                    )
                )
                + ". Unspecified resources cannot sync."
            )


    return IntegrationContractValidation(
        source_mode=
            mode.value,

        ownership=
            normalized_ownership,

        provider_contract=
            provider_contract,

        executable=
            executable,

        warnings=
            tuple(
                warnings
            ),
    )


def validate_hospital_integration_model(
    target:
        HospitalIntegration,
) -> IntegrationContractValidation:
    validation = validate_integration_contract(
        source_mode=
            target.source_mode,

        provider=
            target.provider,

        ownership=
            target.ownership
            or {},
    )


    # Canonicalize persisted ownership aliases.
    target.source_mode = (
        validation.source_mode
    )

    target.ownership = dict(
        validation.ownership
    )


    return validation


@event.listens_for(
    HospitalIntegration,
    "before_insert",
)
def _hospital_integration_contract_before_insert(
    mapper,
    connection,
    target:
        HospitalIntegration,
) -> None:
    del mapper
    del connection

    validate_hospital_integration_model(
        target
    )


@event.listens_for(
    HospitalIntegration,
    "before_update",
)
def _hospital_integration_contract_before_update(
    mapper,
    connection,
    target:
        HospitalIntegration,
) -> None:
    del mapper
    del connection

    validate_hospital_integration_model(
        target
    )
