from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.services.availability_service import AvailabilityService


router = APIRouter()


@router.get("/doctors/{doctor_id}")
async def get_doctor_availability(
    doctor_id: UUID,
    slot_date: Annotated[
        date,
        Query(alias="date"),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
) -> dict:

    service = AvailabilityService(session)

    result = await service.get_doctor_availability(
        doctor_id=doctor_id,
        slot_date=slot_date,
    )

    if not result.get("found"):
        raise HTTPException(
            status_code=404,
            detail="Doctor not found",
        )

    return result
