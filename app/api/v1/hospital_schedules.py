from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.database import get_db_session
from app.models.control_plane import (
    DoctorScheduleException,
    DoctorScheduleRule,
)
from app.schemas.hospital_schedule_engine import (
    MaterializeRequest,
    ScheduleExceptionCreate,
    ScheduleExceptionUpdate,
    ScheduleRuleCreate,
    ScheduleRuleUpdate,
)
from app.services.hospital_schedule_engine import (
    HospitalScheduleEngine,
    ScheduleConflictError,
    ScheduleOwnershipError,
    ScheduleValidationError,
)
from app.api.v1.hospital_doctor_registry import (
    _actor_id,
    _hospital_access,
)


router = APIRouter(
    prefix="/hospital-operations",
    tags=["hospital-schedules"],
)


def _rule(rule: DoctorScheduleRule) -> dict:
    return {
        "id": str(rule.id),
        "weekday": rule.weekday,
        "start_time": (
            rule.start_time.isoformat()
        ),
        "end_time": (
            rule.end_time.isoformat()
        ),
        "slot_duration_minutes": (
            rule.slot_duration_minutes
        ),
        "capacity": rule.capacity,
        "valid_from": (
            rule.valid_from.isoformat()
            if rule.valid_from
            else None
        ),
        "valid_until": (
            rule.valid_until.isoformat()
            if rule.valid_until
            else None
        ),
        "is_active": rule.is_active,
    }


def _exception(
    item: DoctorScheduleException,
) -> dict:
    return {
        "id": str(item.id),
        "exception_date": (
            item.exception_date.isoformat()
        ),
        "kind": item.kind,
        "start_time": (
            item.start_time.isoformat()
            if item.start_time
            else None
        ),
        "end_time": (
            item.end_time.isoformat()
            if item.end_time
            else None
        ),
        "slot_duration_minutes": (
            item.slot_duration_minutes
        ),
        "capacity": item.capacity,
        "reason": item.reason,
        "is_active": item.is_active,
    }


async def _context(
    *,
    hospital_slug: str,
    doctor_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession,
):
    hospital = await _hospital_access(
        hospital_slug=hospital_slug,
        current_user=current_user,
        session=session,
    )

    engine = HospitalScheduleEngine(
        session
    )

    try:
        mapping = await engine.hospital_doctor(
            hospital_id=hospital.id,
            doctor_id=doctor_id,
        )

    except ScheduleOwnershipError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return hospital, mapping, engine


@router.get(
    "/{hospital_slug}/doctors/{doctor_id}/schedule",
)
async def get_schedule(
    hospital_slug: str,
    doctor_id: UUID,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    hospital, mapping, engine = await _context(
        hospital_slug=hospital_slug,
        doctor_id=doctor_id,
        current_user=current_user,
        session=session,
    )

    rules = await engine.rules(
        hospital_doctor_id=mapping.id
    )

    exceptions = await engine.exceptions(
        hospital_doctor_id=mapping.id
    )

    return {
        "hospital_id": str(hospital.id),
        "doctor_id": str(doctor_id),
        "hospital_doctor_id": str(
            mapping.id
        ),
        "source_mode": (
            mapping.source_mode
        ),
        "editable": (
            mapping.source_mode
            != "connected"
        ),
        "rules": [
            _rule(item)
            for item in rules
        ],
        "exceptions": [
            _exception(item)
            for item in exceptions
        ],
    }


@router.post(
    "/{hospital_slug}/doctors/{doctor_id}/schedule/rules",
    status_code=status.HTTP_201_CREATED,
)
async def create_rule(
    hospital_slug: str,
    doctor_id: UUID,
    payload: ScheduleRuleCreate,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    hospital, mapping, engine = await _context(
        hospital_slug=hospital_slug,
        doctor_id=doctor_id,
        current_user=current_user,
        session=session,
    )

    try:
        engine.assert_local_schedule_writable(
            mapping
        )

        engine.validate_window(
            start_time=payload.start_time,
            end_time=payload.end_time,
            valid_from=payload.valid_from,
            valid_until=payload.valid_until,
        )

        rule = DoctorScheduleRule(
            hospital_doctor_id=mapping.id,
            **payload.model_dump(),
        )

        session.add(rule)

        await session.commit()
        await session.refresh(rule)

        return _rule(rule)

    except (
        ScheduleOwnershipError,
        ScheduleValidationError,
    ) as exc:
        await session.rollback()

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.post(
    "/{hospital_slug}/doctors/{doctor_id}/schedule/exceptions",
    status_code=status.HTTP_201_CREATED,
)
async def create_exception(
    hospital_slug: str,
    doctor_id: UUID,
    payload: ScheduleExceptionCreate,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    hospital, mapping, engine = await _context(
        hospital_slug=hospital_slug,
        doctor_id=doctor_id,
        current_user=current_user,
        session=session,
    )

    try:
        engine.assert_local_schedule_writable(
            mapping
        )

        item = DoctorScheduleException(
            hospital_doctor_id=mapping.id,
            **payload.model_dump(),
        )

        engine.validate_exception(item)

        session.add(item)

        await session.commit()
        await session.refresh(item)

        return _exception(item)

    except (
        ScheduleOwnershipError,
        ScheduleValidationError,
    ) as exc:
        await session.rollback()

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{hospital_slug}/doctors/{doctor_id}/schedule/rules/{rule_id}",
)
async def update_rule(
    hospital_slug: str,
    doctor_id: UUID,
    rule_id: UUID,
    payload: ScheduleRuleUpdate,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    hospital, mapping, engine = await _context(
        hospital_slug=hospital_slug,
        doctor_id=doctor_id,
        current_user=current_user,
        session=session,
    )

    engine.assert_local_schedule_writable(
        mapping
    )

    rule = await session.get(
        DoctorScheduleRule,
        rule_id,
    )

    if (
        rule is None
        or rule.hospital_doctor_id
        != mapping.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Schedule rule not found.",
        )

    values = payload.model_dump(
        exclude_unset=True
    )

    for key, value in values.items():
        setattr(
            rule,
            key,
            value,
        )

    engine.validate_window(
        start_time=rule.start_time,
        end_time=rule.end_time,
        valid_from=rule.valid_from,
        valid_until=rule.valid_until,
    )

    await session.commit()
    await session.refresh(rule)

    return _rule(rule)


@router.patch(
    "/{hospital_slug}/doctors/{doctor_id}/schedule/exceptions/{exception_id}",
)
async def update_exception(
    hospital_slug: str,
    doctor_id: UUID,
    exception_id: UUID,
    payload: ScheduleExceptionUpdate,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    hospital, mapping, engine = await _context(
        hospital_slug=hospital_slug,
        doctor_id=doctor_id,
        current_user=current_user,
        session=session,
    )

    engine.assert_local_schedule_writable(
        mapping
    )

    item = await session.get(
        DoctorScheduleException,
        exception_id,
    )

    if (
        item is None
        or item.hospital_doctor_id
        != mapping.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Schedule exception not found.",
        )

    values = payload.model_dump(
        exclude_unset=True
    )

    for key, value in values.items():
        setattr(
            item,
            key,
            value,
        )

    engine.validate_exception(item)

    await session.commit()
    await session.refresh(item)

    return _exception(item)


@router.post(
    "/{hospital_slug}/doctors/{doctor_id}/schedule/preview",
)
async def preview_schedule(
    hospital_slug: str,
    doctor_id: UUID,
    payload: MaterializeRequest,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    hospital, mapping, engine = await _context(
        hospital_slug=hospital_slug,
        doctor_id=doctor_id,
        current_user=current_user,
        session=session,
    )

    try:
        preview = await engine.preview(
            mapping=mapping,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )

    except ScheduleValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return {
        key: value
        for key, value in preview.items()
        if not key.startswith("_")
    }


@router.post(
    "/{hospital_slug}/doctors/{doctor_id}/schedule/apply",
)
async def apply_schedule(
    hospital_slug: str,
    doctor_id: UUID,
    payload: MaterializeRequest,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    hospital, mapping, engine = await _context(
        hospital_slug=hospital_slug,
        doctor_id=doctor_id,
        current_user=current_user,
        session=session,
    )

    try:
        result = await engine.apply(
            mapping=mapping,
            hospital_id=hospital.id,
            actor_user_id=_actor_id(
                current_user
            ),
            start_date=payload.start_date,
            end_date=payload.end_date,
        )

        await session.commit()

        return result

    except ScheduleConflictError as exc:
        await session.rollback()

        raise HTTPException(
            status_code=409,
            detail={
                "message": str(exc),
                "conflicts": exc.conflicts,
            },
        ) from exc

    except (
        ScheduleOwnershipError,
        ScheduleValidationError,
    ) as exc:
        await session.rollback()

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
