from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.hospital_doctor_registry import (
    _actor_id,
    _hospital_access,
)
from app.core.auth import CurrentUser
from app.core.database import get_db_session
from app.models.hospital import HospitalIntegration
from app.services.integration_center import (
    IntegrationCenter,
)


router = APIRouter(
    prefix="/hospital-operations",
    tags=["hospital-integrations"],
)


class IntegrationCreate(BaseModel):
    provider: str = Field(
        min_length=1,
        max_length=64,
    )

    integration_type: str = Field(
        default="custom",
        min_length=1,
        max_length=64,
    )

    source_mode: str = "managed"

    ownership: dict = Field(
        default_factory=dict
    )

    config: dict = Field(
        default_factory=dict
    )


class IntegrationUpdate(BaseModel):
    integration_type: str | None = None
    source_mode: str | None = None
    ownership: dict | None = None
    config: dict | None = None
    is_active: bool | None = None


@router.get(
    "/{hospital_slug}/integrations"
)
async def list_integrations(
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

    center = IntegrationCenter(
        session
    )

    integrations = await center.list(
        hospital.id
    )

    return {
        "hospital": {
            "id": hospital.id,
            "slug": hospital.slug,
            "name": hospital.name,
        },
        "count": len(integrations),
        "integrations": [
            center.serialize(item)
            for item in integrations
        ],
    }


@router.post(
    "/{hospital_slug}/integrations",
    status_code=status.HTTP_201_CREATED,
)
async def create_integration(
    hospital_slug: str,
    payload: IntegrationCreate,
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

    center = IntegrationCenter(
        session
    )

    try:
        ownership = center.validate_mode(
            payload.source_mode,
            payload.ownership,
        )

        integration = HospitalIntegration(
            hospital_id=hospital.id,
            provider=payload.provider.strip().lower(),
            integration_type=(
                payload.integration_type.strip().lower()
            ),
            source_mode=payload.source_mode.strip().lower(),
            ownership=ownership,
            config=payload.config,
            status=(
                "connected"
                if payload.source_mode == "managed"
                else "not_configured"
            ),
        )

        session.add(integration)

        await session.flush()

        await center.audit(
            hospital_id=hospital.id,
            actor_user_id=_actor_id(
                current_user
            ),
            integration=integration,
            action="integration.created",
        )

        await session.commit()
        await session.refresh(
            integration
        )

        return center.serialize(
            integration
        )

    except ValueError as exc:
        await session.rollback()

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except IntegrityError as exc:
        await session.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "This provider is already configured "
                "for the hospital."
            ),
        ) from exc


@router.patch(
    "/{hospital_slug}/integrations/{integration_id}"
)
async def update_integration(
    hospital_slug: str,
    integration_id: UUID,
    payload: IntegrationUpdate,
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

    center = IntegrationCenter(
        session
    )

    integration = await center.get(
        hospital.id,
        integration_id,
    )

    if integration is None:
        raise HTTPException(
            status_code=404,
            detail="Integration not found.",
        )

    before = center.serialize(
        integration
    )

    values = payload.model_dump(
        exclude_unset=True
    )

    mode = values.get(
        "source_mode",
        integration.source_mode,
    )

    ownership = values.get(
        "ownership",
        integration.ownership,
    )

    try:
        normalized = center.validate_mode(
            mode,
            ownership,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    for key, value in values.items():
        if key not in {
            "source_mode",
            "ownership",
        }:
            setattr(
                integration,
                key,
                value,
            )

    integration.source_mode = (
        str(mode).lower()
    )

    integration.ownership = normalized

    await center.audit(
        hospital_id=hospital.id,
        actor_user_id=_actor_id(
            current_user
        ),
        integration=integration,
        action="integration.updated",
        before=before,
    )

    await session.commit()
    await session.refresh(
        integration
    )

    return center.serialize(
        integration
    )


@router.post(
    "/{hospital_slug}/integrations/{integration_id}/health-check"
)
async def health_check(
    hospital_slug: str,
    integration_id: UUID,
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

    center = IntegrationCenter(
        session
    )

    integration = await center.get(
        hospital.id,
        integration_id,
    )

    if integration is None:
        raise HTTPException(
            status_code=404,
            detail="Integration not found.",
        )

    before = center.serialize(
        integration
    )

    result = await center.health_check(
        integration
    )

    await center.audit(
        hospital_id=hospital.id,
        actor_user_id=_actor_id(
            current_user
        ),
        integration=integration,
        action="integration.health_checked",
        before=before,
    )

    await session.commit()

    return {
        **center.serialize(
            integration
        ),
        "health": result,
    }
