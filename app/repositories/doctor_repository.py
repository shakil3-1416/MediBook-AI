from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.doctor import Doctor, Specialty


class DoctorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search(
        self,
        *,
        specialty: str | None = None,
        location: str | None = None,
        gender: str | None = None,
        max_fee: Decimal | None = None,
        name: str | None = None,
    ) -> list[Doctor]:

        statement = (
            select(Doctor)
            .join(Doctor.specialty)
            .options(selectinload(Doctor.specialty))
            .where(Doctor.is_active.is_(True))
        )

        if specialty:
            statement = statement.where(
                func.lower(Specialty.name).contains(
                    specialty.lower()
                )
            )

        if location:
            statement = statement.where(
                func.lower(Doctor.clinic_location).contains(
                    location.lower()
                )
            )

        if gender:
            statement = statement.where(
                func.lower(Doctor.gender) == gender.lower()
            )

        if max_fee is not None:
            statement = statement.where(
                Doctor.consultation_fee <= max_fee
            )

        if name:
            statement = statement.where(
                func.lower(Doctor.full_name).contains(
                    name.lower()
                )
            )

        statement = statement.order_by(
            Doctor.full_name.asc()
        )

        result = await self.session.execute(statement)

        return list(
            result.scalars().unique().all()
        )

    async def get_by_id(
        self,
        doctor_id: UUID,
    ) -> Doctor | None:

        statement = (
            select(Doctor)
            .options(selectinload(Doctor.specialty))
            .where(
                Doctor.id == doctor_id,
                Doctor.is_active.is_(True),
            )
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def find_by_name(
        self,
        name: str,
    ) -> list[Doctor]:

        statement = (
            select(Doctor)
            .options(selectinload(Doctor.specialty))
            .where(
                Doctor.is_active.is_(True),
                func.lower(Doctor.full_name).contains(
                    name.lower()
                ),
            )
            .order_by(Doctor.full_name.asc())
        )

        result = await self.session.execute(statement)

        return list(
            result.scalars().unique().all()
        )
