from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.database import get_db_session
from app.models.doctor import Doctor
from app.models.hospital import (
    Hospital,
    HospitalDoctor,
    HospitalMembership,
)
from app.schemas.hospital_doctor_registry import (
    DoctorActivationUpdate,
    DoctorCreate,
    DoctorRegistryItem,
    DoctorRegistryList,
    DoctorUpdate,
)
from app.services.hospital_doctor_registry import (
    HospitalDoctorRegistryService,
)


router = APIRouter(
    prefix="/hospital-operations",
    tags=["hospital-doctor-registry"],
)


PLATFORM_ROLES = {
    "platform_admin",
    "super_admin",
    "admin",
}


async def _hospital_access(
    *,
    hospital_slug: str,
    current_user: CurrentUser,
    session: AsyncSession,
) -> Hospital:
    hospital = await session.scalar(
        select(
            Hospital
        ).where(
            Hospital.slug == hospital_slug,
            Hospital.is_active.is_(True),
        )
    )

    if hospital is None:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found.",
        )

    role = str(
        getattr(
            current_user,
            "role",
            "",
        )
        or ""
    ).lower()

    if role in PLATFORM_ROLES:
        return hospital

    user_id = getattr(
        current_user,
        "id",
        None,
    )

    if user_id is None:
        raise HTTPException(
            status_code=403,
            detail="Hospital dashboard access denied.",
        )

    membership = await session.scalar(
        select(
            HospitalMembership
        ).where(
            HospitalMembership.hospital_id
            == hospital.id,
            HospitalMembership.user_id
            == user_id,
            HospitalMembership.is_active.is_(True),
        )
    )

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this hospital.",
        )

    return hospital


def _actor_id(
    current_user: CurrentUser,
) -> UUID | None:
    value = getattr(
        current_user,
        "id",
        None,
    )

    if isinstance(
        value,
        UUID,
    ):
        return value

    try:
        return (
            UUID(
                str(
                    value
                )
            )
            if value
            else None
        )

    except (
        TypeError,
        ValueError,
    ):
        return None


@router.get(
    "/{hospital_slug}/doctors",
    response_model=DoctorRegistryList,
)
async def list_hospital_doctors(
    hospital_slug: str,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(
            get_db_session
        ),
    ],
    include_inactive: bool = Query(
        default=False
    ),
):
    hospital = await _hospital_access(
        hospital_slug=hospital_slug,
        current_user=current_user,
        session=session,
    )

    service = HospitalDoctorRegistryService(
        session
    )

    pairs = await service.list_doctors(
        hospital_id=hospital.id,
        include_inactive=include_inactive,
    )

    doctors = [
        DoctorRegistryItem(
            **service.serialize(
                doctor,
                mapping,
            )
        )
        for doctor, mapping
        in pairs
    ]

    return DoctorRegistryList(
        count=len(
            doctors
        ),
        doctors=doctors,
    )


@router.post(
    "/{hospital_slug}/doctors",
    response_model=DoctorRegistryItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_hospital_doctor(
    hospital_slug: str,
    payload: DoctorCreate,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(
            get_db_session
        ),
    ],
):
    hospital = await _hospital_access(
        hospital_slug=hospital_slug,
        current_user=current_user,
        session=session,
    )

    service = HospitalDoctorRegistryService(
        session
    )

    source_mode = service.validate_source_mode(
        payload.source_mode
    )

    external_id = (
        payload.external_doctor_id.strip()
        if payload.external_doctor_id
        else None
    )

    try:
        service.validate_external_identity(
            source_mode=source_mode,
            external_doctor_id=external_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(
                exc
            ),
        ) from exc

    if not await service.specialty_exists(
        payload.specialty_id
    ):
        raise HTTPException(
            status_code=422,
            detail="Specialty does not exist.",
        )

    doctor = Doctor(
        full_name=payload.full_name.strip(),
        gender=(
            payload.gender.strip().lower()
            if payload.gender
            else None
        ),
        qualification=(
            payload.qualification.strip()
            if payload.qualification
            else None
        ),
        experience_years=payload.experience_years,
        specialty_id=payload.specialty_id,
        clinic_name=payload.clinic_name.strip(),
        clinic_location=payload.clinic_location.strip(),
        consultation_fee=payload.consultation_fee,
        is_active=True,
    )

    session.add(
        doctor
    )

    try:
        await session.flush()

        mapping = HospitalDoctor(
            hospital_id=hospital.id,
            doctor_id=doctor.id,
            is_active=True,
            source_mode=source_mode,
            external_doctor_id=external_id,
            clinic_name=payload.clinic_name.strip(),
            clinic_location=payload.clinic_location.strip(),
            consultation_fee=payload.consultation_fee,
            public_profile=payload.public_profile,
            operational_metadata=payload.operational_metadata,
        )

        session.add(
            mapping
        )

        await session.flush()

        pair = await service.doctor_pair(
            hospital_id=hospital.id,
            doctor_id=doctor.id,
        )

        if pair is None:
            raise RuntimeError(
                "Created doctor could not be reloaded."
            )

        created_doctor, created_mapping = pair

        after = service.serialize(
            created_doctor,
            created_mapping,
        )

        await service.audit(
            hospital_id=hospital.id,
            actor_user_id=_actor_id(
                current_user
            ),
            doctor_id=doctor.id,
            action="doctor.created",
            before_state={},
            after_state=after,
            metadata={
                "source_mode":
                    source_mode,
            },
        )

        await session.commit()

        return DoctorRegistryItem(
            **after
        )

    except IntegrityError as exc:
        await session.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Doctor registry conflict. "
                "The external doctor identifier may already exist."
            ),
        ) from exc


@router.patch(
    "/{hospital_slug}/doctors/{doctor_id}",
    response_model=DoctorRegistryItem,
)
async def update_hospital_doctor(
    hospital_slug: str,
    doctor_id: UUID,
    payload: DoctorUpdate,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(
            get_db_session
        ),
    ],
):
    hospital = await _hospital_access(
        hospital_slug=hospital_slug,
        current_user=current_user,
        session=session,
    )

    service = HospitalDoctorRegistryService(
        session
    )

    pair = await service.doctor_pair(
        hospital_id=hospital.id,
        doctor_id=doctor_id,
    )

    if pair is None:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found in this hospital.",
        )

    doctor, mapping = pair

    data = payload.model_dump(
        exclude_unset=True
    )

    non_nullable = {
        "full_name",
        "specialty_id",
        "experience_years",
        "clinic_name",
        "clinic_location",
        "consultation_fee",
        "source_mode",
    }

    invalid_nulls = [
        key
        for key in non_nullable
        if key in data
        and data[key] is None
    ]

    if invalid_nulls:
        raise HTTPException(
            status_code=422,
            detail=(
                "These fields cannot be null: "
                + ", ".join(
                    sorted(
                        invalid_nulls
                    )
                )
            ),
        )

    new_mode = service.validate_source_mode(
        str(
            data.get(
                "source_mode",
                mapping.source_mode,
            )
        )
    )

    external_id_value = data.get(
        "external_doctor_id",
        mapping.external_doctor_id,
    )

    external_id = (
        external_id_value.strip()
        if isinstance(
            external_id_value,
            str,
        )
        and external_id_value.strip()
        else None
    )

    try:
        service.validate_external_identity(
            source_mode=new_mode,
            external_doctor_id=external_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(
                exc
            ),
        ) from exc

    externally_owned_fields = {
        "full_name",
        "specialty_id",
        "gender",
        "qualification",
        "experience_years",
        "clinic_name",
        "clinic_location",
        "consultation_fee",
        "public_profile",
    }

    if (
        mapping.source_mode
        == "connected"
        and new_mode
        == "connected"
        and externally_owned_fields.intersection(
            data
        )
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Connected doctor profile fields are externally managed. "
                "Change the source mode or update the upstream system."
            ),
        )

    specialty_id = data.get(
        "specialty_id"
    )

    if (
        specialty_id is not None
        and not await service.specialty_exists(
            specialty_id
        )
    ):
        raise HTTPException(
            status_code=422,
            detail="Specialty does not exist.",
        )

    global_identity_fields = {
        "full_name",
        "specialty_id",
        "gender",
        "qualification",
        "experience_years",
    }

    if global_identity_fields.intersection(data):
        link_count = await service.hospital_link_count(
            doctor_id=doctor_id,
        )

        if link_count > 1:
            raise HTTPException(
                status_code=409,
                detail=(
                    "This doctor is linked to multiple hospitals. "
                    "Global identity fields cannot be changed from "
                    "a single hospital workspace."
                ),
            )

    before = service.serialize(
        doctor,
        mapping,
    )

    global_fields = {
        "full_name",
        "specialty_id",
        "gender",
        "qualification",
        "experience_years",
    }

    for field in global_fields:
        if field in data:
            value = data[
                field
            ]

            if (
                isinstance(
                    value,
                    str,
                )
                and field
                not in {
                    "gender",
                }
            ):
                value = value.strip()

            if (
                field == "gender"
                and isinstance(
                    value,
                    str,
                )
            ):
                value = value.strip().lower()

            setattr(
                doctor,
                field,
                value,
            )

    hospital_fields = {
        "clinic_name",
        "clinic_location",
        "consultation_fee",
    }

    for field in hospital_fields:
        if field in data:
            value = data[
                field
            ]

            if isinstance(
                value,
                str,
            ):
                value = value.strip()

            setattr(
                mapping,
                field,
                value,
            )

            if new_mode in {
                "managed",
                "hybrid",
            }:
                setattr(
                    doctor,
                    field,
                    value,
                )

    if "public_profile" in data:
        mapping.public_profile = (
            data[
                "public_profile"
            ]
            or {}
        )

    if "operational_metadata" in data:
        mapping.operational_metadata = (
            data[
                "operational_metadata"
            ]
            or {}
        )

    mapping.source_mode = new_mode
    mapping.external_doctor_id = external_id
    mapping.updated_at = datetime.now(
        timezone.utc
    )

    try:
        await session.flush()

        refreshed = await service.doctor_pair(
            hospital_id=hospital.id,
            doctor_id=doctor_id,
        )

        if refreshed is None:
            raise RuntimeError(
                "Updated doctor could not be reloaded."
            )

        updated_doctor, updated_mapping = refreshed

        after = service.serialize(
            updated_doctor,
            updated_mapping,
        )

        await service.audit(
            hospital_id=hospital.id,
            actor_user_id=_actor_id(
                current_user
            ),
            doctor_id=doctor_id,
            action="doctor.updated",
            before_state=before,
            after_state=after,
            metadata={
                "changed_fields":
                    sorted(
                        data.keys()
                    ),
            },
        )

        await session.commit()

        return DoctorRegistryItem(
            **after
        )

    except IntegrityError as exc:
        await session.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Doctor registry conflict. "
                "The external doctor identifier may already exist."
            ),
        ) from exc


@router.patch(
    "/{hospital_slug}/doctors/{doctor_id}/activation",
    response_model=DoctorRegistryItem,
)
async def set_hospital_doctor_activation(
    hospital_slug: str,
    doctor_id: UUID,
    payload: DoctorActivationUpdate,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(
            get_db_session
        ),
    ],
):
    hospital = await _hospital_access(
        hospital_slug=hospital_slug,
        current_user=current_user,
        session=session,
    )

    service = HospitalDoctorRegistryService(
        session
    )

    pair = await service.doctor_pair(
        hospital_id=hospital.id,
        doctor_id=doctor_id,
    )

    if pair is None:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found in this hospital.",
        )

    doctor, mapping = pair

    if (
        mapping.is_active
        and not payload.is_active
    ):
        conflicts = (
            await service.future_active_appointment_count(
                hospital_id=hospital.id,
                doctor_id=doctor_id,
            )
        )

        if conflicts:
            raise HTTPException(
                status_code=409,
                detail={
                    "message":
                        (
                            "Doctor cannot be deactivated while "
                            "active future appointments exist."
                        ),

                    "future_appointment_count":
                        conflicts,
                },
            )

    before = service.serialize(
        doctor,
        mapping,
    )

    mapping.is_active = payload.is_active
    mapping.updated_at = datetime.now(
        timezone.utc
    )

    await session.flush()

    refreshed = await service.doctor_pair(
        hospital_id=hospital.id,
        doctor_id=doctor_id,
    )

    if refreshed is None:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found in this hospital.",
        )

    updated_doctor, updated_mapping = refreshed

    after = service.serialize(
        updated_doctor,
        updated_mapping,
    )

    await service.audit(
        hospital_id=hospital.id,
        actor_user_id=_actor_id(
            current_user
        ),
        doctor_id=doctor_id,
        action=(
            "doctor.activated"
            if payload.is_active
            else "doctor.deactivated"
        ),
        before_state=before,
        after_state=after,
    )

    await session.commit()

    return DoctorRegistryItem(
        **after
    )
