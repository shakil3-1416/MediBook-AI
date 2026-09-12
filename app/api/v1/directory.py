from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import (
    String,
    and_,
    cast,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db_session
from app.models.doctor import Doctor
from app.models.doctor_slot import DoctorSlot
from app.models.specialty import Specialty


router = APIRouter(
    prefix="/directory",
    tags=["directory"],
)


def city_expression():
    return func.trim(
        func.split_part(
            Doctor.clinic_location,
            ",",
            2,
        )
    )


def area_expression():
    return func.trim(
        func.split_part(
            Doctor.clinic_location,
            ",",
            1,
        )
    )


def serialize_doctor(
    doctor: Doctor,
) -> dict:

    return {
        "id":
            str(doctor.id),

        "full_name":
            doctor.full_name,

        "gender":
            doctor.gender,

        "qualification":
            doctor.qualification,

        "experience_years":
            doctor.experience_years,

        "specialty": {
            "id":
                str(
                    doctor.specialty.id
                ),

            "name":
                doctor.specialty.name,
        },

        "clinic_name":
            doctor.clinic_name,

        "clinic_location":
            doctor.clinic_location,

        "consultation_fee":
            float(
                doctor.consultation_fee
            ),

        "is_active":
            doctor.is_active,
    }


@router.get("/facets")
async def directory_facets(
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    city: str | None = None,
) -> dict:

    city_expr = city_expression()
    area_expr = area_expression()

    city_rows = (
        await session.execute(
            select(
                city_expr.label(
                    "city"
                ),
                func.count(
                    Doctor.id
                ).label(
                    "count"
                ),
            )
            .where(
                Doctor.is_active
                .is_(True)
            )
            .group_by(
                city_expr
            )
            .order_by(
                func.count(
                    Doctor.id
                ).desc()
            )
        )
    ).all()


    hospital_stmt = (
        select(
            Doctor.clinic_name.label(
                "name"
            ),
            func.count(
                Doctor.id
            ).label(
                "count"
            ),
        )
        .where(
            Doctor.is_active
            .is_(True)
        )
    )


    if city:

        hospital_stmt = (
            hospital_stmt.where(
                func.lower(
                    city_expr()
                )
                == city.strip().lower()
            )
        )


    hospital_rows = (
        await session.execute(
            hospital_stmt
            .group_by(
                Doctor.clinic_name
            )
            .order_by(
                Doctor.clinic_name.asc()
            )
        )
    ).all()


    specialty_rows = (
        await session.execute(
            select(
                Specialty.name,
                func.count(
                    Doctor.id
                ),
            )
            .join(
                Doctor,
                Doctor.specialty_id
                == Specialty.id,
            )
            .where(
                Doctor.is_active
                .is_(True)
            )
            .group_by(
                Specialty.name
            )
            .order_by(
                Specialty.name.asc()
            )
        )
    ).all()


    area_stmt = (
        select(
            area_expr.label(
                "area"
            ),
            func.count(
                Doctor.id
            ).label(
                "count"
            ),
        )
        .where(
            Doctor.is_active
            .is_(True)
        )
    )


    if city:

        area_stmt = (
            area_stmt.where(
                func.lower(
                    city_expr
                )
                == city.strip().lower()
            )
        )


    area_rows = (
        await session.execute(
            area_stmt
            .group_by(
                area_expr
            )
            .order_by(
                area_expr.asc()
            )
        )
    ).all()


    return {
        "cities": [
            {
                "name":
                    row.city,

                "count":
                    row.count,
            }
            for row
            in city_rows
            if row.city
        ],

        "areas": [
            {
                "name":
                    row.area,

                "count":
                    row.count,
            }
            for row
            in area_rows
            if row.area
        ],

        "hospitals": [
            {
                "name":
                    row.name,

                "count":
                    row.count,
            }
            for row
            in hospital_rows
            if row.name
        ],

        "specialties": [
            {
                "name":
                    name,

                "count":
                    count,
            }
            for (
                name,
                count,
            ) in specialty_rows
        ],
    }


@router.get("/doctors")
async def search_directory(
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    q: str | None = None,
    city: str | None = None,
    area: str | None = None,
    specialty: str | None = None,
    hospital: str | None = None,
    gender: str | None = None,
    max_fee: float | None = None,
    min_experience: int | None = None,
    page: Annotated[
        int,
        Query(
            ge=1,
        ),
    ] = 1,
    page_size: Annotated[
        int,
        Query(
            ge=1,
            le=50,
        ),
    ] = 18,
) -> dict:

    city_expr = city_expression()
    area_expr = area_expression()

    filters = [
        Doctor.is_active
        .is_(True)
    ]


    if q:

        term = (
            "%"
            + q.strip().lower()
            + "%"
        )

        filters.append(
            or_(
                func.lower(
                    Doctor.full_name
                ).like(
                    term
                ),

                func.lower(
                    Doctor.clinic_name
                ).like(
                    term
                ),

                func.lower(
                    Doctor.clinic_location
                ).like(
                    term
                ),

                func.lower(
                    Doctor.qualification
                ).like(
                    term
                ),

                func.lower(
                    Specialty.name
                ).like(
                    term
                ),
            )
        )


    if city:

        filters.append(
            func.lower(
                city_expr
            )
            == city.strip().lower()
        )


    if area:

        filters.append(
            func.lower(
                area_expr
            )
            == area.strip().lower()
        )


    if specialty:

        filters.append(
            func.lower(
                Specialty.name
            )
            == specialty.strip().lower()
        )


    if hospital:

        filters.append(
            func.lower(
                Doctor.clinic_name
            )
            == hospital.strip().lower()
        )


    if gender:

        filters.append(
            func.lower(
                cast(
                    Doctor.gender,
                    String,
                )
            )
            == gender.strip().lower()
        )


    if max_fee is not None:

        filters.append(
            Doctor.consultation_fee
            <= max_fee
        )


    if min_experience is not None:

        filters.append(
            Doctor.experience_years
            >= min_experience
        )


    count_stmt = (
        select(
            func.count(
                Doctor.id
            )
        )
        .join(
            Specialty,
            Specialty.id
            == Doctor.specialty_id,
        )
        .where(
            and_(
                *filters
            )
        )
    )


    total = (
        await session.scalar(
            count_stmt
        )
        or 0
    )


    stmt = (
        select(
            Doctor
        )
        .join(
            Specialty,
            Specialty.id
            == Doctor.specialty_id,
        )
        .options(
            selectinload(
                Doctor.specialty
            )
        )
        .where(
            and_(
                *filters
            )
        )
        .order_by(
            Doctor.full_name.asc()
        )
        .offset(
            (
                page - 1
            )
            * page_size
        )
        .limit(
            page_size
        )
    )


    doctors = (
        await session.scalars(
            stmt
        )
    ).all()


    pages = (
        (
            total
            + page_size
            - 1
        )
        // page_size
        if total
        else 0
    )


    return {
        "count":
            total,

        "page":
            page,

        "page_size":
            page_size,

        "pages":
            pages,

        "doctors": [
            serialize_doctor(
                doctor
            )
            for doctor
            in doctors
        ],
    }


@router.get("/doctors/{doctor_id}")
async def doctor_profile(
    doctor_id: UUID,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> dict:

    doctor = await session.scalar(
        select(
            Doctor
        )
        .options(
            selectinload(
                Doctor.specialty
            )
        )
        .where(
            Doctor.id
            == doctor_id,
            Doctor.is_active
            .is_(True),
        )
    )


    if doctor is None:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found.",
        )


    slots = (
        await session.scalars(
            select(
                DoctorSlot
            )
            .where(
                DoctorSlot.doctor_id
                == doctor.id,

                DoctorSlot.slot_date
                >= date.today(),

                DoctorSlot.is_available
                .is_(True),
            )
            .order_by(
                DoctorSlot.slot_date.asc(),
                DoctorSlot.start_time.asc(),
            )
            .limit(
                20
            )
        )
    ).all()


    return {
        "doctor":
            serialize_doctor(
                doctor
            ),

        "next_available_slots": [
            {
                "id":
                    str(slot.id),

                "date":
                    slot.slot_date.isoformat(),

                "time":
                    slot.start_time.strftime(
                        "%H:%M"
                    ),
            }
            for slot
            in slots
        ],
    }
