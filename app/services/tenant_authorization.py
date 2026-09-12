from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import (
    HOSPITAL_ADMIN,
    HOSPITAL_ROLES,
    PLATFORM_ADMIN,
)
from app.models.hospital import (
    Hospital,
    HospitalMembership,
)


class TenantAccessDenied(Exception):
    pass


class HospitalNotFound(Exception):
    pass


async def get_active_hospital(
    session: AsyncSession,
    hospital_id: uuid.UUID,
) -> Hospital:

    hospital = await session.scalar(
        select(Hospital)
        .where(
            Hospital.id
            == hospital_id,
            Hospital.is_active
            .is_(True),
        )
    )

    if hospital is None:
        raise HospitalNotFound(
            "Hospital not found."
        )

    return hospital


async def get_membership(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    hospital_id: uuid.UUID,
) -> HospitalMembership | None:

    return await session.scalar(
        select(HospitalMembership)
        .where(
            HospitalMembership.user_id
            == user_id,
            HospitalMembership.hospital_id
            == hospital_id,
            HospitalMembership.is_active
            .is_(True),
        )
    )


async def require_hospital_access(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    hospital_id: uuid.UUID,
) -> HospitalMembership:

    await get_active_hospital(
        session,
        hospital_id,
    )

    membership = await get_membership(
        session,
        user_id=user_id,
        hospital_id=hospital_id,
    )

    if membership is None:
        raise TenantAccessDenied(
            "You do not have access "
            "to this hospital."
        )

    if membership.role not in HOSPITAL_ROLES:
        raise TenantAccessDenied(
            "Invalid hospital role."
        )

    return membership


async def require_hospital_admin(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    hospital_id: uuid.UUID,
) -> HospitalMembership:

    membership = (
        await require_hospital_access(
            session,
            user_id=user_id,
            hospital_id=hospital_id,
        )
    )

    if membership.role != HOSPITAL_ADMIN:
        raise TenantAccessDenied(
            "Hospital administrator access required."
        )

    return membership


def require_platform_admin_role(
    user,
) -> None:

    if (
        getattr(
            user,
            "role",
            None,
        )
        != PLATFORM_ADMIN
    ):
        raise TenantAccessDenied(
            "Platform administrator access required."
        )
