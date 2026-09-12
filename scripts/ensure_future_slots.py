import asyncio
from datetime import date, time, timedelta

from sqlalchemy import select

from app.core.database import AsyncSessionFactory
from app.models.doctor import Doctor
from app.models.schedule import DoctorSlot


TIMES = [
    time(17, 0),
    time(17, 30),
    time(18, 0),
    time(18, 30),
    time(19, 0),
]


async def main() -> None:
    created = 0

    async with AsyncSessionFactory() as session:
        doctors = list(
            (
                await session.execute(
                    select(Doctor).where(
                        Doctor.is_active.is_(True)
                    )
                )
            ).scalars().all()
        )

        tomorrow = date.today() + timedelta(days=1)

        for day_offset in range(7):
            slot_date = tomorrow + timedelta(
                days=day_offset
            )

            for doctor in doctors:
                for slot_time in TIMES:
                    exists = await session.scalar(
                        select(DoctorSlot.id).where(
                            DoctorSlot.doctor_id
                            == doctor.id,
                            DoctorSlot.slot_date
                            == slot_date,
                            DoctorSlot.start_time
                            == slot_time,
                        )
                    )

                    if exists:
                        continue

                    session.add(
                        DoctorSlot(
                            doctor_id=doctor.id,
                            slot_date=slot_date,
                            start_time=slot_time,
                            is_available=True,
                        )
                    )

                    created += 1

        await session.commit()

    print(
        f"Future slots created: {created}"
    )


asyncio.run(main())
