from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.hospital_doctor_registry import (
    _actor_id,
    _hospital_access,
)
from app.core.auth import CurrentUser
from app.core.database import get_db_session
from app.models.control_plane import (
    HospitalOperationsAudit,
)
from app.models.hospital import (
    HospitalMembership,
)


router = APIRouter(
    prefix="/hospital-operations",
    tags=["hospital-admin"],
)


class HospitalSettingsUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    timezone: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
    )


@router.get(
    "/{hospital_slug}/audit"
)
async def audit_log(
    hospital_slug: str,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
):
    hospital = await _hospital_access(
        hospital_slug=hospital_slug,
        current_user=current_user,
        session=session,
    )

    rows = (
        await session.execute(
            select(
                HospitalOperationsAudit
            )
            .where(
                HospitalOperationsAudit.hospital_id
                == hospital.id
            )
            .order_by(
                HospitalOperationsAudit.created_at.desc()
            )
            .limit(limit)
        )
    ).scalars().all()

    return {
        "count": len(rows),
        "events": [
            {
                "id": item.id,
                "actor_user_id":
                    item.actor_user_id,
                "entity_type":
                    item.entity_type,
                "entity_id":
                    item.entity_id,
                "action":
                    item.action,
                "metadata":
                    item.metadata_json,
                "created_at":
                    item.created_at,
            }
            for item in rows
        ],
    }


@router.get(
    "/{hospital_slug}/staff"
)
async def hospital_staff(
    hospital_slug: str,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    hospital = await _hospital_access(
        hospital_slug=hospital_slug,
        current_user=current_user,
        session=session,
    )

    rows = (
        await session.execute(
            select(
                HospitalMembership
            )
            .where(
                HospitalMembership.hospital_id
                == hospital.id
            )
            .order_by(
                HospitalMembership.created_at
            )
        )
    ).scalars().all()

    return {
        "count": len(rows),
        "members": [
            {
                "id": item.id,
                "user_id": item.user_id,
                "role": item.role,
                "is_active": item.is_active,
                "created_at":
                    item.created_at,
            }
            for item in rows
        ],
    }


@router.get(
    "/{hospital_slug}/settings"
)
async def hospital_settings(
    hospital_slug: str,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    hospital = await _hospital_access(
        hospital_slug=hospital_slug,
        current_user=current_user,
        session=session,
    )

    return {
        "id": hospital.id,
        "slug": hospital.slug,
        "name": hospital.name,
        "status": hospital.status,
        "timezone": hospital.timezone,
        "is_active": hospital.is_active,
    }


@router.patch(
    "/{hospital_slug}/settings"
)
async def update_settings(
    hospital_slug: str,
    payload: HospitalSettingsUpdate,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
):
    hospital = await _hospital_access(
        hospital_slug=hospital_slug,
        current_user=current_user,
        session=session,
    )

    before = {
        "name": hospital.name,
        "timezone": hospital.timezone,
    }

    values = payload.model_dump(
        exclude_unset=True
    )

    for key, value in values.items():
        setattr(
            hospital,
            key,
            value.strip()
            if isinstance(value, str)
            else value,
        )

    session.add(
        HospitalOperationsAudit(
            hospital_id=hospital.id,
            actor_user_id=_actor_id(
                current_user
            ),
            entity_type="hospital",
            entity_id=hospital.id,
            action="hospital.settings_updated",
            before_state=before,
            after_state={
                "name": hospital.name,
                "timezone":
                    hospital.timezone,
            },
            metadata_json={},
        )
    )

    await session.commit()
    await session.refresh(
        hospital
    )

    return {
        "id": hospital.id,
        "slug": hospital.slug,
        "name": hospital.name,
        "timezone": hospital.timezone,
    }
