from types import SimpleNamespace

import pytest

from app.services.integration_center import (
    IntegrationCenter,
    contains_secrets,
    sanitize_config,
)


def test_managed_ownership():
    result = IntegrationCenter.validate_mode(
        "managed",
        {},
    )

    assert set(result.values()) == {
        "managed"
    }


def test_connected_ownership():
    result = IntegrationCenter.validate_mode(
        "connected",
        {},
    )

    assert set(result.values()) == {
        "connected"
    }


def test_hybrid_requires_explicit_domains():
    with pytest.raises(ValueError):
        IntegrationCenter.validate_mode(
            "hybrid",
            {
                "doctors": "connected",
            },
        )


def test_hybrid_explicit_ownership():
    result = IntegrationCenter.validate_mode(
        "hybrid",
        {
            "doctors": "connected",
            "schedules": "connected",
            "appointments": "managed",
        },
    )

    assert (
        result["appointments"]
        == "managed"
    )


def test_secret_redaction():
    config = {
        "url": "example",
        "api_token": "secret-value",
        "nested": {
            "password": "hidden",
        },
    }

    safe = sanitize_config(
        config
    )

    assert safe["url"] == "example"
    assert safe["api_token"] == "***"
    assert (
        safe["nested"]["password"]
        == "***"
    )
    assert contains_secrets(config)


@pytest.mark.asyncio
async def test_managed_health():
    integration = SimpleNamespace(
        source_mode="managed",
        provider="medibook",
    )

    adapter = (
        IntegrationCenter.adapter(
            integration
        )
    )

    result = await adapter.health()

    assert (
        result["status"]
        == "connected"
    )


@pytest.mark.asyncio
async def test_external_not_faked():
    integration = SimpleNamespace(
        source_mode="connected",
        provider="example-hms",
    )

    adapter = (
        IntegrationCenter.adapter(
            integration
        )
    )

    result = await adapter.health()

    assert (
        result["status"]
        == "degraded"
    )


def test_routes_registered():
    from app.main import app

    paths = app.openapi()["paths"]

    assert (
        "/api/v1/hospital-operations/{hospital_slug}/integrations"
        in paths
    )

    assert (
        "/api/v1/hospital-operations/{hospital_slug}/audit"
        in paths
    )

    assert (
        "/api/v1/hospital-operations/{hospital_slug}/staff"
        in paths
    )

    assert (
        "/api/v1/hospital-operations/{hospital_slug}/settings"
        in paths
    )

    assert (
        "/api/v1/platform-control/summary"
        in paths
    )
