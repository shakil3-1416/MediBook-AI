from __future__ import annotations

from pathlib import Path


def test_platform_system_health_is_protected():
    source = Path(
        "app/api/v1/system_health.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "require_platform_admin_role"
        in source
    )

    assert (
        '"/system-health"'
        in source
    )


def test_system_health_checks_db_and_redis():
    source = Path(
        "app/services/system_health.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "database_health"
        in source
    )

    assert (
        "redis_health"
        in source
    )

    assert (
        "worker_health_snapshot"
        in source
    )


def test_system_health_derives_sync_metrics_from_db():
    source = Path(
        "app/services/system_health.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "integration_sync_runs"
        in source
    )

    assert (
        "stale_running"
        in source
    )


def test_system_health_derives_copilot_metrics():
    source = Path(
        "app/services/system_health.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "hospital_copilot_proposals"
        in source
    )

    assert (
        "hospital_copilot_events"
        in source
    )


def test_worker_uses_redis_heartbeat():
    source = Path(
        "scripts/"
        "run_integration_sync_worker.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "publish_worker_heartbeat"
        in source
    )
