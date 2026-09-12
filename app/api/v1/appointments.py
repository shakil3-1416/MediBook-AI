from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
)
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.database import get_db_session
from app.services.appointment_service import (
    AppointmentNotFoundError,
    AppointmentService,
    AppointmentStateError,
    SlotNotFoundError,
    SlotUnavailableError,
)
from app.services.hospital_context import (
    HospitalContextError,
    resolve_hospital,
)


router = APIRouter()


class CancelAppointmentRequest(BaseModel):
    confirmation_code: str


class RescheduleAppointmentRequest(BaseModel):
    confirmation_code: str
    new_slot_id: UUID


async def _request_hospital(
    session: AsyncSession,
    hospital_slug: str | None,
):
    if not hospital_slug:
        raise HTTPException(
            status_code=400,
            detail="Hospital context is required.",
        )

    try:
        return await resolve_hospital(
            session,
            hospital_slug=hospital_slug,
        )

    except HospitalContextError as exc:
        raise HTTPException(
            status_code=404,
            detail="Hospital workspace not found.",
        ) from exc


@router.get("")
async def list_appointments(
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    include_cancelled: bool = False,
    hospital_slug: Annotated[
        str | None,
        Header(
            alias="X-MediBook-Hospital-Slug",
        ),
    ] = None,
) -> dict:

    hospital = await _request_hospital(
        session,
        hospital_slug,
    )

    service = AppointmentService(
        session
    )

    appointments = (
        await service.list_for_phone(
            phone=current_user.phone,
            hospital_id=hospital.id,
            include_cancelled=(
                include_cancelled
            ),
        )
    )

    return {
        "count": len(appointments),
        "appointments": appointments,
    }


@router.post("/cancel")
async def cancel_appointment(
    current_user: CurrentUser,
    request: CancelAppointmentRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    hospital_slug: Annotated[
        str | None,
        Header(
            alias="X-MediBook-Hospital-Slug",
        ),
    ] = None,
) -> dict:

    hospital = await _request_hospital(
        session,
        hospital_slug,
    )

    service = AppointmentService(
        session
    )

    try:
        return await service.cancel_appointment(
            confirmation_code=(
                request.confirmation_code
            ),
            patient_phone=(
                current_user.phone
            ),
            hospital_id=hospital.id,
        )

    except AppointmentNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except AppointmentStateError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.post("/reschedule")
async def reschedule_appointment(
    current_user: CurrentUser,
    request: RescheduleAppointmentRequest,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    hospital_slug: Annotated[
        str | None,
        Header(
            alias="X-MediBook-Hospital-Slug",
        ),
    ] = None,
) -> dict:

    hospital = await _request_hospital(
        session,
        hospital_slug,
    )

    service = AppointmentService(
        session
    )

    try:
        return await service.reschedule_appointment(
            confirmation_code=(
                request.confirmation_code
            ),
            patient_phone=(
                current_user.phone
            ),
            hospital_id=hospital.id,
            new_slot_id=(
                request.new_slot_id
            ),
        )

    except AppointmentNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except (
        AppointmentStateError,
        SlotUnavailableError,
        SlotNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
