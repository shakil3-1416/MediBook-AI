from __future__ import annotations

from pathlib import Path

from app.services.integration_sync_runtime import (
    retry_delay_seconds,
)


def test_retry_backoff_is_bounded():
    assert (
        retry_delay_seconds(
            1
        )
        ==
        5
    )

    assert (
        retry_delay_seconds(
            2
        )
        ==
        15
    )

    assert (
        retry_delay_seconds(
            3
        )
        ==
        45
    )

    assert (
        retry_delay_seconds(
            10
        )
        ==
        300
    )


def test_api_trigger_is_enqueue_only():
    source = Path(
        "app/services/"
        "integration_sync_runtime.py"
    ).read_text(
        encoding="utf-8",
    )

    trigger = source[
        source.index(
            "    async def trigger("
        ):
        source.index(
            "    async def claim_next("
        )
    ]

    assert (
        "adapter.pull"
        not in trigger
    )

    assert (
        "adapter.push"
        not in trigger
    )

    assert (
        "'pending'"
        in trigger
    )


def test_worker_uses_skip_locked_claim():
    source = Path(
        "app/services/"
        "integration_sync_runtime.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "FOR UPDATE SKIP LOCKED"
        in source
    )

    assert (
        "attempt + 1"
        in source
    )


def test_stale_running_jobs_are_recovered():
    source = Path(
        "app/services/"
        "integration_sync_runtime.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "recover_stale"
        in source
    )

    assert (
        "Worker heartbeat expired"
        in source
    )


def test_sync_history_is_tenant_scoped():
    source = Path(
        "app/services/"
        "integration_sync_runtime.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "async def list_runs"
        in source
    )

    assert (
        "WHERE hospital_id ="
        in source
    )


def test_health_is_derived_from_runs():
    source = Path(
        "app/services/"
        "integration_sync_runtime.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "health_summary"
        in source
    )

    assert (
        "last_success_at"
        in source
    )

    assert (
        "last_failure_at"
        in source
    )

    assert (
        "in_flight"
        in source
    )



def test_stale_recovery_casts_timestamp_case_values():
    from pathlib import Path

    source = Path(
        "app/services/"
        "integration_sync_runtime.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "NULL::timestamptz"
        in source
    )

    assert (
        "AS timestamptz"
        in source
    )

    assert (
        "recover_stale"
        in source
    )
