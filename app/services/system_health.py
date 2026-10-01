from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)
import time
from typing import Any

from sqlalchemy import text

from app.core.database import (
    AsyncSessionFactory,
)

from app.core.observability import (
    request_metrics,
)

from app.core.redis import (
    redis_client,
)

from app.services.worker_health import (
    worker_health_snapshot,
)


def utcnow_iso() -> str:
    return (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )


async def database_health() -> dict[
    str,
    Any,
]:
    started = (
        time.perf_counter()
    )


    try:
        async with (
            AsyncSessionFactory()
        ) as session:
            await session.execute(
                text(
                    "SELECT 1"
                )
            )


        latency_ms = (
            time.perf_counter()
            -
            started
        ) * 1000.0


        return {
            "healthy":
                True,

            "latency_ms":
                round(
                    latency_ms,
                    2,
                ),
        }


    except Exception as exc:
        return {
            "healthy":
                False,

            "error_type":
                exc.__class__.__name__,
        }


async def redis_health() -> dict[
    str,
    Any,
]:
    started = (
        time.perf_counter()
    )


    try:
        healthy = bool(
            await redis_client.ping()
        )


        latency_ms = (
            time.perf_counter()
            -
            started
        ) * 1000.0


        return {
            "healthy":
                healthy,

            "latency_ms":
                round(
                    latency_ms,
                    2,
                ),
        }


    except Exception as exc:
        return {
            "healthy":
                False,

            "error_type":
                exc.__class__.__name__,
        }


async def integration_runtime_metrics() -> dict[
    str,
    Any,
]:
    async with (
        AsyncSessionFactory()
    ) as session:
        result = await session.execute(
            text(
                """
                SELECT
                    COUNT(*) AS total,

                    COUNT(*) FILTER
                    (
                        WHERE status =
                              'pending'
                    )
                    AS pending,

                    COUNT(*) FILTER
                    (
                        WHERE status =
                              'running'
                    )
                    AS running,

                    COUNT(*) FILTER
                    (
                        WHERE status =
                              'retry'
                    )
                    AS retry,

                    COUNT(*) FILTER
                    (
                        WHERE status =
                              'succeeded'
                    )
                    AS succeeded,

                    COUNT(*) FILTER
                    (
                        WHERE status =
                              'failed'
                    )
                    AS failed,

                    COUNT(*) FILTER
                    (
                        WHERE status =
                              'blocked'
                    )
                    AS blocked,

                    COUNT(*) FILTER
                    (
                        WHERE status =
                              'running'
                          AND
                            (
                                heartbeat_at IS NULL
                                OR heartbeat_at
                                   <
                                   now()
                                   -
                                   interval '5 minutes'
                            )
                    )
                    AS stale_running

                FROM integration_sync_runs
                """
            )
        )


        row = (
            result.mappings()
            .one()
        )


    return {
        key:
            int(
                row[
                    key
                ]
                or 0
            )
        for key
        in (
            "total",
            "pending",
            "running",
            "retry",
            "succeeded",
            "failed",
            "blocked",
            "stale_running",
        )
    }


async def copilot_runtime_metrics() -> dict[str, Any]:
    async with AsyncSessionFactory() as session:
        proposal_cols = await session.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='hospital_copilot_proposals'
                """
            )
        )

        proposal_columns = {str(row[0]) for row in proposal_cols.all()}

        proposals = {
            "total": 0,
            "pending": 0,
            "confirmed": 0,
            "executed": 0,
            "failed": 0,
        }

        if proposal_columns:
            if "status" in proposal_columns:
                rows = await session.execute(
                    text(
                        """
                        SELECT CAST(status AS TEXT), COUNT(*)
                        FROM hospital_copilot_proposals
                        GROUP BY status
                        """
                    )
                )

                for raw_status, count in rows.all():
                    status = str(raw_status or "").strip().lower()
                    amount = int(count or 0)

                    proposals["total"] += amount

                    if status == "pending":
                        proposals["pending"] += amount
                    elif status == "confirmed":
                        proposals["confirmed"] += amount
                    elif status == "executed":
                        proposals["executed"] += amount
                    elif "fail" in status or "error" in status:
                        proposals["failed"] += amount
            else:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM hospital_copilot_proposals")
                )
                proposals["total"] = int(result.scalar_one() or 0)

        event_cols = await session.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='hospital_copilot_events'
                """
            )
        )

        event_columns = {str(row[0]) for row in event_cols.all()}

        events = {
            "total": 0,
            "failure_events": 0,
        }

        if event_columns:
            event_type_column = next(
                (
                    name
                    for name in ("event_type", "action", "event_name", "type")
                    if name in event_columns
                ),
                None,
            )

            if event_type_column:
                result = await session.execute(
                    text(
                        f"""
                        SELECT
                            COUNT(*) AS total,
                            COUNT(*) FILTER (
                                WHERE CAST("{event_type_column}" AS TEXT) ILIKE '%fail%'
                                   OR CAST("{event_type_column}" AS TEXT) ILIKE '%error%'
                            ) AS failures
                        FROM hospital_copilot_events
                        """
                    )
                )

                row = result.mappings().one()

                events["total"] = int(row["total"] or 0)
                events["failure_events"] = int(row["failures"] or 0)

            else:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM hospital_copilot_events")
                )
                events["total"] = int(result.scalar_one() or 0)

        return {
            "proposals": proposals,
            "events": events,
        }


async def system_health_snapshot() -> dict[
    str,
    Any,
]:
    database = await database_health()

    redis = await redis_health()


    try:
        worker = (
            await worker_health_snapshot()
        )

    except Exception as exc:
        worker = {
            "healthy":
                False,

            "active_workers":
                0,

            "workers":
                [],

            "error_type":
                exc.__class__.__name__,
        }


    try:
        integration = (
            await integration_runtime_metrics()
        )

    except Exception as exc:
        integration = {
            "error_type":
                exc.__class__.__name__,
        }


    try:
        copilot = (
            await copilot_runtime_metrics()
        )

    except Exception as exc:
        copilot = {
            "error_type":
                exc.__class__.__name__,
        }


    ready = bool(
        database.get(
            "healthy"
        )
        and redis.get(
            "healthy"
        )
    )


    return {
        "timestamp":
            utcnow_iso(),

        "status":
            (
                "healthy"
                if ready
                else "degraded"
            ),

        "ready":
            ready,

        "dependencies": {
            "database":
                database,

            "redis":
                redis,
        },

        "workers": {
            "integration_sync":
                worker,
        },

        "integration_runtime":
            integration,

        "copilot":
            copilot,

        "http":
            request_metrics.snapshot(
                window_seconds=300
            ),
    }
