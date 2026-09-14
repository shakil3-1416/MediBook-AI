import asyncio
from datetime import date, time, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select, text

from app.core.database import get_db_session
from app.models.hospital import Hospital, HospitalDoctor
from app.models.schedule import DoctorSlot
from app.services.appointment_service import (
    AppointmentService,
    SlotUnavailableError,
)


@pytest.mark.asyncio
async def test_capacity_two_real_postgres_flow():
    gen = get_db_session()
    session = await anext(gen)

    token = uuid4().hex[:10]

    phones = [
        "CAP-A-" + token,
        "CAP-B-" + token,
        "CAP-C-" + token,
    ]

    slot_id = None

    try:
        hd = await session.scalar(
            select(HospitalDoctor)
            .join(
                Hospital,
                Hospital.id == HospitalDoctor.hospital_id,
            )
            .where(
                Hospital.slug == "medibook-demo",
                HospitalDoctor.is_active.is_(True),
            )
            .limit(1)
        )

        assert hd is not None

        slot_date = date.today() + timedelta(
            days=5000 + uuid4().int % 500
        )

        slot_time = time(
            21,
            uuid4().int % 60,
        )

        existing = await session.scalar(
            select(DoctorSlot.id).where(
                DoctorSlot.hospital_doctor_id == hd.id,
                DoctorSlot.slot_date == slot_date,
                DoctorSlot.start_time == slot_time,
            )
        )

        if existing is not None:
            slot_date = slot_date + timedelta(days=700)

        slot = DoctorSlot(
            hospital_doctor_id=hd.id,
            doctor_id=hd.doctor_id,
            slot_date=slot_date,
            start_time=slot_time,
            capacity=2,
            is_enabled=True,
            is_available=True,
        )

        session.add(slot)

        await session.flush()

        slot_id = slot.id
        hospital_id = hd.hospital_id

        await session.commit()

        service = AppointmentService(session)

        booking_a = await service.confirm_booking(
            slot_id=slot_id,
            hospital_id=hospital_id,
            patient_name="Capacity Patient A",
            patient_phone=phones[0],
        )

        booking_b = await service.confirm_booking(
            slot_id=slot_id,
            hospital_id=hospital_id,
            patient_name="Capacity Patient B",
            patient_phone=phones[1],
        )

        assert booking_a["status"] == "confirmed"
        assert booking_b["status"] == "confirmed"

        with pytest.raises(SlotUnavailableError):
            await service.confirm_booking(
                slot_id=slot_id,
                hospital_id=hospital_id,
                patient_name="Capacity Patient C",
                patient_phone=phones[2],
            )

        await service.cancel_appointment(
            confirmation_code=booking_a[
                "confirmation_code"
            ],
            patient_phone=phones[0],
            hospital_id=hospital_id,
        )

        booking_c = await service.confirm_booking(
            slot_id=slot_id,
            hospital_id=hospital_id,
            patient_name="Capacity Patient C",
            patient_phone=phones[2],
        )

        assert booking_c["status"] == "confirmed"

        active = await service.active_slot_count(
            slot_id=slot_id,
        )

        assert active == 2

        await session.rollback()

        slot_state = await session.scalar(
            select(DoctorSlot).where(
                DoctorSlot.id == slot_id
            )
        )

        assert slot_state is not None
        assert slot_state.capacity == 2
        assert slot_state.is_available is False

    finally:
        await session.rollback()

        if slot_id is not None:
            await session.execute(
                text(
                    "DELETE FROM appointment_events "
                    "WHERE appointment_id IN ("
                    "SELECT id FROM appointments "
                    "WHERE doctor_slot_id = :slot_id)"
                ),
                {"slot_id": slot_id},
            )

            await session.execute(
                text(
                    "DELETE FROM appointments "
                    "WHERE doctor_slot_id = :slot_id"
                ),
                {"slot_id": slot_id},
            )

            await session.execute(
                text(
                    "DELETE FROM doctor_slots "
                    "WHERE id = :slot_id"
                ),
                {"slot_id": slot_id},
            )

        for phone in phones:
            await session.execute(
                text(
                    "DELETE FROM patients "
                    "WHERE phone = :phone"
                ),
                {"phone": phone},
            )

        await session.commit()
        await gen.aclose()
