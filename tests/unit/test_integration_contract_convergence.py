from __future__ import annotations

from pathlib import Path


def test_sync_runtime_uses_canonical_ownership_policy():
    source = Path(
        "app/services/"
        "integration_sync_runtime.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "decide_sync_direction"
        in source
    )

    assert (
        "IntegrationOwnershipError"
        in source
    )


def test_integration_api_has_contract_validation_boundary():
    source = Path(
        "app/api/v1/"
        "hospital_integrations.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "validate_integration_contract"
        in source
    )

    assert (
        "_validate_contract_or_422"
        in source
    )


def test_integration_service_has_contract_validation_boundary():
    source = Path(
        "app/services/"
        "integration_center.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "validate_integration_configuration"
        in source
    )


def test_no_real_provider_contract_is_invented():
    source = Path(
        "app/services/"
        "integration_provider_contracts.py"
    ).read_text(
        encoding="utf-8",
    ).lower()

    # Provider contracts must only become executable
    # through explicit runtime registration.
    assert (
        "executable: bool = false"
        in source
    )

    assert (
        "no executable provider contract"
        in source
    )
