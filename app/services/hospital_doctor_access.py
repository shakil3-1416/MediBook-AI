from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hospital import HospitalDoctor


async def require_active_hospital_doctor(
    session: AsyncSession,
    *,
    hospital_id: UUID,
    doctor_id: UUID,
) -> HospitalDoctor:
    mapping = await session.scalar(
        select(HospitalDoctor).where(
            HospitalDoctor.hospital_id == hospital_id,
            HospitalDoctor.doctor_id == doctor_id,
            HospitalDoctor.is_active.is_(True),
        )
    )

    if mapping is None:
        raise HTTPException(
            status_code=404,
            detail="Doctor is not active for this hospital.",
        )

    return mapping
