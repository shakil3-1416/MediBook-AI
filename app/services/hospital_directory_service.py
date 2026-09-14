from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Doctor,
    DoctorSlot,
)
from app.models.hospital import HospitalDoctor
from app.services.hospital_doctor_access import (
    require_active_hospital_doctor,
)


class HospitalDirectoryService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def list_doctors(
        self,
        *,
        hospital_id: uuid.UUID,
        specialty: str | None = None,
        gender: str | None = None,
        location: str | None = None,
        limit: int = 500,
    ) -> list[Doctor]:

        query = (
            select(Doctor)
            .join(
                HospitalDoctor,
                HospitalDoctor.doctor_id
                == Doctor.id,
            )
            .options(
                selectinload(
                    Doctor.specialty
                )
            )
            .where(
                HospitalDoctor.hospital_id
                == hospital_id,
                HospitalDoctor.is_active.is_(True),
                Doctor.is_active.is_(True),
            )
        )

        if specialty:
            query = query.where(
                Doctor.specialty.has(
                    name=specialty
                )
            )

        if gender:
            query = query.where(
                Doctor.gender
                == gender.lower()
            )

        if location:
            query = query.where(
                Doctor.clinic_location
                .ilike(
                    f"%{location}%"
                )
            )

        query = (
            query
            .order_by(
                Doctor.full_name
            )
            .limit(limit)
        )

        result = await self.session.scalars(
            query
        )

        return list(
            result.unique().all()
        )

    async def doctor(
        self,
        *,
        hospital_id: uuid.UUID,
        doctor_id: uuid.UUID,
    ) -> Doctor | None:

        await require_active_hospital_doctor(
            self.session,
            hospital_id=hospital_id,
            doctor_id=doctor_id,
        )

        return await self.session.scalar(
            select(Doctor)
            .options(
                selectinload(
                    Doctor.specialty
                )
            )
            .where(
                Doctor.id == doctor_id,
                Doctor.is_active.is_(True),
            )
        )

    async def availability(
        self,
        *,
        hospital_id: uuid.UUID,
        doctor_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[DoctorSlot]:

        await require_active_hospital_doctor(
            self.session,
            hospital_id=hospital_id,
            doctor_id=doctor_id,
        )

        result = await self.session.scalars(
            select(DoctorSlot)
            .where(
                DoctorSlot.doctor_id
                == doctor_id,
                DoctorSlot.slot_date
                >= start_date,
                DoctorSlot.slot_date
                <= end_date,
                DoctorSlot.is_enabled.is_(True),
                DoctorSlot.is_available
                .is_(True),
            )
            .order_by(
                DoctorSlot.slot_date,
                DoctorSlot.start_time,
            )
        )

        return list(
            result.all()
        )
