from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.doctor_repository import DoctorRepository
from app.repositories.schedule_repository import ScheduleRepository


class AvailabilityService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.doctors = DoctorRepository(session)
        self.schedules = ScheduleRepository(session)

    async def get_doctor_availability(
        self,
        *,
        doctor_id: UUID,
        slot_date: date,
    ) -> dict:

        doctor = await self.doctors.get_by_id(
            doctor_id
        )

        if doctor is None:
            return {
                "found": False,
                "reason": "doctor_not_found",
            }

        slots = await self.schedules.get_available_slots(
            doctor_id=doctor_id,
            slot_date=slot_date,
        )

        return {
            "found": True,
            "doctor": {
                "id": str(doctor.id),
                "full_name": doctor.full_name,
                "specialty": doctor.specialty.name,
                "clinic_name": doctor.clinic_name,
                "clinic_location": doctor.clinic_location,
                "consultation_fee": float(
                    doctor.consultation_fee
                ),
            },
            "date": slot_date.isoformat(),
            "available_slots": [
                slot.start_time.strftime("%H:%M")
                for slot in slots
            ],
            "count": len(slots),
        }
