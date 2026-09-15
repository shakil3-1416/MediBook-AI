from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.control_plane import (
    DoctorScheduleException,
    DoctorScheduleRule,
    HospitalOperationsAudit,
)
from app.models.hospital import HospitalDoctor
from app.models.schedule import DoctorSlot


ACTIVE_APPOINTMENT_STATUSES = {
    "confirmed",
    "checked_in",
}


class ScheduleEngineError(Exception):
    pass


class ScheduleOwnershipError(ScheduleEngineError):
    pass


class ScheduleValidationError(ScheduleEngineError):
    pass


class ScheduleConflictError(ScheduleEngineError):
    def __init__(self, conflicts: list[dict]):
        super().__init__(
            "Schedule change conflicts with existing appointments."
        )
        self.conflicts = conflicts


class HospitalScheduleEngine:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def hospital_doctor(
        self,
        *,
        hospital_id: UUID,
        doctor_id: UUID,
    ) -> HospitalDoctor:
        mapping = await self.session.scalar(
            select(HospitalDoctor).where(
                HospitalDoctor.hospital_id == hospital_id,
                HospitalDoctor.doctor_id == doctor_id,
                HospitalDoctor.is_active.is_(True),
            )
        )

        if mapping is None:
            raise ScheduleOwnershipError(
                "Doctor is not active for this hospital."
            )

        return mapping

    @staticmethod
    def assert_local_schedule_writable(
        mapping: HospitalDoctor,
    ) -> None:
        if mapping.source_mode == "connected":
            raise ScheduleOwnershipError(
                "This doctor schedule is externally managed."
            )

    @staticmethod
    def validate_window(
        *,
        start_time,
        end_time,
        valid_from=None,
        valid_until=None,
    ) -> None:
        if start_time >= end_time:
            raise ScheduleValidationError(
                "Schedule start time must be before end time."
            )

        if (
            valid_from is not None
            and valid_until is not None
            and valid_until < valid_from
        ):
            raise ScheduleValidationError(
                "Schedule valid_until cannot precede valid_from."
            )

    @staticmethod
    def validate_exception(
        exception: DoctorScheduleException,
    ) -> None:
        if exception.kind == "override":
            if (
                exception.start_time is None
                or exception.end_time is None
            ):
                raise ScheduleValidationError(
                    "Override requires start_time and end_time."
                )

        if (
            exception.start_time is not None
            and exception.end_time is not None
            and exception.start_time >= exception.end_time
        ):
            raise ScheduleValidationError(
                "Exception start time must be before end time."
            )

    async def rules(
        self,
        *,
        hospital_doctor_id: UUID,
    ) -> list[DoctorScheduleRule]:
        result = await self.session.execute(
            select(DoctorScheduleRule)
            .where(
                DoctorScheduleRule.hospital_doctor_id
                == hospital_doctor_id
            )
            .order_by(
                DoctorScheduleRule.weekday,
                DoctorScheduleRule.start_time,
            )
        )

        return list(
            result.scalars().all()
        )

    async def exceptions(
        self,
        *,
        hospital_doctor_id: UUID,
    ) -> list[DoctorScheduleException]:
        result = await self.session.execute(
            select(DoctorScheduleException)
            .where(
                DoctorScheduleException.hospital_doctor_id
                == hospital_doctor_id
            )
            .order_by(
                DoctorScheduleException.exception_date,
                DoctorScheduleException.start_time,
            )
        )

        return list(
            result.scalars().all()
        )

    async def effective_rules(
        self,
        *,
        hospital_doctor_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[DoctorScheduleRule]:
        result = await self.session.execute(
            select(DoctorScheduleRule).where(
                DoctorScheduleRule.hospital_doctor_id
                == hospital_doctor_id,
                DoctorScheduleRule.is_active.is_(True),
                (
                    DoctorScheduleRule.valid_from.is_(None)
                    | (
                        DoctorScheduleRule.valid_from
                        <= end_date
                    )
                ),
                (
                    DoctorScheduleRule.valid_until.is_(None)
                    | (
                        DoctorScheduleRule.valid_until
                        >= start_date
                    )
                ),
            )
        )

        return list(
            result.scalars().all()
        )

    async def effective_exceptions(
        self,
        *,
        hospital_doctor_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[DoctorScheduleException]:
        result = await self.session.execute(
            select(DoctorScheduleException).where(
                DoctorScheduleException.hospital_doctor_id
                == hospital_doctor_id,
                DoctorScheduleException.is_active.is_(True),
                DoctorScheduleException.exception_date
                >= start_date,
                DoctorScheduleException.exception_date
                <= end_date,
            )
        )

        return list(
            result.scalars().all()
        )

    @staticmethod
    def _generate_window(
        *,
        slot_date: date,
        start_time,
        end_time,
        duration: int,
        capacity: int,
    ) -> list[dict]:
        cursor = datetime.combine(
            slot_date,
            start_time,
        )
        boundary = datetime.combine(
            slot_date,
            end_time,
        )

        delta = timedelta(
            minutes=duration
        )

        slots: list[dict] = []

        while cursor + delta <= boundary:
            slots.append(
                {
                    "slot_date": slot_date,
                    "start_time": cursor.time(),
                    "end_time": (
                        cursor + delta
                    ).time(),
                    "capacity": capacity,
                }
            )

            cursor += delta

        return slots

    @staticmethod
    def _overlaps(
        slot: dict,
        exception: DoctorScheduleException,
    ) -> bool:
        if (
            exception.start_time is None
            or exception.end_time is None
        ):
            return True

        return (
            slot["start_time"]
            < exception.end_time
            and slot["end_time"]
            > exception.start_time
        )

    async def desired_slots(
        self,
        *,
        hospital_doctor_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        if end_date < start_date:
            raise ScheduleValidationError(
                "end_date cannot precede start_date."
            )

        if (
            end_date - start_date
        ).days > 180:
            raise ScheduleValidationError(
                "Materialization range cannot exceed 180 days."
            )

        rules = await self.effective_rules(
            hospital_doctor_id=hospital_doctor_id,
            start_date=start_date,
            end_date=end_date,
        )

        exceptions = await self.effective_exceptions(
            hospital_doctor_id=hospital_doctor_id,
            start_date=start_date,
            end_date=end_date,
        )

        exceptions_by_date: dict[
            date,
            list[DoctorScheduleException],
        ] = defaultdict(list)

        for item in exceptions:
            self.validate_exception(item)

            exceptions_by_date[
                item.exception_date
            ].append(item)

        output: dict[
            tuple[date, object],
            dict,
        ] = {}

        current = start_date

        while current <= end_date:
            day_exceptions = (
                exceptions_by_date.get(
                    current,
                    [],
                )
            )

            overrides = [
                item
                for item in day_exceptions
                if item.kind == "override"
            ]

            blockers = [
                item
                for item in day_exceptions
                if item.kind in {
                    "leave",
                    "closure",
                    "unavailable",
                }
            ]

            windows: list[dict] = []

            if overrides:
                for item in overrides:
                    windows.extend(
                        self._generate_window(
                            slot_date=current,
                            start_time=item.start_time,
                            end_time=item.end_time,
                            duration=(
                                item.slot_duration_minutes
                                or 20
                            ),
                            capacity=(
                                item.capacity
                                or 1
                            ),
                        )
                    )

            else:
                for rule in rules:
                    if rule.weekday != current.weekday():
                        continue

                    if (
                        rule.valid_from is not None
                        and current < rule.valid_from
                    ):
                        continue

                    if (
                        rule.valid_until is not None
                        and current > rule.valid_until
                    ):
                        continue

                    windows.extend(
                        self._generate_window(
                            slot_date=current,
                            start_time=rule.start_time,
                            end_time=rule.end_time,
                            duration=(
                                rule.slot_duration_minutes
                            ),
                            capacity=rule.capacity,
                        )
                    )

            for slot in windows:
                blocked = any(
                    self._overlaps(
                        slot,
                        exception,
                    )
                    for exception in blockers
                )

                if blocked:
                    continue

                key = (
                    slot["slot_date"],
                    slot["start_time"],
                )

                existing = output.get(key)

                if existing is None:
                    output[key] = slot
                else:
                    existing["capacity"] = max(
                        existing["capacity"],
                        slot["capacity"],
                    )

            current += timedelta(days=1)

        return [
            output[key]
            for key in sorted(
                output,
                key=lambda item: (
                    item[0],
                    item[1],
                ),
            )
        ]

    async def existing_slots(
        self,
        *,
        hospital_doctor_id: UUID,
        start_date: date,
        end_date: date,
        lock: bool = False,
    ) -> list[DoctorSlot]:
        statement = (
            select(DoctorSlot)
            .where(
                DoctorSlot.hospital_doctor_id
                == hospital_doctor_id,
                DoctorSlot.slot_date
                >= start_date,
                DoctorSlot.slot_date
                <= end_date,
            )
            .order_by(
                DoctorSlot.slot_date,
                DoctorSlot.start_time,
            )
        )

        if lock:
            statement = statement.with_for_update()

        result = await self.session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def appointment_counts(
        self,
        *,
        slot_ids: list[UUID],
    ) -> dict[UUID, int]:
        if not slot_ids:
            return {}

        result = await self.session.execute(
            select(
                Appointment.doctor_slot_id,
                func.count(Appointment.id),
            )
            .where(
                Appointment.doctor_slot_id.in_(
                    slot_ids
                ),
                Appointment.status.in_(
                    ACTIVE_APPOINTMENT_STATUSES
                ),
            )
            .group_by(
                Appointment.doctor_slot_id
            )
        )

        return {
            row[0]: int(row[1])
            for row in result.all()
        }

    async def preview(
        self,
        *,
        mapping: HospitalDoctor,
        start_date: date,
        end_date: date,
        lock_existing: bool = False,
    ) -> dict:
        desired = await self.desired_slots(
            hospital_doctor_id=mapping.id,
            start_date=start_date,
            end_date=end_date,
        )

        existing = await self.existing_slots(
            hospital_doctor_id=mapping.id,
            start_date=start_date,
            end_date=end_date,
            lock=lock_existing,
        )

        counts = await self.appointment_counts(
            slot_ids=[
                slot.id
                for slot in existing
            ]
        )

        desired_by_key = {
            (
                slot["slot_date"],
                slot["start_time"],
            ): slot
            for slot in desired
        }

        conflicts: list[dict] = []

        for slot in existing:
            active = counts.get(
                slot.id,
                0,
            )

            if active == 0:
                continue

            desired_slot = desired_by_key.get(
                (
                    slot.slot_date,
                    slot.start_time,
                )
            )

            if desired_slot is None:
                conflicts.append(
                    {
                        "slot_id": slot.id,
                        "slot_date": slot.slot_date,
                        "start_time": slot.start_time,
                        "active_appointments": active,
                        "reason": (
                            "schedule_would_remove_booked_slot"
                        ),
                    }
                )

                continue

            if (
                desired_slot["capacity"]
                < active
            ):
                conflicts.append(
                    {
                        "slot_id": slot.id,
                        "slot_date": slot.slot_date,
                        "start_time": slot.start_time,
                        "active_appointments": active,
                        "reason": (
                            "capacity_below_active_bookings"
                        ),
                    }
                )

        return {
            "doctor_id": mapping.doctor_id,
            "hospital_doctor_id": mapping.id,
            "start_date": start_date,
            "end_date": end_date,
            "desired_slots": len(desired),
            "existing_slots": len(existing),
            "conflicts": conflicts,
            "_desired": desired,
            "_existing": existing,
            "_counts": counts,
        }

    async def apply(
        self,
        *,
        mapping: HospitalDoctor,
        hospital_id: UUID,
        actor_user_id: UUID | None,
        start_date: date,
        end_date: date,
    ) -> dict:
        self.assert_local_schedule_writable(
            mapping
        )

        locked_mapping = await self.session.scalar(
            select(HospitalDoctor)
            .where(
                HospitalDoctor.id == mapping.id,
                HospitalDoctor.hospital_id
                == hospital_id,
            )
            .with_for_update()
        )

        if locked_mapping is None:
            raise ScheduleOwnershipError(
                "Hospital doctor mapping no longer exists."
            )

        mapping = locked_mapping

        preview = await self.preview(
            mapping=mapping,
            start_date=start_date,
            end_date=end_date,
            lock_existing=True,
        )

        if preview["conflicts"]:
            raise ScheduleConflictError(
                preview["conflicts"]
            )

        desired = preview["_desired"]
        existing = preview["_existing"]
        counts = preview["_counts"]

        existing_by_key = {
            (
                slot.slot_date,
                slot.start_time,
            ): slot
            for slot in existing
        }

        desired_keys = set()

        created = 0
        updated = 0
        disabled = 0

        for spec in desired:
            key = (
                spec["slot_date"],
                spec["start_time"],
            )

            desired_keys.add(key)

            slot = existing_by_key.get(key)

            if slot is None:
                slot = DoctorSlot(
                    hospital_doctor_id=mapping.id,
                    doctor_id=mapping.doctor_id,
                    slot_date=spec["slot_date"],
                    start_time=spec["start_time"],
                    capacity=spec["capacity"],
                    is_enabled=True,
                    is_available=True,
                )

                self.session.add(slot)
                created += 1
                continue

            active = counts.get(
                slot.id,
                0,
            )

            changed = (
                slot.capacity
                != spec["capacity"]
                or not slot.is_enabled
            )

            slot.capacity = spec[
                "capacity"
            ]

            slot.is_enabled = True
            slot.is_available = (
                active < slot.capacity
            )

            if changed:
                updated += 1

        for slot in existing:
            key = (
                slot.slot_date,
                slot.start_time,
            )

            if key in desired_keys:
                continue

            if counts.get(slot.id, 0):
                continue

            if (
                slot.is_enabled
                or slot.is_available
            ):
                slot.is_enabled = False
                slot.is_available = False
                disabled += 1

        audit = HospitalOperationsAudit(
            hospital_id=hospital_id,
            actor_user_id=actor_user_id,
            entity_type="doctor_schedule",
            entity_id=mapping.id,
            action="schedule.materialized",
            before_state={
                "existing_slots": (
                    preview["existing_slots"]
                ),
            },
            after_state={
                "desired_slots": (
                    preview["desired_slots"]
                ),
                "created": created,
                "updated": updated,
                "disabled": disabled,
            },
            metadata_json={
                "start_date": (
                    start_date.isoformat()
                ),
                "end_date": (
                    end_date.isoformat()
                ),
            },
        )

        self.session.add(audit)

        await self.session.flush()

        return {
            "applied": True,
            "created": created,
            "updated": updated,
            "disabled": disabled,
            "conflicts": [],
        }
