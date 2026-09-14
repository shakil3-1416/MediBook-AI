from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionFactory
from app.models import Doctor, DoctorSlot
from app.models.hospital import Hospital, HospitalDoctor


router = APIRouter(
    prefix="/hospital-public",
    tags=["hospital-public"],
)


async def get_session():
    async with AsyncSessionFactory() as session:
        yield session


async def resolve_hospital(
    session: AsyncSession,
    slug: str,
) -> Hospital:
    hospital = await session.scalar(
        select(Hospital).where(
            Hospital.slug == slug,
            Hospital.is_active.is_(True),
        )
    )

    if hospital is None:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found.",
        )

    return hospital


async def require_doctor_membership(
    session: AsyncSession,
    hospital_id: uuid.UUID,
    doctor_id: uuid.UUID,
) -> None:
    mapping = await session.scalar(
        select(HospitalDoctor.id).where(
            HospitalDoctor.hospital_id
            == hospital_id,
            HospitalDoctor.doctor_id
            == doctor_id,
        )
    )

    if mapping is None:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found in this hospital.",
        )


@router.get(
    "/{hospital_slug}/doctors"
)
async def hospital_doctors(
    hospital_slug: str,
    specialty: str | None = None,
    gender: str | None = None,
    location: str | None = None,
    limit: int = Query(
        default=500,
        ge=1,
        le=500,
    ),
    session: AsyncSession = Depends(
        get_session
    ),
):
    hospital = await resolve_hospital(
        session,
        hospital_slug,
    )

    query = (
        select(Doctor)
        .join(
            HospitalDoctor,
            HospitalDoctor.doctor_id
            == Doctor.id,
        )
        .options(
            selectinload(
                Doctor.specialty
            )
        )
        .where(
            HospitalDoctor.hospital_id
            == hospital.id,
            Doctor.is_active.is_(True),
        )
    )

    if gender:
        query = query.where(
            Doctor.gender
            == gender.lower()
        )

    if location:
        query = query.where(
            Doctor.clinic_location.ilike(
                f"%{location}%"
            )
        )

    if specialty:
        query = query.where(
            Doctor.specialty.has(
                name=specialty
            )
        )

    doctors = (
        await session.scalars(
            query
            .order_by(
                Doctor.full_name
            )
            .limit(limit)
        )
    ).unique().all()

    return [
        {
            "id": str(doctor.id),
            "full_name": doctor.full_name,
            "gender": doctor.gender,
            "qualification":
                doctor.qualification,
            "experience_years":
                doctor.experience_years,
            "specialty":
                doctor.specialty.name
                if doctor.specialty
                else None,
            "clinic_name":
                doctor.clinic_name,
            "clinic_location":
                doctor.clinic_location,
            "consultation_fee":
                float(
                    doctor.consultation_fee
                ),
            "hospital_id":
                str(hospital.id),
            "hospital_slug":
                hospital.slug,
        }
        for doctor in doctors
    ]


@router.get(
    "/{hospital_slug}/doctors/{doctor_id}/slots"
)
async def doctor_slots(
    hospital_slug: str,
    doctor_id: uuid.UUID,
    days: int = Query(
        default=30,
        ge=1,
        le=60,
    ),
    session: AsyncSession = Depends(
        get_session
    ),
):
    hospital = await resolve_hospital(
        session,
        hospital_slug,
    )

    await require_doctor_membership(
        session,
        hospital.id,
        doctor_id,
    )

    today = date.today()

    slots = (
        await session.scalars(
            select(DoctorSlot)
            .where(
                DoctorSlot.doctor_id
                == doctor_id,
                DoctorSlot.slot_date
                >= today,
                DoctorSlot.slot_date
                <= today
                + timedelta(days=days),
                DoctorSlot.is_enabled.is_(True),
                DoctorSlot.is_available
                .is_(True),
            )
            .order_by(
                DoctorSlot.slot_date,
                DoctorSlot.start_time,
            )
        )
    ).all()

    return [
        {
            "id": str(slot.id),
            "doctor_id":
                str(slot.doctor_id),
            "slot_date":
                slot.slot_date.isoformat(),
            "start_time":
                slot.start_time.isoformat(),
            "is_available":
                slot.is_available,
        }
        for slot in slots
    ]


@router.get(
    "/{hospital_slug}"
)
async def hospital_widget_config(
    hospital_slug: str,
    session: AsyncSession = Depends(
        get_session
    ),
):
    hospital = await resolve_hospital(
        session,
        hospital_slug,
    )

    doctor_count = len(
        (
            await session.scalars(
                select(
                    HospitalDoctor.doctor_id
                ).where(
                    HospitalDoctor.hospital_id
                    == hospital.id
                )
            )
        ).all()
    )

    return {
        "id": str(hospital.id),
        "slug": hospital.slug,
        "name": hospital.name,
        "status": hospital.status,
        "timezone": hospital.timezone,
        "doctor_count": doctor_count,
    }
