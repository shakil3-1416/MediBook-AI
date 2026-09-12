from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dashboard_auth import (
    dashboard_user,
)
from app.core.database import get_db
from app.models import Doctor
from app.models.hospital import (
    Hospital,
    HospitalDoctor,
    HospitalMembership,
)
from app.schemas.workspace import (
    HospitalDoctorSummary,
    PlatformHospitalSummary,
    WorkspaceSummary,
)
from app.services.tenant_authorization import (
    HospitalNotFound,
    TenantAccessDenied,
    require_hospital_access,
    require_platform_admin_role,
)

router = APIRouter(
    tags=["workspaces"],
)


@router.get(
    "/platform/hospitals",
    response_model=list[
        PlatformHospitalSummary
    ],
)
async def platform_hospitals(
    current_user=Depends(
        dashboard_user
    ),
    session: AsyncSession=Depends(
        get_db
    ),
):

    try:
        require_platform_admin_role(
            current_user
        )

    except TenantAccessDenied as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    hospitals = await session.scalars(
        select(Hospital)
        .order_by(
            Hospital.name
        )
    )

    return list(
        hospitals.all()
    )


@router.get(
    "/hospital/workspaces",
    response_model=list[
        WorkspaceSummary
    ],
)
async def my_hospital_workspaces(
    current_user=Depends(
        dashboard_user
    ),
    session: AsyncSession=Depends(
        get_db
    ),
):

    rows = (
        await session.execute(
            select(
                Hospital,
                HospitalMembership.role,
            )
            .join(
                HospitalMembership,
                HospitalMembership.hospital_id
                == Hospital.id,
            )
            .where(
                HospitalMembership.user_id
                == current_user.id,
                HospitalMembership.is_active
                .is_(True),
                Hospital.is_active
                .is_(True),
            )
            .order_by(
                Hospital.name
            )
        )
    ).all()

    return [
        WorkspaceSummary(
            id=hospital.id,
            slug=hospital.slug,
            name=hospital.name,
            status=hospital.status,
            timezone=hospital.timezone,
            role=role,
        )
        for hospital, role
        in rows
    ]


@router.get(
    "/hospital/{hospital_id}/doctors",
    response_model=list[
        HospitalDoctorSummary
    ],
)
async def hospital_doctors(
    hospital_id: uuid.UUID,
    current_user=Depends(
        dashboard_user
    ),
    session: AsyncSession=Depends(
        get_db
    ),
):

    try:

        await require_hospital_access(
            session,
            user_id=current_user.id,
            hospital_id=hospital_id,
        )

    except HospitalNotFound as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except TenantAccessDenied as exc:

        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    doctors = await session.scalars(
        select(Doctor)
        .join(
            HospitalDoctor,
            HospitalDoctor.doctor_id
            == Doctor.id,
        )
        .where(
            HospitalDoctor.hospital_id
            == hospital_id
        )
        .order_by(
            Doctor.full_name
        )
    )

    return [
        HospitalDoctorSummary(
            id=doctor.id,
            full_name=doctor.full_name,
            gender=doctor.gender,
            qualification=doctor.qualification,
            experience_years=doctor.experience_years,
            clinic_name=doctor.clinic_name,
            clinic_location=doctor.clinic_location,
            consultation_fee=float(
                doctor.consultation_fee
            ),
            is_active=doctor.is_active,
        )
        for doctor
        in doctors.all()
    ]
