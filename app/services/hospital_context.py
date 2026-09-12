from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hospital import (
    Hospital,
    HospitalDoctor,
)


DEFAULT_HOSPITAL_SLUG = "medibook-demo"


class HospitalContextError(Exception):
    pass


class HospitalDoctorAccessError(Exception):
    pass


async def resolve_hospital(
    session: AsyncSession,
    *,
    hospital_id: uuid.UUID | None = None,
    hospital_slug: str | None = None,
) -> Hospital:
    query = select(Hospital).where(
        Hospital.is_active.is_(True)
    )

    if hospital_id is not None:
        query = query.where(
            Hospital.id == hospital_id
        )
    elif hospital_slug:
        query = query.where(
            Hospital.slug == hospital_slug
        )
    else:
        query = query.where(
            Hospital.slug
            == DEFAULT_HOSPITAL_SLUG
        )

    hospital = await session.scalar(query)

    if hospital is None:
        raise HospitalContextError(
            "Hospital workspace not found."
        )

    return hospital


async def hospital_owns_doctor(
    session: AsyncSession,
    *,
    hospital_id: uuid.UUID,
    doctor_id: uuid.UUID,
) -> bool:
    mapping = await session.scalar(
        select(HospitalDoctor.id).where(
            HospitalDoctor.hospital_id
            == hospital_id,
            HospitalDoctor.doctor_id
            == doctor_id,
        )
    )

    return mapping is not None


async def require_hospital_doctor(
    session: AsyncSession,
    *,
    hospital_id: uuid.UUID,
    doctor_id: uuid.UUID,
) -> None:
    if not await hospital_owns_doctor(
        session,
        hospital_id=hospital_id,
        doctor_id=doctor_id,
    ):
        raise HospitalDoctorAccessError(
            "Doctor does not belong to this hospital."
        )


async def hospital_doctor_ids(
    session: AsyncSession,
    *,
    hospital_id: uuid.UUID,
) -> list[uuid.UUID]:
    result = await session.scalars(
        select(HospitalDoctor.doctor_id)
        .where(
            HospitalDoctor.hospital_id
            == hospital_id
        )
    )

    return list(result.all())
