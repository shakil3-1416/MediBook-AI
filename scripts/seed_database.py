import asyncio
from datetime import date, time, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.database import AsyncSessionFactory
from app.models.doctor import Doctor, Specialty
from app.models.schedule import DoctorSlot


async def main() -> None:
    async with AsyncSessionFactory() as session:

        existing = await session.scalar(
            select(Specialty.id).limit(1)
        )

        if existing is not None:
            print("Seed data already exists.")
            return

        cardiology = Specialty(name="Cardiology")
        dermatology = Specialty(name="Dermatology")
        neurology = Specialty(name="Neurology")

        session.add_all([
            cardiology,
            dermatology,
            neurology,
        ])

        await session.flush()

        doctors = [
            Doctor(
                full_name="Dr. Farhana Ahmed",
                gender="female",
                qualification="MBBS, MD (Cardiology)",
                experience_years=12,
                specialty_id=cardiology.id,
                clinic_name="MediCare Dhanmondi",
                clinic_location="Dhanmondi, Dhaka",
                consultation_fee=Decimal("1200"),
            ),
            Doctor(
                full_name="Dr. Hasan Rahman",
                gender="male",
                qualification="MBBS, FCPS (Cardiology)",
                experience_years=10,
                specialty_id=cardiology.id,
                clinic_name="MediCare Mirpur",
                clinic_location="Mirpur, Dhaka",
                consultation_fee=Decimal("1000"),
            ),
            Doctor(
                full_name="Dr. Nusrat Jahan",
                gender="female",
                qualification="MBBS, DDV",
                experience_years=8,
                specialty_id=dermatology.id,
                clinic_name="MediCare Dhanmondi",
                clinic_location="Dhanmondi, Dhaka",
                consultation_fee=Decimal("900"),
            ),
            Doctor(
                full_name="Dr. Arif Hossain",
                gender="male",
                qualification="MBBS, MD (Neurology)",
                experience_years=15,
                specialty_id=neurology.id,
                clinic_name="MediCare Uttara",
                clinic_location="Uttara, Dhaka",
                consultation_fee=Decimal("1500"),
            ),
        ]

        session.add_all(doctors)
        await session.flush()

        tomorrow = date.today() + timedelta(days=1)

        available_times = [
            time(17, 0),
            time(17, 30),
            time(18, 0),
            time(18, 30),
            time(19, 0),
        ]

        slots = []

        for doctor in doctors:
            for start_time in available_times:
                slots.append(
                    DoctorSlot(
                        doctor_id=doctor.id,
                        slot_date=tomorrow,
                        start_time=start_time,
                        is_available=True,
                    )
                )

        session.add_all(slots)

        await session.commit()

        print(f"Seeded {len(doctors)} doctors.")
        print(f"Seeded {len(slots)} slots.")


if __name__ == "__main__":
    asyncio.run(main())
