"""Create or refresh Dhaka Demo Hospital for hands-on testing.

It sets up, and on later runs only fills gaps in:
  - hospital dhaka-demo-hospital (Asia/Dhaka, managed data, active), provisioned
    through PlatformControlService exactly like POST /api/v1/platform-control-v2/hospitals
  - hospital admin demo-admin@medibook.test with a fresh random password
  - 24 Dhaka doctors from the national network: 3 each from the 4 most common
    specialties and 2 each from the next 6, linked as managed hospital doctors
  - weekly rules Saturday to Thursday, Friday closed: half the doctors 10:00-13:00,
    half 17:00-21:00, 20-minute slots, capacity 1
  - bookable slots for the next 30 days, made by HospitalScheduleEngine.apply

Usage: PYTHONPATH=. .venv/bin/python scripts/seed_demo_hospital.py LOGIN_FILE
The admin login goes to LOGIN_FILE (mode 600), never to the screen or the repo.
"""
from __future__ import annotations

import asyncio
import os
import secrets
import sys
from collections import defaultdict
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from app.core import roles
from app.core.database import AsyncSessionFactory
from app.models.control_plane import DoctorScheduleRule
from app.models.doctor import Doctor, Specialty
from app.models.hospital import Hospital, HospitalDoctor
from app.models.schedule import DoctorSlot
from app.models.user import User
from app.schemas.platform_control_v2 import PlatformHospitalProvisionRequest
from app.services.hospital_schedule_engine import HospitalScheduleEngine, ScheduleEngineError
from app.services.platform_control_v2 import PlatformControlError, PlatformControlService
from scripts.seed_e2e_accounts import _ensure_membership, _hospital_user_role, _upsert_user

SLUG = "dhaka-demo-hospital"
NAME = "Dhaka Demo Hospital"
TIMEZONE = "Asia/Dhaka"
ADMIN_EMAIL = "demo-admin@medibook.test"
PER_SPECIALTY = (3, 3, 3, 3, 2, 2, 2, 2, 2, 2)
WORKDAYS = (5, 6, 0, 1, 2, 3)  # Python weekday(): Saturday to Thursday; Friday (4) closed
SESSIONS = ((time(10, 0), time(13, 0)), (time(17, 0), time(21, 0)))
SLOT_MINUTES = 20
DAYS_AHEAD = 30


def write_login(path: str, password: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(
            f"{NAME}\n"
            f"  hospital admin  {ADMIN_EMAIL}\n"
            f"  password        {password}\n"
            f"  sign in         http://localhost:3000/hospital-login\n"
            f"  chat widget     http://localhost:3000/widget/{SLUG}\n"
        )
    os.chmod(path, 0o600)


async def link_doctors(session, hospital_id) -> int:
    linked = set(await session.scalars(
        select(HospitalDoctor.doctor_id).where(HospitalDoctor.hospital_id == hospital_id)
    ))
    if len(linked) >= sum(PER_SPECIALTY):
        return 0
    rows = (await session.execute(
        select(Doctor, Specialty.name)
        .join(Specialty, Specialty.id == Doctor.specialty_id)
        .where(
            Doctor.is_active.is_(True),
            Doctor.clinic_location.ilike("%, Dhaka"),
            Doctor.full_name.notilike("e2e%"),
        )
        .order_by(Doctor.experience_years.desc(), Doctor.full_name)
    )).all()
    by_specialty = defaultdict(list)
    for doctor, specialty in rows:
        by_specialty[specialty].append(doctor)
    top = sorted(by_specialty, key=lambda name: (-len(by_specialty[name]), name))[:len(PER_SPECIALTY)]
    added = 0
    for specialty, count in zip(top, PER_SPECIALTY):
        for doctor in by_specialty[specialty][:count]:
            if doctor.id in linked:
                continue
            session.add(HospitalDoctor(
                hospital_id=hospital_id,
                doctor_id=doctor.id,
                is_active=True,
                source_mode="managed",
                clinic_name=NAME,
                clinic_location=doctor.clinic_location,
                consultation_fee=doctor.consultation_fee,
                public_profile={},
                operational_metadata={"seeded_by": "seed_demo_hospital"},
            ))
            added += 1
    await session.commit()
    return added


async def add_rules(session, mapping_ids, today) -> int:
    added = 0
    for index, mapping_id in enumerate(mapping_ids):
        existing = await session.scalar(
            select(func.count()).select_from(DoctorScheduleRule).where(
                DoctorScheduleRule.hospital_doctor_id == mapping_id,
                DoctorScheduleRule.is_active.is_(True),
            )
        )
        if existing:
            continue
        start, end = SESSIONS[index % 2]
        for weekday in WORKDAYS:
            session.add(DoctorScheduleRule(
                hospital_doctor_id=mapping_id,
                weekday=weekday,
                start_time=start,
                end_time=end,
                slot_duration_minutes=SLOT_MINUTES,
                capacity=1,
                valid_from=today,
                is_active=True,
            ))
            added += 1
    await session.commit()
    return added


async def make_slots(session, hospital_id, actor_id, mapping_ids, today) -> tuple[int, list[str]]:
    engine = HospitalScheduleEngine(session)
    created = 0
    problems = []
    for mapping_id in mapping_ids:
        mapping = await session.get(HospitalDoctor, mapping_id)
        try:
            result = await engine.apply(
                mapping=mapping,
                hospital_id=hospital_id,
                actor_user_id=actor_id,
                start_date=today,
                end_date=today + timedelta(days=DAYS_AHEAD),
            )
            await session.commit()
            created += int(result.get("created", 0) or 0)
        except ScheduleEngineError as exc:
            await session.rollback()
            problems.append(f"{mapping_id}: {exc}")
    return created, problems


async def main(login_file: str) -> int:
    today = datetime.now(ZoneInfo(TIMEZONE)).date()
    async with AsyncSessionFactory() as session:
        platform_admin = await session.scalar(
            select(User).where(User.role == roles.PLATFORM_ADMIN).order_by(User.email).limit(1)
        )
        if platform_admin is None:
            print("No platform admin exists yet. Run: bash ~/medibook-tools/medibook_local.sh start")
            return 1
        platform_admin_id = platform_admin.id

        password = secrets.token_urlsafe(18)
        admin = await _upsert_user(session, ADMIN_EMAIL, await _hospital_user_role(session), "Demo", password)
        admin_id = admin.id
        await session.commit()
        write_login(login_file, password)

        hospital = await session.scalar(select(Hospital).where(Hospital.slug == SLUG))
        if hospital is None:
            service = PlatformControlService(session, actor_user_id=platform_admin_id)
            try:
                await service.provision(PlatformHospitalProvisionRequest(
                    name=NAME, slug=SLUG, timezone=TIMEZONE,
                    initial_admin_email=ADMIN_EMAIL, activate=True,
                ))
            except PlatformControlError as exc:
                print(f"provisioning failed: {exc}")
                return 1
            await session.commit()
            hospital = await session.scalar(select(Hospital).where(Hospital.slug == SLUG))
            print(f"provisioned {NAME} ({SLUG})")
        else:
            print(f"{NAME} already exists; reusing it")
        hospital_id = hospital.id
        if hospital.status != "active" or hospital.is_active is not True:
            hospital.status = "active"
            hospital.is_active = True
            print("hospital set to active")
        await _ensure_membership(session, admin, hospital)
        await session.commit()

        added = await link_doctors(session, hospital_id)
        mapping_ids = list(await session.scalars(
            select(HospitalDoctor.id)
            .where(HospitalDoctor.hospital_id == hospital_id, HospitalDoctor.is_active.is_(True))
            .order_by(HospitalDoctor.created_at, HospitalDoctor.id)
        ))
        print(f"doctors linked now: {added}; active doctors in the hospital: {len(mapping_ids)}")

        rules = await add_rules(session, mapping_ids, today)
        print(f"weekly schedule rules added: {rules}")

        created, problems = await make_slots(session, hospital_id, admin_id, mapping_ids, today)
        print(f"slots created for the next {DAYS_AHEAD} days: {created}")
        for problem in problems:
            print(f"  schedule not applied for {problem}")

        future = await session.scalar(
            select(func.count()).select_from(DoctorSlot)
            .join(HospitalDoctor, HospitalDoctor.id == DoctorSlot.hospital_doctor_id)
            .where(
                HospitalDoctor.hospital_id == hospital_id,
                DoctorSlot.slot_date >= today,
                DoctorSlot.is_enabled.is_(True),
            )
        )
        mix = (await session.execute(
            select(Specialty.name, func.count())
            .select_from(HospitalDoctor)
            .join(Doctor, Doctor.id == HospitalDoctor.doctor_id)
            .join(Specialty, Specialty.id == Doctor.specialty_id)
            .where(HospitalDoctor.hospital_id == hospital_id, HospitalDoctor.is_active.is_(True))
            .group_by(Specialty.name)
            .order_by(func.count().desc(), Specialty.name)
        )).all()
        print(f"bookable future slots: {future}")
        print("specialties: " + ", ".join(f"{name} {count}" for name, count in mix))
        return 0 if not problems else 2


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: seed_demo_hospital.py LOGIN_FILE")
    raise SystemExit(asyncio.run(main(sys.argv[1])))
