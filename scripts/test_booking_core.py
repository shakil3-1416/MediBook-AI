import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionFactory
from app.models.doctor import Doctor
from app.models.schedule import DoctorSlot
from app.services.appointment_service import (
    AppointmentService,
    SlotUnavailableError,
)


async def main() -> None:

    # -----------------------------------------
    # Pick Farhana's first available future slot
    # -----------------------------------------

    async with AsyncSessionFactory() as session:
        slot = await session.scalar(
            select(DoctorSlot)
            .join(
                Doctor,
                Doctor.id
                == DoctorSlot.doctor_id,
            )
            .where(
                Doctor.full_name
                == "Dr. Farhana Ahmed",
                DoctorSlot.is_available
                .is_(True),
            )
            .order_by(
                DoctorSlot.slot_date,
                DoctorSlot.start_time,
            )
            .limit(1)
        )

        if slot is None:
            raise RuntimeError(
                "No future Farhana slot exists."
            )

        slot_id = slot.id

        service = AppointmentService(
            session
        )

        preview = await service.preview_booking(
            slot_id=slot_id
        )

        print("BOOKING PREVIEW:")
        print(preview)

    # -----------------------------------------
    # First booking
    # -----------------------------------------

    async with AsyncSessionFactory() as session:
        service = AppointmentService(
            session
        )

        result = await service.confirm_booking(
            slot_id=slot_id,
            patient_name="MediBook Test Patient",
            patient_phone="01700000001",
        )

        print()
        print("FIRST BOOKING:")
        print(result)

    # -----------------------------------------
    # Second booking of SAME slot
    # must fail.
    # -----------------------------------------

    async with AsyncSessionFactory() as session:
        service = AppointmentService(
            session
        )

        try:
            await service.confirm_booking(
                slot_id=slot_id,
                patient_name="Second Test Patient",
                patient_phone="01700000002",
            )

            raise RuntimeError(
                "CRITICAL: DOUBLE BOOKING WAS ALLOWED"
            )

        except SlotUnavailableError:
            print()
            print(
                "DOUBLE BOOKING PROTECTION: PASS"
            )


asyncio.run(main())
