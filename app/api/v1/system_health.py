from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.api.v1.dashboard_auth import (
    dashboard_user,
)

from app.services.system_health import (
    system_health_snapshot,
)

from app.services.tenant_authorization import (
    TenantAccessDenied,
    require_platform_admin_role,
)


router = APIRouter(
    prefix="/platform-control-v2",
    tags=[
        "platform-system-health",
    ],
)


def _require_platform_admin(
    current_user,
) -> None:
    try:
        require_platform_admin_role(
            current_user
        )

    except TenantAccessDenied as exc:
        raise HTTPException(
            status_code=403,
            detail=
                "Platform administrator access required.",
        ) from exc


@router.get(
    "/system-health",
)
async def platform_system_health(
    current_user=Depends(
        dashboard_user
    ),
):
    _require_platform_admin(
        current_user
    )

    return await system_health_snapshot()
