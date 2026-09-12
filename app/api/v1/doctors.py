from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.schemas.doctor import (
    DoctorResponse,
    DoctorSearchResponse,
)
from app.services.doctor_service import DoctorService


router = APIRouter()


@router.get(
    "",
    response_model=DoctorSearchResponse,
)
async def search_doctors(
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    specialty: Annotated[
        str | None,
        Query(max_length=100),
    ] = None,
    location: Annotated[
        str | None,
        Query(max_length=200),
    ] = None,
    gender: Annotated[
        str | None,
        Query(max_length=30),
    ] = None,
    max_fee: Annotated[
        Decimal | None,
        Query(gt=0),
    ] = None,
    name: Annotated[
        str | None,
        Query(max_length=200),
    ] = None,
) -> DoctorSearchResponse:

    service = DoctorService(
        session
    )

    doctors = (
        await service.search_doctors(
            specialty=specialty,
            location=location,
            gender=gender,
            max_fee=max_fee,
            name=name,
        )
    )

    return DoctorSearchResponse(
        count=len(doctors),
        doctors=[
            DoctorResponse.model_validate(
                doctor
            )
            for doctor in doctors
        ],
    )


@router.get(
    "/{doctor_id}",
    response_model=DoctorResponse,
)
async def get_doctor(
    doctor_id: UUID,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> DoctorResponse:

    service = DoctorService(
        session
    )

    doctor = await service.get_doctor(
        doctor_id
    )

    if doctor is None:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found.",
        )

    return DoctorResponse.model_validate(
        doctor
    )
