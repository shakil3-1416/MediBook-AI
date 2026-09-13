from __future__ import annotations

import json
import uuid
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.doctor import Doctor, Specialty
from app.models.hospital import HospitalDoctor
from app.models.schedule import DoctorSlot


VALID_SOURCE_MODES = {
    "managed",
    "connected",
    "hybrid",
}


class HospitalDoctorRegistryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_doctors(
        self,
        *,
        hospital_id: UUID,
        include_inactive: bool = False,
    ) -> list[tuple[Doctor, HospitalDoctor]]:
        query = (
            select(
                Doctor,
                HospitalDoctor,
            )
            .join(
                HospitalDoctor,
                HospitalDoctor.doctor_id == Doctor.id,
            )
            .options(
                selectinload(Doctor.specialty)
            )
            .where(
                HospitalDoctor.hospital_id == hospital_id,
            )
            .order_by(
                Doctor.full_name,
            )
        )

        if not include_inactive:
            query = query.where(
                HospitalDoctor.is_active.is_(True),
            )

        result = await self.session.execute(query)

        return [
            (doctor, hospital_doctor)
            for doctor, hospital_doctor in result.all()
        ]

    async def hospital_doctor(
        self,
        *,
        hospital_id: UUID,
        doctor_id: UUID,
    ) -> HospitalDoctor | None:
        return await self.session.scalar(
            select(HospitalDoctor).where(
                HospitalDoctor.hospital_id == hospital_id,
                HospitalDoctor.doctor_id == doctor_id,
            )
        )

    @staticmethod
    def validate_source_mode(source_mode: str) -> str:
        normalized = source_mode.strip().lower()

        if normalized not in VALID_SOURCE_MODES:
            raise ValueError(
                "source_mode must be managed, connected, or hybrid"
            )

        return normalized

    @staticmethod
    def validate_external_identity(
        *,
        source_mode: str,
        external_doctor_id: str | None,
    ) -> None:
        if (
            source_mode == "connected"
            and not (
                external_doctor_id
                and external_doctor_id.strip()
            )
        ):
            raise ValueError(
                "Connected doctors require external_doctor_id"
            )


    async def doctor_pair(
        self,
        *,
        hospital_id: UUID,
        doctor_id: UUID,
    ) -> tuple[Doctor, HospitalDoctor] | None:
        result = await self.session.execute(
            select(
                Doctor,
                HospitalDoctor,
            )
            .join(
                HospitalDoctor,
                HospitalDoctor.doctor_id == Doctor.id,
            )
            .options(
                selectinload(Doctor.specialty)
            )
            .where(
                HospitalDoctor.hospital_id == hospital_id,
                HospitalDoctor.doctor_id == doctor_id,
            )
        )

        return result.first()

    async def specialty_exists(
        self,
        specialty_id: UUID,
    ) -> bool:
        value = await self.session.scalar(
            select(Specialty.id).where(
                Specialty.id == specialty_id
            )
        )

        return value is not None

    async def hospital_link_count(
        self,
        *,
        doctor_id: UUID,
    ) -> int:
        value = await self.session.scalar(
            select(
                func.count(HospitalDoctor.id)
            ).where(
                HospitalDoctor.doctor_id == doctor_id
            )
        )

        return int(value or 0)

    async def future_active_appointment_count(
        self,
        *,
        hospital_id: UUID,
        doctor_id: UUID,
    ) -> int:
        value = await self.session.scalar(
            select(
                func.count(Appointment.id)
            )
            .join(
                DoctorSlot,
                DoctorSlot.id == Appointment.doctor_slot_id,
            )
            .where(
                Appointment.hospital_id == hospital_id,
                Appointment.doctor_id == doctor_id,
                DoctorSlot.slot_date >= date.today(),
                Appointment.status.in_(
                    (
                        "confirmed",
                        "checked_in",
                    )
                ),
            )
        )

        return int(value or 0)

    @staticmethod
    def serialize(
        doctor: Doctor,
        mapping: HospitalDoctor,
    ) -> dict[str, Any]:
        specialty = getattr(
            doctor,
            "specialty",
            None,
        )

        return {
            "hospital_doctor_id": mapping.id,
            "doctor_id": doctor.id,
            "full_name": doctor.full_name,
            "specialty_id": doctor.specialty_id,
            "specialty_name": (
                specialty.name
                if specialty
                else None
            ),
            "gender": doctor.gender,
            "qualification": doctor.qualification,
            "experience_years": doctor.experience_years,
            "clinic_name": mapping.clinic_name,
            "clinic_location": mapping.clinic_location,
            "consultation_fee": mapping.consultation_fee,
            "source_mode": mapping.source_mode,
            "external_doctor_id": mapping.external_doctor_id,
            "is_active": mapping.is_active,
            "public_profile": dict(
                mapping.public_profile or {}
            ),
            "operational_metadata": dict(
                mapping.operational_metadata or {}
            ),
        }

    async def audit(
        self,
        *,
        hospital_id: UUID,
        actor_user_id: UUID | None,
        doctor_id: UUID,
        action: str,
        before_state: dict[str, Any],
        after_state: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        statement = (
            "INSERT INTO hospital_operations_audit ("
            "id, hospital_id, actor_user_id, entity_type, entity_id, "
            "action, before_state, after_state, metadata, created_at"
            ") VALUES ("
            ":id, :hospital_id, :actor_user_id, :entity_type, "
            ":entity_id, :action, CAST(:before_state AS jsonb), "
            "CAST(:after_state AS jsonb), CAST(:metadata AS jsonb), "
            "now()"
            ")"
        )

        await self.session.execute(
            text(statement),
            {
                "id": str(uuid.uuid4()),
                "hospital_id": str(hospital_id),
                "actor_user_id": (
                    str(actor_user_id)
                    if actor_user_id
                    else None
                ),
                "entity_type": "doctor",
                "entity_id": str(doctor_id),
                "action": action,
                "before_state": json.dumps(
                    before_state,
                    default=str,
                ),
                "after_state": json.dumps(
                    after_state,
                    default=str,
                ),
                "metadata": json.dumps(
                    metadata or {},
                    default=str,
                ),
            },
        )
