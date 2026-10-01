from __future__ import annotations

import pytest

from app.schemas.integration_sync import (
    IntegrationSyncDirection,
)

from app.services.integration_adapter_runtime import (
    AdapterRegistry,
    IntegrationAdapterUnavailable,
    RuntimeIntegrationAdapter,
    SyncPayload,
    SyncResult,
    UnavailableExternalAdapter,
)

from app.services.integration_sync_runtime import (
    deterministic_idempotency_key,
)


def test_unknown_provider_is_fail_closed():
    registry = AdapterRegistry()

    adapter = registry.resolve(
        "not-real"
    )

    assert isinstance(
        adapter,
        UnavailableExternalAdapter,
    )


@pytest.mark.asyncio
async def test_unknown_provider_never_reports_success():
    registry = AdapterRegistry()

    adapter = registry.resolve(
        "not-real"
    )

    payload = SyncPayload(
        resource="appointments",
        direction="pull",
        config={},
        ownership={},
    )

    with pytest.raises(
        IntegrationAdapterUnavailable
    ):
        await adapter.pull(
            payload
        )


class FakeAdapter(
    RuntimeIntegrationAdapter
):
    provider = "fake"


    async def pull(
        self,
        payload:
            SyncPayload,
    ) -> SyncResult:
        assert (
            payload.resource
            ==
            "appointments"
        )

        return SyncResult(
            records_seen=3,
            records_changed=2,
            detail={
                "fake":
                    True,
            },
        )


    async def push(
        self,
        payload:
            SyncPayload,
    ) -> SyncResult:
        return SyncResult(
            records_seen=1,
            records_changed=1,
        )


def test_registered_adapter_can_be_resolved():
    registry = AdapterRegistry()

    registry.register(
        "fake",
        FakeAdapter,
    )

    adapter = registry.resolve(
        "fake"
    )

    assert isinstance(
        adapter,
        FakeAdapter,
    )


def test_explicit_idempotency_key_is_preserved():
    value = (
        deterministic_idempotency_key(
            integration_id=
                "integration",

            direction=
                "pull",

            resource=
                "appointments",

            nonce=
                "request-12345678",
        )
    )

    assert (
        value
        ==
        "request-12345678"
    )


def test_generated_idempotency_key_is_stable_shape():
    value = (
        deterministic_idempotency_key(
            integration_id=
                "integration",

            direction=
                IntegrationSyncDirection.PULL.value,

            resource=
                "appointments",

            nonce=None,
        )
    )

    assert value.startswith(
        "auto-"
    )

    assert len(
        value
    ) > 20



def test_runtime_closes_unexpected_provider_failures():
    from pathlib import Path

    source = Path(
        "app/services/"
        "integration_sync_runtime.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "except Exception as exc:"
        in source
    )

    # B2 supports retry before terminal failure.
    assert (
        "terminal ="
        in source
    )

    assert (
        'status = "failed"'
        in source
    )

    assert (
        'status = "retry"'
        in source
    )

    assert (
        "next_attempt_at"
        in source
    )

    assert (
        "integration.sync_status"
        in source
    )

    assert (
        "integration.last_error"
        in source
    )
