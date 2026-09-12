from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import DoctorSlot


class ScheduleRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_available_slots(
        self,
        *,
        doctor_id: UUID,
        slot_date: date,
    ) -> list[DoctorSlot]:

        statement = (
            select(DoctorSlot)
            .where(
                DoctorSlot.doctor_id == doctor_id,
                DoctorSlot.slot_date == slot_date,
                DoctorSlot.is_available.is_(True),
            )
            .order_by(DoctorSlot.start_time.asc())
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())
