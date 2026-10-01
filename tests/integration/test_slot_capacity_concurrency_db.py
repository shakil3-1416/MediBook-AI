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

ATTEMPTS = 8
CAPACITY = 2


async def _open_session():
    gen = get_db_session()
    session = await anext(gen)
    return gen, session


@pytest.mark.asyncio
async def test_capacity_holds_under_concurrent_bookings():
    gen, session = await _open_session()
    token = uuid4().hex[:10]
    phones = [f"CONC-{index}-{token}" for index in range(ATTEMPTS)]
    workers = []
    slot_id = None

    try:
        hd = await session.scalar(
            select(HospitalDoctor)
            .join(Hospital, Hospital.id == HospitalDoctor.hospital_id)
            .where(
                Hospital.slug == "medibook-demo",
                HospitalDoctor.is_active.is_(True),
            )
            .limit(1)
        )
        assert hd is not None

        slot = DoctorSlot(
            hospital_doctor_id=hd.id,
            doctor_id=hd.doctor_id,
            slot_date=date.today() + timedelta(days=6000 + uuid4().int % 500),
            start_time=time(22, uuid4().int % 60),
            capacity=CAPACITY,
            is_enabled=True,
            is_available=True,
        )
        session.add(slot)
        await session.flush()
        slot_id = slot.id
        hospital_id = hd.hospital_id
        await session.commit()

        workers = [await _open_session() for _ in range(ATTEMPTS)]

        async def attempt(index: int) -> str:
            worker_session = workers[index][1]
            try:
                booking = await AppointmentService(worker_session).confirm_booking(
                    slot_id=slot_id,
                    hospital_id=hospital_id,
                    patient_name=f"Concurrent Patient {index}",
                    patient_phone=phones[index],
                )
            except SlotUnavailableError:
                await worker_session.rollback()
                return "unavailable"
            return booking["status"]

        outcomes = await asyncio.gather(*(attempt(index) for index in range(ATTEMPTS)))

        assert outcomes.count("confirmed") == CAPACITY, outcomes
        assert outcomes.count("unavailable") == ATTEMPTS - CAPACITY, outcomes

        active = await AppointmentService(session).active_slot_count(slot_id=slot_id)
        assert active == CAPACITY

    finally:
        for worker_gen, worker_session in workers:
            await worker_session.rollback()
            await worker_gen.aclose()

        await session.rollback()

        if slot_id is not None:
            await session.execute(
                text(
                    "DELETE FROM appointment_events WHERE appointment_id IN ("
                    "SELECT id FROM appointments WHERE doctor_slot_id = :slot_id)"
                ),
                {"slot_id": slot_id},
            )
            await session.execute(
                text("DELETE FROM appointments WHERE doctor_slot_id = :slot_id"),
                {"slot_id": slot_id},
            )
            await session.execute(
                text("DELETE FROM doctor_slots WHERE id = :slot_id"),
                {"slot_id": slot_id},
            )

        for phone in phones:
            await session.execute(
                text("DELETE FROM patients WHERE phone = :phone"),
                {"phone": phone},
            )

        await session.commit()
        await gen.aclose()
