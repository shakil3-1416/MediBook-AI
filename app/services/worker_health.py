from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)
import json
from typing import Any

from app.core.redis import (
    redis_client,
)


WORKER_KEY_PREFIX = (
    "medibook:worker:integration-sync:"
)

WORKER_INDEX_KEY = (
    "medibook:worker:integration-sync:index"
)

DEFAULT_WORKER_TTL_SECONDS = 30


def utcnow_iso() -> str:
    return (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )


async def publish_worker_heartbeat(
    *,
    worker_id: str,
    ttl_seconds: int =
        DEFAULT_WORKER_TTL_SECONDS,
    state: str = "idle",
    last_run_id:
        str | None = None,
    last_run_status:
        str | None = None,
) -> None:
    payload = {
        "worker_id":
            worker_id,

        "state":
            state,

        "heartbeat_at":
            utcnow_iso(),

        "last_run_id":
            last_run_id,

        "last_run_status":
            last_run_status,
    }


    key = (
        WORKER_KEY_PREFIX
        + worker_id
    )


    async with redis_client.pipeline(
        transaction=True
    ) as pipe:
        await pipe.set(
            key,
            json.dumps(
                payload,
                separators=(
                    ",",
                    ":",
                ),
            ),
            ex=max(
                5,
                int(
                    ttl_seconds
                ),
            ),
        )

        await pipe.sadd(
            WORKER_INDEX_KEY,
            worker_id,
        )

        await pipe.expire(
            WORKER_INDEX_KEY,
            max(
                60,
                int(
                    ttl_seconds
                )
                * 10,
            ),
        )

        await pipe.execute()


async def worker_health_snapshot() -> dict[
    str,
    Any,
]:
    ids = sorted(
        await redis_client.smembers(
            WORKER_INDEX_KEY
        )
        or []
    )


    workers = []

    stale_ids = []


    for worker_id in ids:
        raw = await redis_client.get(
            WORKER_KEY_PREFIX
            + worker_id
        )

        if raw is None:
            stale_ids.append(
                worker_id
            )

            continue


        try:
            payload = json.loads(
                raw
            )

        except Exception:
            payload = {
                "worker_id":
                    worker_id,

                "state":
                    "unknown",

                "heartbeat_at":
                    None,
            }


        workers.append(
            payload
        )


    if stale_ids:
        await redis_client.srem(
            WORKER_INDEX_KEY,
            *stale_ids,
        )


    return {
        "healthy":
            bool(
                workers
            ),

        "active_workers":
            len(
                workers
            ),

        "workers":
            workers,
    }
