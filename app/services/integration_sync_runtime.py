from __future__ import annotations

from app.services.external_adapter_resilience import resilient_adapter_call

from datetime import (
    datetime,
    timedelta,
    timezone,
)
import hashlib
import json
import os
import socket
import uuid
from typing import Any

from sqlalchemy import (
    select,
    text,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.models.hospital import (
    HospitalIntegration,
)

from app.schemas.integration_sync import (
    IntegrationSyncDirection,
)

from app.services.integration_adapter_runtime import (
    SyncPayload,
    registry,
)

from app.services.integration_config_security import (
    prepare_integration_config_for_runtime,
)

from app.services.integration_ownership import (
    IntegrationOwnershipError,
    decide_sync_direction,
)


class IntegrationSyncRuntimeError(
    RuntimeError
):
    pass


DEFAULT_MAX_ATTEMPTS = 3

DEFAULT_STALE_SECONDS = 300

MAX_ERROR_LENGTH = 1000


def utcnow() -> datetime:
    return datetime.now(
        timezone.utc
    )


def worker_identity() -> str:
    return (
        os.getenv(
            "MEDIBOOK_SYNC_WORKER_ID",
            "",
        ).strip()
        or
        f"{socket.gethostname()}:{os.getpid()}"
    )[:120]


def retry_delay_seconds(
    attempt: int,
) -> int:
    """
    Bounded exponential backoff:
      attempt 1 -> 5 sec
      attempt 2 -> 15 sec
      attempt 3 -> 45 sec
      attempt 4+ -> max 300 sec
    """

    normalized = max(
        1,
        int(
            attempt
        ),
    )

    return min(
        300,
        5
        * (
            3
            **
            (
                normalized
                - 1
            )
        ),
    )


def deterministic_idempotency_key(
    *,
    integration_id: str,
    direction: str,
    resource: str,
    nonce: str | None,
) -> str:
    if nonce:
        return nonce

    material = (
        f"{integration_id}:"
        f"{direction}:"
        f"{resource}:"
        f"{utcnow().strftime('%Y%m%d%H')}"
    )

    digest = hashlib.sha256(
        material.encode(
            "utf-8"
        )
    ).hexdigest()

    return (
        "auto-"
        + digest
    )


class IntegrationSyncRuntime:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session


    async def _integration(
        self,
        *,
        hospital_id: str,
        integration_id: str,
    ) -> HospitalIntegration:
        integration = (
            await self.session.get(
                HospitalIntegration,
                integration_id,
            )
        )

        if integration is None:
            raise IntegrationSyncRuntimeError(
                "Integration not found."
            )

        if str(
            integration.hospital_id
        ) != str(
            hospital_id
        ):
            raise IntegrationSyncRuntimeError(
                "Integration does not belong "
                "to this hospital."
            )

        if not integration.is_active:
            raise IntegrationSyncRuntimeError(
                "Integration is inactive."
            )

        return integration


    @staticmethod
    def _direction_allowed(
        integration:
            HospitalIntegration,
        direction:
            IntegrationSyncDirection,
        resource: str,
    ) -> bool:
        try:
            decision = decide_sync_direction(
                source_mode=
                    integration.source_mode,

                ownership=
                    integration.ownership
                    or {},

                resource=
                    resource,

                direction=
                    direction.value,
            )

        except IntegrationOwnershipError:
            return False

        return decision.allowed


    async def _existing_run(
        self,
        *,
        integration_id: str,
        idempotency_key: str,
    ) -> dict[
        str,
        Any,
    ] | None:
        result = await self.session.execute(
            text(
                """
                SELECT *
                FROM integration_sync_runs
                WHERE integration_id =
                      :integration_id
                  AND idempotency_key =
                      :idempotency_key
                LIMIT 1
                """
            ),
            {
                "integration_id":
                    integration_id,

                "idempotency_key":
                    idempotency_key,
            },
        )

        row = (
            result.mappings()
            .first()
        )

        return (
            dict(
                row
            )
            if row
            else None
        )


    async def trigger(
        self,
        *,
        hospital_id: str,
        integration_id: str,
        direction:
            IntegrationSyncDirection,
        resource: str,
        idempotency_key:
            str | None = None,
        max_attempts:
            int = DEFAULT_MAX_ATTEMPTS,
    ) -> dict[
        str,
        Any,
    ]:
        """
        Validate and ENQUEUE only.

        Provider/network work is performed by run_next(),
        never inside the API request.
        """

        integration = (
            await self._integration(
                hospital_id=
                    hospital_id,

                integration_id=
                    integration_id,
            )
        )


        key = (
            deterministic_idempotency_key(
                integration_id=
                    str(
                        integration.id
                    ),

                direction=
                    direction.value,

                resource=
                    resource,

                nonce=
                    idempotency_key,
            )
        )


        existing = (
            await self._existing_run(
                integration_id=
                    str(
                        integration.id
                    ),

                idempotency_key=
                    key,
            )
        )


        if existing is not None:
            return existing


        run_id = str(
            uuid.uuid4()
        )

        now = utcnow()


        if not self._direction_allowed(
            integration,
            direction,
            resource,
        ):
            await self.session.execute(
                text(
                    """
                    INSERT INTO integration_sync_runs
                    (
                        id,
                        hospital_id,
                        integration_id,
                        provider,
                        resource,
                        direction,
                        status,
                        idempotency_key,
                        attempt,
                        max_attempts,
                        last_error,
                        result,
                        created_at,
                        completed_at
                    )
                    VALUES
                    (
                        :id,
                        :hospital_id,
                        :integration_id,
                        :provider,
                        :resource,
                        :direction,
                        'blocked',
                        :idempotency_key,
                        0,
                        :max_attempts,
                        :last_error,
                        CAST(:result AS json),
                        :created_at,
                        :completed_at
                    )
                    """
                ),
                {
                    "id":
                        run_id,

                    "hospital_id":
                        str(
                            hospital_id
                        ),

                    "integration_id":
                        str(
                            integration.id
                        ),

                    "provider":
                        integration.provider,

                    "resource":
                        resource,

                    "direction":
                        direction.value,

                    "idempotency_key":
                        key,

                    "max_attempts":
                        max(
                            1,
                            int(
                                max_attempts
                            ),
                        ),

                    "last_error":
                        (
                            "Sync direction is not permitted "
                            "by source_mode/ownership."
                        ),

                    "result":
                        "{}",

                    "created_at":
                        now,

                    "completed_at":
                        now,
                },
            )

            await self.session.commit()

            return (
                await self._existing_run(
                    integration_id=
                        str(
                            integration.id
                        ),

                    idempotency_key=
                        key,
                )
            )


        await self.session.execute(
            text(
                """
                INSERT INTO integration_sync_runs
                (
                    id,
                    hospital_id,
                    integration_id,
                    provider,
                    resource,
                    direction,
                    status,
                    idempotency_key,
                    attempt,
                    max_attempts,
                    result,
                    created_at,
                    next_attempt_at
                )
                VALUES
                (
                    :id,
                    :hospital_id,
                    :integration_id,
                    :provider,
                    :resource,
                    :direction,
                    'pending',
                    :idempotency_key,
                    0,
                    :max_attempts,
                    CAST(:result AS json),
                    :created_at,
                    :next_attempt_at
                )
                """
            ),
            {
                "id":
                    run_id,

                "hospital_id":
                    str(
                        hospital_id
                    ),

                "integration_id":
                    str(
                        integration.id
                    ),

                "provider":
                    integration.provider,

                "resource":
                    resource,

                "direction":
                    direction.value,

                "idempotency_key":
                    key,

                "max_attempts":
                    max(
                        1,
                        int(
                            max_attempts
                        ),
                    ),

                "result":
                    "{}",

                "created_at":
                    now,

                "next_attempt_at":
                    now,
            },
        )

        integration.sync_status = (
            "pending"
        )

        integration.last_error = None

        await self.session.commit()


        return (
            await self._existing_run(
                integration_id=
                    str(
                        integration.id
                    ),

                idempotency_key=
                    key,
            )
        )


    async def claim_next(
        self,
        *,
        claimed_by:
            str | None = None,
    ) -> dict[
        str,
        Any,
    ] | None:
        """
        Atomically claim one due queued run.

        PostgreSQL SKIP LOCKED allows multiple workers safely.
        """

        worker = (
            claimed_by
            or worker_identity()
        )[:120]

        now = utcnow()


        result = await self.session.execute(
            text(
                """
                WITH candidate AS
                (
                    SELECT id
                    FROM integration_sync_runs
                    WHERE status IN
                        (
                            'pending',
                            'retry'
                        )
                      AND
                        (
                            next_attempt_at IS NULL
                            OR next_attempt_at <= :now
                        )
                    ORDER BY
                        created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE integration_sync_runs r
                SET
                    status = 'running',
                    claimed_by = :claimed_by,
                    heartbeat_at = :now,
                    started_at =
                        COALESCE(
                            started_at,
                            :now
                        ),
                    last_attempt_at = :now,
                    attempt =
                        attempt + 1
                FROM candidate
                WHERE r.id =
                      candidate.id
                RETURNING r.*
                """
            ),
            {
                "claimed_by":
                    worker,

                "now":
                    now,
            },
        )

        row = (
            result.mappings()
            .first()
        )

        await self.session.commit()


        return (
            dict(
                row
            )
            if row
            else None
        )


    async def heartbeat(
        self,
        *,
        run_id: str,
        claimed_by: str,
    ) -> None:
        await self.session.execute(
            text(
                """
                UPDATE integration_sync_runs
                SET heartbeat_at = :now
                WHERE id = :run_id
                  AND claimed_by =
                      :claimed_by
                  AND status =
                      'running'
                """
            ),
            {
                "run_id":
                    run_id,

                "claimed_by":
                    claimed_by,

                "now":
                    utcnow(),
            },
        )

        await self.session.commit()


    async def _integration_for_run(
        self,
        row:
            dict[
                str,
                Any,
            ],
    ) -> HospitalIntegration:
        integration = (
            await self.session.get(
                HospitalIntegration,
                row[
                    "integration_id"
                ],
            )
        )

        if integration is None:
            raise IntegrationSyncRuntimeError(
                "Integration disappeared "
                "before execution."
            )

        if str(
            integration.hospital_id
        ) != str(
            row[
                "hospital_id"
            ]
        ):
            raise IntegrationSyncRuntimeError(
                "Tenant ownership changed "
                "before execution."
            )

        if not integration.is_active:
            raise IntegrationSyncRuntimeError(
                "Integration became inactive "
                "before execution."
            )

        return integration


    async def execute_claimed(
        self,
        row:
            dict[
                str,
                Any,
            ],
    ) -> dict[
        str,
        Any,
    ]:
        run_id = str(
            row[
                "id"
            ]
        )

        integration = None


        try:
            integration = (
                await self._integration_for_run(
                    row
                )
            )


            direction = (
                IntegrationSyncDirection(
                    str(
                        row[
                            "direction"
                        ]
                    )
                )
            )


            if not self._direction_allowed(
                integration,
                direction,
                str(
                    row[
                        "resource"
                    ]
                ),
            ):
                raise IntegrationSyncRuntimeError(
                    "Source-mode/ownership no longer "
                    "permits this sync."
                )


            adapter = registry.resolve(
                integration.provider
            )


            runtime_config = (
                prepare_integration_config_for_runtime(
                    integration.config
                    or {}
                )
            )


            payload = SyncPayload(
                resource=str(
                    row[
                        "resource"
                    ]
                ),

                direction=
                    direction.value,

                config=
                    runtime_config,

                ownership=
                    integration.ownership
                    or {},
            )


            if direction == (
                IntegrationSyncDirection.PULL
            ):
                adapter_result = (
                    await resilient_adapter_call(
                    provider=str(
                        integration.provider
                        or "unknown"
                    ),
                    operation="pull",
                    function=adapter.pull,
                    args=(
                        payload
                    ,),
                )
                )

            else:
                adapter_result = (
                    await resilient_adapter_call(
                    provider=str(
                        integration.provider
                        or "unknown"
                    ),
                    operation="push",
                    function=adapter.push,
                    args=(
                        payload
                    ,),
                )
                )


            await self.session.execute(
                text(
                    """
                    UPDATE integration_sync_runs
                    SET
                        status = 'succeeded',
                        records_seen =
                            :records_seen,
                        records_changed =
                            :records_changed,
                        result =
                            CAST(:result AS json),
                        completed_at =
                            :completed_at,
                        heartbeat_at =
                            :completed_at,
                        next_attempt_at =
                            NULL,
                        last_error =
                            NULL
                    WHERE id = :run_id
                    """
                ),
                {
                    "run_id":
                        run_id,

                    "records_seen":
                        adapter_result.records_seen,

                    "records_changed":
                        adapter_result.records_changed,

                    "result":
                        json.dumps(
                            adapter_result.detail
                            or {},
                            default=str,
                        ),

                    "completed_at":
                        utcnow(),
                },
            )


            integration.sync_status = (
                "healthy"
            )

            integration.last_sync_at = (
                utcnow()
            )

            integration.last_error = None

            integration.last_checked_at = (
                utcnow()
            )

            await self.session.commit()


        except Exception as exc:
            message = (
                str(
                    exc
                )
                or exc.__class__.__name__
            )[
                :MAX_ERROR_LENGTH
            ]


            attempt = int(
                row.get(
                    "attempt"
                )
                or 1
            )

            max_attempts = int(
                row.get(
                    "max_attempts"
                )
                or DEFAULT_MAX_ATTEMPTS
            )


            terminal = (
                attempt
                >=
                max_attempts
            )


            if terminal:
                status = "failed"

                next_attempt_at = None

            else:
                status = "retry"

                next_attempt_at = (
                    utcnow()
                    + timedelta(
                        seconds=
                            retry_delay_seconds(
                                attempt
                            )
                    )
                )


            await self.session.execute(
                text(
                    """
                    UPDATE integration_sync_runs
                    SET
                        status = :status,
                        last_error =
                            :last_error,
                        next_attempt_at =
                            :next_attempt_at,
                        heartbeat_at =
                            :heartbeat_at,
                        completed_at =
                            CASE
                                WHEN :terminal
                                THEN :completed_at
                                ELSE NULL
                            END
                    WHERE id = :run_id
                    """
                ),
                {
                    "run_id":
                        run_id,

                    "status":
                        status,

                    "last_error":
                        message,

                    "next_attempt_at":
                        next_attempt_at,

                    "heartbeat_at":
                        utcnow(),

                    "terminal":
                        terminal,

                    "completed_at":
                        utcnow(),
                },
            )


            if integration is not None:
                integration.sync_status = (
                    "failed"
                    if terminal
                    else "retry"
                )

                integration.last_error = (
                    message
                )

                integration.last_checked_at = (
                    utcnow()
                )


            await self.session.commit()


        return (
            await self.get_run(
                hospital_id=str(
                    row[
                        "hospital_id"
                    ]
                ),

                run_id=
                    run_id,
            )
        )


    async def run_next(
        self,
        *,
        claimed_by:
            str | None = None,
    ) -> dict[
        str,
        Any,
    ] | None:
        row = await self.claim_next(
            claimed_by=
                claimed_by,
        )

        if row is None:
            return None

        return await self.execute_claimed(
            row
        )


    async def recover_stale(
        self,
        *,
        stale_seconds:
            int =
            DEFAULT_STALE_SECONDS,
    ) -> int:
        """
        Requeue running jobs whose worker heartbeat disappeared.
        """

        cutoff = (
            utcnow()
            - timedelta(
                seconds=max(
                    30,
                    int(
                        stale_seconds
                    ),
                )
            )
        )


        result = await self.session.execute(
            text(
                """
                UPDATE integration_sync_runs
                SET
                    status =
                        CASE
                            WHEN attempt >= max_attempts
                            THEN 'failed'
                            ELSE 'retry'
                        END,

                    last_error =
                        CASE
                            WHEN attempt >= max_attempts
                            THEN
                                'Worker heartbeat expired; '
                                'maximum attempts reached.'
                            ELSE
                                'Worker heartbeat expired; '
                                'run requeued.'
                        END,

                    next_attempt_at =
                        CASE
                            WHEN attempt >= max_attempts
                            THEN NULL::timestamptz
                            ELSE CAST(
                                :now
                                AS timestamptz
                            )
                        END,

                    claimed_by = NULL,

                    completed_at =
                        CASE
                            WHEN attempt >= max_attempts
                            THEN CAST(
                                :now
                                AS timestamptz
                            )
                            ELSE NULL::timestamptz
                        END

                WHERE status = 'running'
                  AND
                    (
                        heartbeat_at IS NULL
                        OR heartbeat_at <
                           CAST(
                               :cutoff
                               AS timestamptz
                           )
                    )
                """
            ),
            {
                "now":
                    utcnow(),

                "cutoff":
                    cutoff,
            },
        )


        changed = (
            result.rowcount
            or 0
        )

        await self.session.commit()

        return int(
            changed
        )


    async def get_run(
        self,
        *,
        hospital_id: str,
        run_id: str,
    ) -> dict[
        str,
        Any,
    ] | None:
        result = await self.session.execute(
            text(
                """
                SELECT *
                FROM integration_sync_runs
                WHERE id = :run_id
                  AND hospital_id =
                      :hospital_id
                LIMIT 1
                """
            ),
            {
                "run_id":
                    run_id,

                "hospital_id":
                    hospital_id,
            },
        )

        row = (
            result.mappings()
            .first()
        )

        return (
            dict(
                row
            )
            if row
            else None
        )


    async def list_runs(
        self,
        *,
        hospital_id: str,
        integration_id:
            str | None = None,
        limit: int = 50,
    ) -> list[
        dict[
            str,
            Any,
        ]
    ]:
        bounded = min(
            100,
            max(
                1,
                int(
                    limit
                ),
            ),
        )


        if integration_id:
            sql = """
                SELECT *
                FROM integration_sync_runs
                WHERE hospital_id =
                      :hospital_id
                  AND integration_id =
                      :integration_id
                ORDER BY created_at DESC
                LIMIT :limit
            """

            params = {
                "hospital_id":
                    hospital_id,

                "integration_id":
                    integration_id,

                "limit":
                    bounded,
            }

        else:
            sql = """
                SELECT *
                FROM integration_sync_runs
                WHERE hospital_id =
                      :hospital_id
                ORDER BY created_at DESC
                LIMIT :limit
            """

            params = {
                "hospital_id":
                    hospital_id,

                "limit":
                    bounded,
            }


        result = await self.session.execute(
            text(
                sql
            ),
            params,
        )


        return [
            dict(
                row
            )
            for row
            in result.mappings()
        ]


    async def health_summary(
        self,
        *,
        hospital_id: str,
        integration_id: str,
    ) -> dict[
        str,
        Any,
    ]:
        integration = (
            await self._integration(
                hospital_id=
                    hospital_id,

                integration_id=
                    integration_id,
            )
        )


        result = await self.session.execute(
            text(
                """
                SELECT
                    COUNT(*) AS total_runs,

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
                        WHERE status IN
                              (
                                'pending',
                                'retry',
                                'running'
                              )
                    )
                    AS in_flight,

                    MAX(completed_at)
                        FILTER
                        (
                            WHERE status =
                                  'succeeded'
                        )
                    AS last_success_at,

                    MAX(completed_at)
                        FILTER
                        (
                            WHERE status =
                                  'failed'
                        )
                    AS last_failure_at

                FROM integration_sync_runs
                WHERE hospital_id =
                      :hospital_id
                  AND integration_id =
                      :integration_id
                """
            ),
            {
                "hospital_id":
                    hospital_id,

                "integration_id":
                    integration_id,
            },
        )


        summary = dict(
            result.mappings()
            .one()
        )


        status = str(
            integration.sync_status
            or "unknown"
        )


        return {
            "integration_id":
                str(
                    integration.id
                ),

            "provider":
                integration.provider,

            "source_mode":
                integration.source_mode,

            "sync_status":
                status,

            "last_sync_at":
                integration.last_sync_at,

            "last_error":
                integration.last_error,

            "last_checked_at":
                integration.last_checked_at,

            "total_runs":
                int(
                    summary[
                        "total_runs"
                    ]
                    or 0
                ),

            "succeeded":
                int(
                    summary[
                        "succeeded"
                    ]
                    or 0
                ),

            "failed":
                int(
                    summary[
                        "failed"
                    ]
                    or 0
                ),

            "in_flight":
                int(
                    summary[
                        "in_flight"
                    ]
                    or 0
                ),

            "last_success_at":
                summary[
                    "last_success_at"
                ],

            "last_failure_at":
                summary[
                    "last_failure_at"
                ],
        }
