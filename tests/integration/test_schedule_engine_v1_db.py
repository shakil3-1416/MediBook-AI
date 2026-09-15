from datetime import date, time, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text

from app.core.database import get_db_session
from app.models.control_plane import (
    DoctorScheduleException,
    DoctorScheduleRule,
    HospitalOperationsAudit,
)
from app.models.hospital import (
    Hospital,
    HospitalDoctor,
)
from app.models.schedule import DoctorSlot
from app.services.appointment_service import (
    AppointmentService,
)
from app.services.hospital_schedule_engine import (
    HospitalScheduleEngine,
    ScheduleConflictError,
)


@pytest.mark.asyncio
async def test_schedule_engine_real_postgres_flow():
    gen = get_db_session()
    session = await anext(gen)

    token = uuid4().hex[:10]
    phone = "SCHED-" + token

    mapping_ref = None
    rule = None
    exception = None

    try:
        mapping = await session.scalar(
            select(HospitalDoctor)
            .join(
                Hospital,
                Hospital.id
                == HospitalDoctor.hospital_id,
            )
            .where(
                Hospital.slug == "medibook-demo",
                HospitalDoctor.is_active.is_(True),
                HospitalDoctor.source_mode.in_(
                    ["managed", "hybrid"]
                ),
            )
            .limit(1)
        )

        assert mapping is not None

        mapping_ref = SimpleNamespace(
            id=mapping.id,
            doctor_id=mapping.doctor_id,
            hospital_id=mapping.hospital_id,
            source_mode=mapping.source_mode,
        )

        target = date.today() + timedelta(
            days=4200 + uuid4().int % 100
        )

        rule = DoctorScheduleRule(
            hospital_doctor_id=mapping_ref.id,
            weekday=target.weekday(),
            start_time=time(9, 0),
            end_time=time(10, 0),
            slot_duration_minutes=20,
            capacity=2,
            valid_from=target,
            valid_until=target,
            is_active=True,
        )

        session.add(rule)
        await session.commit()

        engine = HospitalScheduleEngine(
            session
        )

        desired = await engine.desired_slots(
            hospital_doctor_id=mapping_ref.id,
            start_date=target,
            end_date=target,
        )

        assert len(desired) == 3
        assert all(
            item["capacity"] == 2
            for item in desired
        )

        await session.commit()

        result = await engine.apply(
            mapping=mapping_ref,
            hospital_id=mapping_ref.hospital_id,
            actor_user_id=None,
            start_date=target,
            end_date=target,
        )

        assert result["created"] == 3
        assert result["conflicts"] == []

        await session.commit()

        slots = list(
            (
                await session.execute(
                    select(DoctorSlot)
                    .where(
                        DoctorSlot.hospital_doctor_id
                        == mapping_ref.id,
                        DoctorSlot.slot_date
                        == target,
                        DoctorSlot.is_enabled.is_(True),
                    )
                    .order_by(
                        DoctorSlot.start_time
                    )
                )
            )
            .scalars()
            .all()
        )

        assert len(slots) == 3

        audit_count = await session.scalar(
            select(
                func.count(
                    HospitalOperationsAudit.id
                )
            ).where(
                HospitalOperationsAudit.hospital_id
                == mapping_ref.hospital_id,
                HospitalOperationsAudit.entity_id
                == mapping_ref.id,
                HospitalOperationsAudit.action
                == "schedule.materialized",
            )
        )

        assert int(audit_count or 0) >= 1

        booked_slot_id = slots[0].id

        await session.commit()

        service = AppointmentService(
            session
        )

        booking = await service.confirm_booking(
            slot_id=booked_slot_id,
            hospital_id=mapping_ref.hospital_id,
            patient_name="Schedule Conflict Patient",
            patient_phone=phone,
        )

        assert booking["status"] == "confirmed"

        exception = DoctorScheduleException(
            hospital_doctor_id=mapping_ref.id,
            exception_date=target,
            kind="leave",
            reason="Integration proof leave",
            is_active=True,
        )

        session.add(exception)
        await session.commit()

        preview = await engine.preview(
            mapping=mapping_ref,
            start_date=target,
            end_date=target,
        )

        assert preview["conflicts"]
        assert any(
            item["reason"]
            == "schedule_would_remove_booked_slot"
            for item in preview["conflicts"]
        )

        await session.commit()

        with pytest.raises(
            ScheduleConflictError
        ):
            await engine.apply(
                mapping=mapping_ref,
                hospital_id=mapping_ref.hospital_id,
                actor_user_id=None,
                start_date=target,
                end_date=target,
            )

        await session.rollback()

        active = await session.scalar(
            select(
                func.count(DoctorSlot.id)
            ).where(
                DoctorSlot.hospital_doctor_id
                == mapping_ref.id,
                DoctorSlot.slot_date
                == target,
                DoctorSlot.is_enabled.is_(True),
            )
        )

        assert int(active or 0) == 3

    finally:
        await session.rollback()

        if mapping_ref is not None:
            await session.execute(
                text(
                    "DELETE FROM appointment_events "
                    "WHERE appointment_id IN ("
                    "SELECT a.id "
                    "FROM appointments a "
                    "JOIN doctor_slots ds "
                    "ON ds.id = a.doctor_slot_id "
                    "WHERE ds.hospital_doctor_id = :hd "
                    "AND ds.slot_date >= :start_date)"
                ),
                {
                    "hd": mapping_ref.id,
                    "start_date": date.today()
                    + timedelta(days=4000),
                },
            )

            await session.execute(
                text(
                    "DELETE FROM appointments "
                    "WHERE doctor_slot_id IN ("
                    "SELECT id FROM doctor_slots "
                    "WHERE hospital_doctor_id = :hd "
                    "AND slot_date >= :start_date)"
                ),
                {
                    "hd": mapping_ref.id,
                    "start_date": date.today()
                    + timedelta(days=4000),
                },
            )

            await session.execute(
                text(
                    "DELETE FROM doctor_slots "
                    "WHERE hospital_doctor_id = :hd "
                    "AND slot_date >= :start_date"
                ),
                {
                    "hd": mapping_ref.id,
                    "start_date": date.today()
                    + timedelta(days=4000),
                },
            )

            await session.execute(
                text(
                    "DELETE FROM doctor_schedule_exceptions "
                    "WHERE hospital_doctor_id = :hd "
                    "AND exception_date >= :start_date"
                ),
                {
                    "hd": mapping_ref.id,
                    "start_date": date.today()
                    + timedelta(days=4000),
                },
            )

            await session.execute(
                text(
                    "DELETE FROM doctor_schedule_rules "
                    "WHERE hospital_doctor_id = :hd "
                    "AND valid_from >= :start_date"
                ),
                {
                    "hd": mapping_ref.id,
                    "start_date": date.today()
                    + timedelta(days=4000),
                },
            )

            await session.execute(
                text(
                    "DELETE FROM hospital_operations_audit "
                    "WHERE hospital_id = :hospital_id "
                    "AND entity_id = :hd "
                    "AND action = :action"
                ),
                {
                    "hospital_id":
                    mapping_ref.hospital_id,
                    "hd": mapping_ref.id,
                    "action": "schedule.materialized",
                },
            )

        await session.execute(
            text(
                "DELETE FROM patients "
                "WHERE phone = :phone"
            ),
            {"phone": phone},
        )

        await session.commit()
        await gen.aclose()
