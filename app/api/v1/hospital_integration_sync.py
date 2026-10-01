from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.api.v1.dashboard_auth import (
    dashboard_user,
)

from app.core.database import (
    get_db,
)

from app.schemas.integration_sync import (
    IntegrationSyncRunView,
    IntegrationSyncTrigger,
)

from app.services.integration_sync_runtime import (
    IntegrationSyncRuntime,
    IntegrationSyncRuntimeError,
)

from app.services.tenant_authorization import (
    require_hospital_admin,
)


router = APIRouter(
    prefix=(
        "/hospital-operations/"
        "{hospital_slug}/integrations"
    ),
    tags=[
        "hospital-integration-sync"
    ],
)


async def _hospital_admin(
    hospital_slug: str,
    current_user,
    session: AsyncSession,
):
    return await require_hospital_admin(
        session,
        current_user,
        hospital_slug,
    )


def _view(
    row,
) -> IntegrationSyncRunView:
    return IntegrationSyncRunView(
        id=str(
            row[
                "id"
            ]
        ),

        hospital_id=str(
            row[
                "hospital_id"
            ]
        ),

        integration_id=str(
            row[
                "integration_id"
            ]
        ),

        provider=str(
            row[
                "provider"
            ]
        ),

        resource=str(
            row[
                "resource"
            ]
        ),

        direction=row[
            "direction"
        ],

        status=row[
            "status"
        ],

        idempotency_key=str(
            row[
                "idempotency_key"
            ]
        ),

        attempt=int(
            row[
                "attempt"
            ]
        ),

        max_attempts=int(
            row.get(
                "max_attempts"
            )
            or 3
        ),

        next_attempt_at=(
            str(
                row[
                    "next_attempt_at"
                ]
            )
            if row.get(
                "next_attempt_at"
            )
            else None
        ),

        heartbeat_at=(
            str(
                row[
                    "heartbeat_at"
                ]
            )
            if row.get(
                "heartbeat_at"
            )
            else None
        ),

        claimed_by=(
            str(
                row[
                    "claimed_by"
                ]
            )
            if row.get(
                "claimed_by"
            )
            else None
        ),

        records_seen=int(
            row.get(
                "records_seen"
            )
            or 0
        ),

        records_changed=int(
            row.get(
                "records_changed"
            )
            or 0
        ),

        last_error=(
            str(
                row[
                    "last_error"
                ]
            )
            if row.get(
                "last_error"
            )
            else None
        ),

        created_at=str(
            row[
                "created_at"
            ]
        ),

        started_at=(
            str(
                row[
                    "started_at"
                ]
            )
            if row.get(
                "started_at"
            )
            else None
        ),

        completed_at=(
            str(
                row[
                    "completed_at"
                ]
            )
            if row.get(
                "completed_at"
            )
            else None
        ),

        result=(
            row.get(
                "result"
            )
            or {}
        ),
    )


@router.post(
    "/{integration_id}/sync",
    response_model=
        IntegrationSyncRunView,
)
async def trigger_integration_sync(
    hospital_slug: str,
    integration_id: UUID,
    payload:
        IntegrationSyncTrigger,
    current_user=Depends(
        dashboard_user
    ),
    session: Annotated[
        AsyncSession,
        Depends(
            get_db
        ),
    ] = None,
):
    hospital = await _hospital_admin(
        hospital_slug,
        current_user,
        session,
    )


    runtime = IntegrationSyncRuntime(
        session
    )


    try:
        row = await runtime.trigger(
            hospital_id=str(
                hospital.id
            ),

            integration_id=str(
                integration_id
            ),

            direction=
                payload.direction,

            resource=
                payload.resource,

            idempotency_key=
                payload.idempotency_key,
        )

    except IntegrationSyncRuntimeError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(
                exc
            ),
        ) from exc


    return _view(
        row
    )


@router.get(
    "/sync-runs/{run_id}",
    response_model=
        IntegrationSyncRunView,
)
async def get_integration_sync_run(
    hospital_slug: str,
    run_id: str,
    current_user=Depends(
        dashboard_user
    ),
    session: Annotated[
        AsyncSession,
        Depends(
            get_db
        ),
    ] = None,
):
    hospital = await _hospital_admin(
        hospital_slug,
        current_user,
        session,
    )


    runtime = IntegrationSyncRuntime(
        session
    )


    row = await runtime.get_run(
        hospital_id=str(
            hospital.id
        ),

        run_id=
            run_id,
    )


    if row is None:
        raise HTTPException(
            status_code=404,
            detail=
                "Sync run not found.",
        )


    return _view(
        row
    )


@router.get(
    "/{integration_id}/sync-runs",
    response_model=
        list[
            IntegrationSyncRunView
        ],
)
async def list_integration_sync_runs(
    hospital_slug: str,
    integration_id: UUID,
    limit: int = 50,
    current_user=Depends(
        dashboard_user
    ),
    session: Annotated[
        AsyncSession,
        Depends(
            get_db
        ),
    ] = None,
):
    hospital = await _hospital_admin(
        hospital_slug,
        current_user,
        session,
    )

    runtime = IntegrationSyncRuntime(
        session
    )

    rows = await runtime.list_runs(
        hospital_id=str(
            hospital.id
        ),

        integration_id=str(
            integration_id
        ),

        limit=limit,
    )

    return [
        _view(
            row
        )
        for row
        in rows
    ]


@router.get(
    "/{integration_id}/sync-health",
)
async def integration_sync_health(
    hospital_slug: str,
    integration_id: UUID,
    current_user=Depends(
        dashboard_user
    ),
    session: Annotated[
        AsyncSession,
        Depends(
            get_db
        ),
    ] = None,
):
    hospital = await _hospital_admin(
        hospital_slug,
        current_user,
        session,
    )

    runtime = IntegrationSyncRuntime(
        session
    )

    try:
        return await runtime.health_summary(
            hospital_id=str(
                hospital.id
            ),

            integration_id=str(
                integration_id
            ),
        )

    except IntegrationSyncRuntimeError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(
                exc
            ),
        ) from exc


@router.get(
    "/{integration_id}/contract",
)
async def integration_contract(
    hospital_slug: str,
    integration_id: UUID,
    current_user=Depends(
        dashboard_user
    ),
    session: Annotated[
        AsyncSession,
        Depends(
            get_db
        ),
    ] = None,
):
    from app.models.hospital import (
        HospitalIntegration,
    )

    from app.services.integration_contract_validation import (
        validate_integration_contract,
    )

    from app.services.integration_ownership import (
        SUPPORTED_SYNC_RESOURCES,
    )


    hospital = await _hospital_admin(
        hospital_slug,
        current_user,
        session,
    )


    integration = await session.get(
        HospitalIntegration,
        integration_id,
    )


    if integration is None:
        raise HTTPException(
            status_code=404,
            detail=
                "Integration not found.",
        )


    if str(
        integration.hospital_id
    ) != str(
        hospital.id
    ):
        raise HTTPException(
            status_code=404,
            detail=
                "Integration not found.",
        )


    validation = (
        validate_integration_contract(
            source_mode=
                integration.source_mode,

            provider=
                integration.provider,

            ownership=
                integration.ownership
                or {},
        )
    )


    contract = (
        validation.provider_contract
    )


    return {
        "source_mode":
            validation.source_mode,

        "ownership":
            validation.ownership,

        "executable":
            validation.executable,

        "supported_resources":
            sorted(
                SUPPORTED_SYNC_RESOURCES
            ),

        "provider": {
            "provider":
                contract.provider,

            "executable":
                contract.executable,

            "supports_pull":
                sorted(
                    contract.supports_pull
                ),

            "supports_push":
                sorted(
                    contract.supports_push
                ),

            "supports_webhooks":
                contract.supports_webhooks,

            "supports_health_check":
                contract.supports_health_check,

            "notes":
                contract.notes,
        },

        "warnings":
            list(
                validation.warnings
            ),
    }
