from __future__ import annotations

from typing import Annotated

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
from app.schemas.platform_control_v2 import (
    PlatformControlHospitalDetail,
    PlatformControlHospitalSummary,
    PlatformControlOverview,
    PlatformHospitalProvisionRequest,
    PlatformHospitalStatusUpdate,
)
from app.services.tenant_authorization import (
    require_platform_admin_role,
)
from app.services.platform_control_v2 import (
    PlatformControlError,
    PlatformControlService,
)


router = APIRouter(
    prefix="/platform-control-v2",
    tags=["platform-control-v2"],
)


def _require_platform_admin(
    current_user,
) -> None:
    require_platform_admin_role(
        current_user
    )


def _service(
    session: AsyncSession,
    current_user,
) -> PlatformControlService:
    _require_platform_admin(
        current_user
    )

    return PlatformControlService(
        session,
        actor_user_id=
            current_user.id,
    )


@router.get(
    "/overview",
    response_model=
        PlatformControlOverview,
)
async def platform_control_overview(
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
    return await _service(
        session,
        current_user,
    ).overview()


@router.get(
    "/hospitals",
    response_model=
        list[
            PlatformControlHospitalSummary
        ],
)
async def platform_control_hospitals(
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
    return await _service(
        session,
        current_user,
    ).list_hospitals()


@router.get(
    "/hospitals/{hospital_slug}",
    response_model=
        PlatformControlHospitalDetail,
)
async def platform_control_hospital_detail(
    hospital_slug: str,
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
    try:
        return await _service(
            session,
            current_user,
        ).detail(
            hospital_slug
        )

    except PlatformControlError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(
                exc
            ),
        ) from exc


@router.post(
    "/hospitals",
    response_model=
        PlatformControlHospitalDetail,
)
async def platform_control_provision_hospital(
    payload:
        PlatformHospitalProvisionRequest,
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
    try:
        return await _service(
            session,
            current_user,
        ).provision(
            payload
        )

    except PlatformControlError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(
                exc
            ),
        ) from exc


@router.patch(
    "/hospitals/{hospital_slug}/status",
    response_model=
        PlatformControlHospitalDetail,
)
async def platform_control_update_status(
    hospital_slug: str,
    payload:
        PlatformHospitalStatusUpdate,
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
    try:
        return await _service(
            session,
            current_user,
        ).update_status(
            hospital_slug,
            payload,
        )

    except PlatformControlError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(
                exc
            ),
        ) from exc
