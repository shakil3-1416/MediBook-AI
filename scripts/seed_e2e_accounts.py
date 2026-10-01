"""Create or refresh the E2E test accounts. Development and CI only.

  e2e-patient@example.com          role patient
  e2e-hospital-admin@example.com   hospital_admin membership in E2E_HOSPITAL_SLUG
                                   (default medibook-demo)
  e2e-platform-admin@example.com   role platform_admin

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

from sqlalchemy import Boolean, DateTime, inspect as sa_inspect, select

from app.core import roles
from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import hash_password
from app.models.hospital import Hospital, HospitalMembership
from app.models.user import User

HOSPITAL_SLUG = os.getenv("E2E_HOSPITAL_SLUG", "medibook-demo")
POSITIVE_FLAGS = ("active", "verified", "enabled")
NEGATIVE_FLAGS = ("inactive", "disabled", "locked", "deleted", "banned", "suspended")


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
        other_slug = await session.scalar(
            select(Hospital.slug).where(Hospital.slug.notin_([HOSPITAL_SLUG])).order_by(Hospital.slug).limit(1)
        )
        member_role = await _hospital_user_role(session)
        await _upsert_user(session, "e2e-patient@example.com", roles.PATIENT, "E2E Patient", passwords["PATIENT"])
        admin = await _upsert_user(session, "e2e-hospital-admin@example.com", member_role, "E2E Hospital Admin", passwords["HOSPITAL"])
        await _ensure_membership(session, admin, hospital)
        await _upsert_user(session, "e2e-platform-admin@example.com", roles.PLATFORM_ADMIN, "E2E Platform Admin", passwords["PLATFORM"])
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
        "E2E_OTHER_HOSPITAL_SLUG=" + (other_slug or ""),
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
