from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.database import get_db_session
from app.models.hospital import (
    Hospital,
    HospitalDoctor,
    HospitalIntegration,
)


router = APIRouter(
    prefix="/platform-control",
    tags=["platform-control"],
)


PLATFORM_ROLES = {
    "platform_admin",
    "super_admin",
    "admin",
}


def require_platform(
    current_user: CurrentUser,
):
    role = str(
        getattr(
            current_user,
            "role",
            "",
        )
        or ""
    ).lower()

    if role not in PLATFORM_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Platform administrator access required.",
        )


@router.get("/summary")
async def platform_summary(
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    require_platform(
        current_user
    )

    hospitals = list(
        (
            await session.execute(
                select(Hospital)
                .order_by(
                    Hospital.name
                )
            )
        ).scalars().all()
    )

    doctor_counts = dict(
        (
            await session.execute(
                select(
                    HospitalDoctor.hospital_id,
                    func.count(
                        HospitalDoctor.id
                    ),
                )
                .where(
                    HospitalDoctor.is_active.is_(True)
                )
                .group_by(
                    HospitalDoctor.hospital_id
                )
            )
        ).all()
    )

    integration_rows = (
        await session.execute(
            select(
                HospitalIntegration.hospital_id,
                HospitalIntegration.status,
            )
        )
    ).all()

    by_hospital = {}

    for hospital_id, status in integration_rows:
        values = by_hospital.setdefault(
            hospital_id,
            {
                "total": 0,
                "connected": 0,
                "degraded": 0,
                "error": 0,
            },
        )

        values["total"] += 1

        if status in values:
            values[status] += 1

    return {
        "metrics": {
            "hospitals":
                len(hospitals),
            "active_hospitals":
                sum(
                    1
                    for hospital in hospitals
                    if hospital.is_active
                ),
            "integrations":
                len(integration_rows),
            "degraded_integrations":
                sum(
                    1
                    for _, status
                    in integration_rows
                    if status in {
                        "degraded",
                        "error",
                    }
                ),
        },
        "hospitals": [
            {
                "id": hospital.id,
                "slug": hospital.slug,
                "name": hospital.name,
                "status": hospital.status,
                "is_active":
                    hospital.is_active,
                "timezone":
                    hospital.timezone,
                "doctors":
                    doctor_counts.get(
                        hospital.id,
                        0,
                    ),
                "integrations":
                    by_hospital.get(
                        hospital.id,
                        {
                            "total": 0,
                            "connected": 0,
                            "degraded": 0,
                            "error": 0,
                        },
                    ),
            }
            for hospital in hospitals
        ],
    }
