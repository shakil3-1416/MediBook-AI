from sqlalchemy.orm import selectinload
from sqlalchemy import select
from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor import Doctor
from app.repositories.doctor_repository import DoctorRepository


class DoctorService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = DoctorRepository(session)

    async def search_doctors(
        self,
        *,
        specialty: str | None = None,
        location: str | None = None,
        gender: str | None = None,
        max_fee: Decimal | None = None,
        name: str | None = None,
    ) -> list[Doctor]:

        return await self.repository.search(
            specialty=specialty,
            location=location,
            gender=gender,
            max_fee=max_fee,
            name=name,
        )

    async def get_doctor(
        self,
        doctor_id: UUID,
    ):
        """
        Return one active doctor by ID.

        The specialty relationship is eager-loaded so the API
        can serialize DoctorResponse without additional queries.
        """

        doctor = await self.session.scalar(
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

        return doctor

