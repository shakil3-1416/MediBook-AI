from __future__ import annotations

import pytest

from app.services.integration_contract_validation import (
    validate_integration_contract,
)

from app.services.integration_ownership import (
    DataMode,
    IntegrationOwnershipError,
    ResourceOwner,
    decide_sync_direction,
    normalize_ownership,
)

from app.services.integration_provider_contracts import (
    ProviderCapabilityContract,
    ProviderContractRegistry,
)


def test_managed_external_sync_is_blocked():
    pull = decide_sync_direction(
        source_mode="managed",
        ownership={},
        resource="appointments",
        direction="pull",
    )

    push = decide_sync_direction(
        source_mode="managed",
        ownership={},
        resource="appointments",
        direction="push",
    )

    assert not pull.allowed
    assert not push.allowed


def test_connected_defaults_to_external_authority():
    pull = decide_sync_direction(
        source_mode="connected",
        ownership={},
        resource="appointments",
        direction="pull",
    )

    push = decide_sync_direction(
        source_mode="connected",
        ownership={},
        resource="appointments",
        direction="push",
    )

    assert pull.allowed

    assert (
        pull.owner
        ==
        ResourceOwner.EXTERNAL
    )

    assert not push.allowed


def test_connected_cannot_mark_resource_medibook_owned():
    with pytest.raises(
        IntegrationOwnershipError
    ):
        normalize_ownership(
            source_mode="connected",
            ownership={
                "appointments":
                    "medibook",
            },
        )


def test_hybrid_requires_explicit_ownership():
    with pytest.raises(
        IntegrationOwnershipError
    ):
        normalize_ownership(
            source_mode="hybrid",
            ownership={},
        )


def test_hybrid_external_resource_is_pull_only():
    pull = decide_sync_direction(
        source_mode="hybrid",
        ownership={
            "appointments":
                "external",
        },
        resource="appointments",
        direction="pull",
    )

    push = decide_sync_direction(
        source_mode="hybrid",
        ownership={
            "appointments":
                "external",
        },
        resource="appointments",
        direction="push",
    )

    assert pull.allowed
    assert not push.allowed


def test_hybrid_medibook_resource_is_push_only():
    pull = decide_sync_direction(
        source_mode="hybrid",
        ownership={
            "schedules":
                "medibook",
        },
        resource="schedules",
        direction="pull",
    )

    push = decide_sync_direction(
        source_mode="hybrid",
        ownership={
            "schedules":
                "medibook",
        },
        resource="schedules",
        direction="push",
    )

    assert not pull.allowed
    assert push.allowed


def test_hybrid_unspecified_resource_is_blocked():
    decision = decide_sync_direction(
        source_mode="hybrid",
        ownership={
            "schedules":
                "medibook",
        },
        resource="appointments",
        direction="pull",
    )

    assert not decision.allowed
    assert decision.owner is None


def test_unknown_resource_fails_closed():
    with pytest.raises(
        IntegrationOwnershipError
    ):
        decide_sync_direction(
            source_mode="connected",
            ownership={},
            resource="invented-resource",
            direction="pull",
        )


def test_unknown_provider_contract_is_not_executable():
    registry = ProviderContractRegistry()

    contract = registry.resolve(
        "unknown-provider"
    )

    assert not contract.executable

    assert (
        contract.supports_pull
        ==
        frozenset()
    )

    assert (
        contract.supports_push
        ==
        frozenset()
    )


def test_registered_provider_contract_is_explicit():
    registry = ProviderContractRegistry()

    registry.register(
        ProviderCapabilityContract(
            provider="fake-provider",
            executable=True,
            supports_pull=
                frozenset(
                    {
                        "appointments",
                    }
                ),
            supports_push=
                frozenset(
                    {
                        "schedules",
                    }
                ),
            supports_webhooks=True,
            supports_health_check=True,
            notes="test only",
        )
    )

    contract = registry.resolve(
        "fake-provider"
    )

    assert contract.executable

    assert (
        "appointments"
        in contract.supports_pull
    )

    assert (
        "schedules"
        in contract.supports_push
    )


def test_connected_validation_warns_when_adapter_missing():
    result = validate_integration_contract(
        source_mode="connected",
        provider="not-installed",
        ownership={},
    )

    assert (
        result.source_mode
        ==
        DataMode.CONNECTED.value
    )

    assert not result.executable

    assert result.warnings


def test_connected_requires_provider():
    with pytest.raises(
        IntegrationOwnershipError
    ):
        validate_integration_contract(
            source_mode="connected",
            provider="",
            ownership={},
        )
