"""Create or refresh the E2E test accounts. Development and CI only.

  e2e-patient@example.com          role patient
  e2e-hospital-admin@example.com   hospital_admin membership in E2E_HOSPITAL_SLUG
                                   (default medibook-demo)
  e2e-platform-admin@example.com   role platform_admin

It also makes sure the second hospital has a doctor the primary hospital does
not have (an existing one, or a hidden "E2E Isolation Doctor" copied from an
existing record), linked inactive, so object-level authorization can be probed.

Every run sets fresh random passwords and writes emails, passwords and hospital
slugs as KEY=VALUE lines to the file given as the only argument (mode 600).
Refuses to run when APP_ENV is production.

Usage: PYTHONPATH=. python scripts/seed_e2e_accounts.py /path/to/e2e.env
"""

from __future__ import annotations

import asyncio
import os
import secrets
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import Boolean, DateTime, UniqueConstraint, inspect as sa_inspect, select

from app.core import roles
from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import hash_password
from app.models.hospital import Hospital, HospitalDoctor, HospitalMembership
from app.models.user import User

HOSPITAL_SLUG = os.getenv("E2E_HOSPITAL_SLUG", "medibook-demo")
POSITIVE_FLAGS = ("active", "verified", "enabled")
NEGATIVE_FLAGS = ("inactive", "disabled", "locked", "deleted", "banned", "suspended")
HIDDEN_FLAGS = ("active", "public", "publish", "visible", "verified", "available", "featured", "enabled")
ISOLATION_DOCTOR = "E2E Isolation Doctor"


def _environment() -> str:
    return str(getattr(settings, "app_env", "") or os.getenv("APP_ENV", "")).lower()


def _positive_flag(name: str) -> bool:
    lowered = name.lower()
    return any(w in lowered for w in POSITIVE_FLAGS) and not any(w in lowered for w in NEGATIVE_FLAGS)


def _attribute_keys(model) -> dict[str, str]:
    mapper = sa_inspect(model)
    return {column.name: prop.key for prop in mapper.column_attrs for column in prop.columns}


def _complete(model, values: dict, label: str) -> list[str]:
    """Fill columns the caller did not set: required ones plus active/verified flags."""
    filled = []
    now = datetime.now(timezone.utc)
    for column in model.__table__.columns:
        name = column.name
        if name in values:
            continue
        lowered = name.lower()
        has_default = column.default is not None or column.server_default is not None
        if isinstance(column.type, Boolean) and _positive_flag(name):
            values[name] = True
        elif isinstance(column.type, DateTime) and "verified" in lowered:
            values[name] = now
        elif column.nullable or has_default:
            continue
        elif column.primary_key:
            values[name] = uuid.uuid4()
        elif "name" in lowered:
            values[name] = label
        elif "phone" in lowered:
            values[name] = "019" + str(secrets.randbelow(10**8)).zfill(8)
        elif isinstance(column.type, DateTime):
            values[name] = now
        elif isinstance(column.type, Boolean):
            values[name] = False
        else:
            raise SystemExit(f"cannot fill required column {model.__tablename__}.{name}")
        filled.append(name)
    return filled


def _build(model, values: dict):
    keys = _attribute_keys(model)
    return model(**{keys.get(name, name): value for name, value in values.items()})


async def _upsert_user(session, email: str, role: str, label: str, password: str):
    keys = _attribute_keys(User)
    password_columns = [c.name for c in User.__table__.columns if "password" in c.name.lower()]
    secret_hash = hash_password(password)
    user = await session.scalar(select(User).where(User.email == email))
    if user is None:
        values = {"email": email, "role": role}
        values.update({name: secret_hash for name in password_columns})
        filled = _complete(User, values, label)
        user = _build(User, values)
        session.add(user)
        print(f"created {email} as {role} (auto-filled: {', '.join(filled) or 'none'})")
    else:
        user.role = role
        for name in password_columns:
            setattr(user, keys[name], secret_hash)
        now = datetime.now(timezone.utc)
        for column in User.__table__.columns:
            if isinstance(column.type, Boolean) and _positive_flag(column.name):
                setattr(user, keys[column.name], True)
            elif isinstance(column.type, DateTime) and "verified" in column.name.lower() and getattr(user, keys[column.name]) is None:
                setattr(user, keys[column.name], now)
        print(f"refreshed {email} as {role}")
    await session.flush()
    return user


async def _ensure_membership(session, user, hospital) -> None:
    keys = _attribute_keys(HospitalMembership)
    membership = await session.scalar(
        select(HospitalMembership).where(
            HospitalMembership.hospital_id == hospital.id,
            HospitalMembership.user_id == user.id,
        )
    )
    if membership is None:
        values = {"hospital_id": hospital.id, "user_id": user.id, "role": roles.HOSPITAL_ADMIN}
        filled = _complete(HospitalMembership, values, "E2E")
        session.add(_build(HospitalMembership, values))
        print(f"hospital_admin membership in {hospital.slug} (auto-filled: {', '.join(filled) or 'none'})")
    else:
        setattr(membership, keys["role"], roles.HOSPITAL_ADMIN)
        if "is_active" in keys:
            setattr(membership, keys["is_active"], True)
        print(f"membership in {hospital.slug} refreshed")


async def _hospital_user_role(session) -> str:
    found = await session.scalar(
        select(User.role)
        .join(HospitalMembership, HospitalMembership.user_id == User.id)
        .where(User.role.notin_([roles.PLATFORM_ADMIN]))
        .limit(1)
    )
    return found or roles.PATIENT


async def _create_isolation_doctor(session, doctor_model):
    """Copy an existing doctor into a hidden test doctor with unique fields marked."""
    template = await session.scalar(select(doctor_model).limit(1))
    if template is None:
        return None
    table = doctor_model.__table__
    keys = _attribute_keys(doctor_model)
    unique = {c.name for c in table.columns if c.unique}
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint):
            unique.update(c.name for c in constraint.columns)
    for index in table.indexes:
        if index.unique:
            unique.update(c.name for c in index.columns)
    marker = "e2e-iso-" + secrets.token_hex(3)
    now = datetime.now(timezone.utc)
    values = {}
    for column in table.columns:
        lowered = column.name.lower()
        value = getattr(template, keys[column.name])
        if column.primary_key:
            value = uuid.uuid4()
        elif isinstance(column.type, Boolean) and any(word in lowered for word in HIDDEN_FLAGS):
            value = False
        elif isinstance(column.type, DateTime) and lowered in ("created_at", "updated_at"):
            value = now
        elif "name" in lowered and isinstance(value, str):
            value = ISOLATION_DOCTOR
        if column.name in unique and isinstance(value, str):
            length = getattr(column.type, "length", None) or 255
            value = (marker + "-" + value)[:length]
        values[column.name] = value
    async with session.begin_nested():
        doctor = _build(doctor_model, values)
        session.add(doctor)
        await session.flush()
        return doctor.id


async def _ensure_isolation_fixture(session, primary, other) -> str:
    if other is None:
        return "no second hospital"
    try:
        from app.models.doctor import Doctor
    except ImportError:
        return "doctor model not importable; fixture skipped"
    primary_doctors = select(HospitalDoctor.doctor_id).where(HospitalDoctor.hospital_id == primary.id)
    existing = await session.scalar(
        select(HospitalDoctor.doctor_id)
        .where(HospitalDoctor.hospital_id == other.id, HospitalDoctor.doctor_id.notin_(primary_doctors))
        .limit(1)
    )
    if existing is not None:
        return f"fixture present in {other.slug}"
    candidate = await session.scalar(select(Doctor.id).where(Doctor.id.notin_(primary_doctors)).limit(1))
    created = False
    if candidate is None:
        try:
            candidate = await _create_isolation_doctor(session, Doctor)
            created = candidate is not None
        except Exception as exc:
            return f"could not create an isolation doctor ({type(exc).__name__}: {str(exc)[:160]})"
    if candidate is None:
        return "no doctor available for the fixture"
    values = {"hospital_id": other.id, "doctor_id": candidate, "is_active": False}
    _complete(HospitalDoctor, values, "E2E")
    async with session.begin_nested():
        session.add(_build(HospitalDoctor, values))
        await session.flush()
    return ("created a hidden test doctor and " if created else "") + f"linked it to {other.slug} (inactive)"


async def main(out_path: str) -> None:
    if _environment() in {"production", "prod"}:
        raise SystemExit("refusing to create test accounts when APP_ENV is production")
    passwords = {key: secrets.token_urlsafe(18) for key in ("PATIENT", "HOSPITAL", "PLATFORM")}
    gen = get_db_session()
    session = await anext(gen)
    try:
        hospital = await session.scalar(select(Hospital).where(Hospital.slug == HOSPITAL_SLUG))
        if hospital is None:
            raise SystemExit(f"hospital {HOSPITAL_SLUG} not found")
        other_hospital = await session.scalar(
            select(Hospital).where(Hospital.slug.notin_([HOSPITAL_SLUG])).order_by(Hospital.slug).limit(1)
        )
        member_role = await _hospital_user_role(session)
        await _upsert_user(session, "e2e-patient@example.com", roles.PATIENT, "E2E Patient", passwords["PATIENT"])
        admin = await _upsert_user(session, "e2e-hospital-admin@example.com", member_role, "E2E Hospital Admin", passwords["HOSPITAL"])
        await _ensure_membership(session, admin, hospital)
        await _upsert_user(session, "e2e-platform-admin@example.com", roles.PLATFORM_ADMIN, "E2E Platform Admin", passwords["PLATFORM"])
        print("isolation fixture:", await _ensure_isolation_fixture(session, hospital, other_hospital))
        other_slug = other_hospital.slug if other_hospital is not None else ""
        await session.commit()
    finally:
        await gen.aclose()
    lines = [
        "E2E_PATIENT_EMAIL=e2e-patient@example.com",
        "E2E_PATIENT_PASSWORD=" + passwords["PATIENT"],
        "E2E_HOSPITAL_EMAIL=e2e-hospital-admin@example.com",
        "E2E_HOSPITAL_PASSWORD=" + passwords["HOSPITAL"],
        "E2E_PLATFORM_EMAIL=e2e-platform-admin@example.com",
        "E2E_PLATFORM_PASSWORD=" + passwords["PLATFORM"],
        "E2E_HOSPITAL_SLUG=" + HOSPITAL_SLUG,
        "E2E_OTHER_HOSPITAL_SLUG=" + other_slug,
    ]
    path = Path(out_path)
    path.touch(mode=0o600, exist_ok=True)
    path.chmod(0o600)
    path.write_text("\n".join(lines) + "\n")
    print(f"credentials for 3 accounts written to {path} (mode 600); hospital admin user role: {member_role}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: seed_e2e_accounts.py OUTPUT_ENV_FILE")
    asyncio.run(main(sys.argv[1]))
