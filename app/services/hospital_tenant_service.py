from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hospital import (
    Hospital,
    HospitalDoctor,
)

DEFAULT_HOSPITAL_ID = uuid.UUID(
    "00000000-0000-0000-0000-000000000001"
)


async def get_hospital(
    session: AsyncSession,
    hospital_id: uuid.UUID,
):
    return await session.scalar(
        select(Hospital).where(
            Hospital.id == hospital_id,
            Hospital.is_active.is_(True),
        )
    )


async def hospital_doctor_ids(
    session: AsyncSession,
    hospital_id: uuid.UUID,
):
    result = await session.scalars(
        select(
            HospitalDoctor.doctor_id
        ).where(
            HospitalDoctor.hospital_id
            == hospital_id
        )
    )

    return list(result.all())
