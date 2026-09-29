from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dashboard_auth import dashboard_user
from app.core.database import get_db
from app.core.roles import HOSPITAL_ROLES
from app.models.hospital import Hospital, HospitalMembership
from app.models.user import User
from app.schemas.hospital_staff_admin import (
    HospitalStaffAddRequest,
    HospitalStaffMutationResponse,
    HospitalStaffUpdateRequest,
)
from app.services.tenant_authorization import (
    HospitalNotFound,
    TenantAccessDenied,
    require_hospital_admin,
)


router = APIRouter(
    prefix="/hospital-operations",
    tags=["hospital-staff-admin"],
)


async def _hospital_by_slug(
    session: AsyncSession,
    hospital_slug: str,
) -> Hospital:
    hospital = await session.scalar(
        select(Hospital).where(
            Hospital.slug == hospital_slug,
            Hospital.is_active.is_(True),
        )
    )

    if hospital is None:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found.",
        )

    return hospital


async def _require_admin(
    session: AsyncSession,
    *,
    hospital: Hospital,
    current_user,
) -> None:
    try:
        await require_hospital_admin(
            session,
            user_id=current_user.id,
            hospital_id=hospital.id,
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


def _response(
    membership: HospitalMembership,
    user: User,
) -> HospitalStaffMutationResponse:
    return HospitalStaffMutationResponse(
        membership_id=membership.id,
        user_id=user.id,
        email=user.email,
        role=membership.role,
        is_active=membership.is_active,
    )


@router.post(
    "/{hospital_slug}/staff",
    response_model=HospitalStaffMutationResponse,
)
async def add_hospital_staff(
    hospital_slug: str,
    payload: HospitalStaffAddRequest,
    current_user=Depends(dashboard_user),
    session: AsyncSession=Depends(get_db),
):
    hospital = await _hospital_by_slug(
        session,
        hospital_slug,
    )

    await _require_admin(
        session,
        hospital=hospital,
        current_user=current_user,
    )

    if payload.role not in HOSPITAL_ROLES:
        raise HTTPException(
            status_code=422,
            detail="Invalid hospital role.",
        )

    normalized_email = (
        payload.email.strip().lower()
    )

    user = await session.scalar(
        select(User).where(
            User.email == normalized_email
        )
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No existing MediBook user was found "
                "for this email."
            ),
        )

    membership = await session.scalar(
        select(HospitalMembership).where(
            HospitalMembership.hospital_id
            == hospital.id,
            HospitalMembership.user_id
            == user.id,
        )
    )

    if membership is None:
        membership = HospitalMembership(
            hospital_id=hospital.id,
            user_id=user.id,
            role=payload.role,
            is_active=True,
        )

        session.add(
            membership
        )
    else:
        membership.role = payload.role
        membership.is_active = True

    await session.commit()
    await session.refresh(
        membership
    )

    return _response(
        membership,
        user,
    )


@router.patch(
    "/{hospital_slug}/staff/{membership_id}",
    response_model=HospitalStaffMutationResponse,
)
async def update_hospital_staff(
    hospital_slug: str,
    membership_id: uuid.UUID,
    payload: HospitalStaffUpdateRequest,
    current_user=Depends(dashboard_user),
    session: AsyncSession=Depends(get_db),
):
    hospital = await _hospital_by_slug(
        session,
        hospital_slug,
    )

    await _require_admin(
        session,
        hospital=hospital,
        current_user=current_user,
    )

    membership = await session.scalar(
        select(HospitalMembership).where(
            HospitalMembership.id
            == membership_id,
            HospitalMembership.hospital_id
            == hospital.id,
        )
    )

    if membership is None:
        raise HTTPException(
            status_code=404,
            detail="Hospital staff membership not found.",
        )

    if (
        payload.role is not None
        and payload.role not in HOSPITAL_ROLES
    ):
        raise HTTPException(
            status_code=422,
            detail="Invalid hospital role.",
        )

    if payload.role is not None:
        membership.role = payload.role

    if payload.is_active is not None:
        if (
            membership.user_id
            == current_user.id
            and payload.is_active is False
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "You cannot deactivate your own "
                    "active hospital membership."
                ),
            )

        membership.is_active = (
            payload.is_active
        )

    user = await session.get(
        User,
        membership.user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=409,
            detail="Membership user no longer exists.",
        )

    await session.commit()
    await session.refresh(
        membership
    )

    return _response(
        membership,
        user,
    )
