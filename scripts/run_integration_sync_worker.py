from __future__ import annotations

import argparse
import asyncio
import inspect
import os
import signal
import socket
import sys
import time

import logging

from app.core.observability import (
    configure_observability_logging,
    log_event,
)
from app.services.worker_health import (
    publish_worker_heartbeat,
)

import app.core.database as database

from app.services.integration_sync_runtime import (
    IntegrationSyncRuntime,
)


logger = logging.getLogger(
    "medibook.integration_worker"
)


STOP = False


def request_stop(
    signum,
    frame,
):
    del signum
    del frame

    global STOP

    STOP = True


async def acquire():
    for name in (
        "get_db_session",
        "get_db",
    ):
        fn = getattr(
            database,
            name,
            None,
        )

        if (
            fn
            and inspect.isasyncgenfunction(
                fn
            )
        ):
            gen = fn()

            return (
                await anext(
                    gen
                ),
                gen,
            )

    raise RuntimeError(
        "Database dependency unavailable."
    )


async def one_iteration(
    *,
    worker_id: str,
    stale_seconds: int,
):
    session, gen = await acquire()

    try:
        runtime = IntegrationSyncRuntime(
            session
        )

        recovered = (
            await runtime.recover_stale(
                stale_seconds=
                    stale_seconds
            )
        )

        run = await runtime.run_next(
            claimed_by=
                worker_id
        )

        return (
            recovered,
            run,
        )

    finally:
        await gen.aclose()


async def main():
    configure_observability_logging()
    parser = argparse.ArgumentParser(
        description=(
            "MediBook durable integration "
            "sync worker"
        )
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help=(
            "Process at most one due job "
            "and exit."
        ),
    )

    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=2.0,
    )

    parser.add_argument(
        "--stale-seconds",
        type=int,
        default=300,
    )

    args = parser.parse_args()


    worker_id = (
        os.getenv(
            "MEDIBOOK_SYNC_WORKER_ID"
        )
        or
        f"{socket.gethostname()}:{os.getpid()}"
    )[:120]


    signal.signal(
        signal.SIGTERM,
        request_stop,
    )

    signal.signal(
        signal.SIGINT,
        request_stop,
    )


    log_event(
        logger,
        logging.INFO,
        "integration.worker.started",
        worker_id=
            worker_id,
    )

    await publish_worker_heartbeat(
        worker_id=
            worker_id,

        state="idle",
    )


    while not STOP:
        recovered, run = (
            await one_iteration(
                worker_id=
                    worker_id,

                stale_seconds=
                    args.stale_seconds,
            )
        )


        if recovered:
            log_event(
                logger,
                logging.WARNING,
                "integration.worker.stale_recovered",
                worker_id=
                    worker_id,

                count=
                    recovered,
            )


        if run is not None:
            log_event(
                logger,
                logging.INFO,
                "integration.worker.run_completed",
                worker_id=
                    worker_id,

                run_id=str(
                    run[
                        "id"
                    ]
                ),

                run_status=str(
                    run[
                        "status"
                    ]
                ),
            )


        await publish_worker_heartbeat(
            worker_id=
                worker_id,

            state=(
                "processed"
                if run is not None
                else "idle"
            ),

            last_run_id=(
                str(
                    run[
                        "id"
                    ]
                )
                if run is not None
                else None
            ),

            last_run_status=(
                str(
                    run[
                        "status"
                    ]
                )
                if run is not None
                else None
            ),
        )


        if args.once:
            return


        if run is None:
            await asyncio.sleep(
                max(
                    0.25,
                    args.poll_seconds,
                )
            )


if __name__ == "__main__":
    asyncio.run(
        main()
    )
