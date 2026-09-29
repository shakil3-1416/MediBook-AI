from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.hospital_copilot import (
    HospitalCopilotIntent,
    HospitalCopilotToolResult,
)

from app.services.hospital_copilot_llm import (
    interpret_intent,
)


MODEL_CONFIG = {'appointment_table': 'appointments', 'appointment_fields': ['doctor_id', 'doctor_slot_id', 'patient_id', 'hospital_id', 'consultation_fee', 'status', 'confirmation_code', 'booked_at', 'cancelled_at'], 'doctor_table': 'doctors', 'doctor_fields': ['full_name', 'gender', 'qualification', 'experience_years', 'specialty_id', 'clinic_name', 'clinic_location', 'consultation_fee', 'is_active', 'specialty', 'slots'], 'hospital_doctor_table': 'hospital_doctors', 'hospital_doctor_fields': ['id', 'hospital_id', 'doctor_id', 'is_active', 'source_mode', 'external_doctor_id', 'clinic_name', 'clinic_location', 'consultation_fee', 'public_profile', 'operational_metadata', 'created_at', 'updated_at'], 'schedule_rule_table': 'doctor_schedule_rules', 'schedule_rule_fields': ['id', 'hospital_doctor_id', 'weekday', 'start_time', 'end_time', 'slot_duration_minutes', 'capacity', 'valid_from', 'valid_until', 'is_active', 'created_at', 'updated_at'], 'schedule_exception_table': 'doctor_schedule_exceptions', 'schedule_exception_fields': ['id', 'hospital_doctor_id', 'exception_date', 'kind', 'start_time', 'end_time', 'slot_duration_minutes', 'capacity', 'reason', 'is_active', 'created_at', 'updated_at'], 'integration_table': 'hospital_integrations', 'integration_fields': ['id', 'hospital_id', 'provider', 'status', 'integration_type', 'source_mode', 'sync_status', 'ownership', 'last_sync_at', 'last_error', 'is_active', 'config', 'last_checked_at', 'created_at', 'updated_at'], 'membership_table': 'hospital_memberships', 'membership_fields': ['id', 'hospital_id', 'user_id', 'role', 'is_active', 'created_at'], 'audit_table': None, 'audit_fields': []}


class HospitalCopilotService:
    """
    Deterministic, hospital-scoped analytics layer.

    Important:
    - This service never mutates hospital operational data.
    - It never lets an LLM construct SQL.
    - Every table/column identifier is discovered from the local
      SQLAlchemy model source at generation time and stored in MODEL_CONFIG.
    - Hospital scoping is applied by trusted deterministic code.
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        hospital_id,
        hospital_slug: str,
    ) -> None:
        self.session = session
        self.hospital_id = hospital_id
        self.hospital_slug = hospital_slug


    # --------------------------------------------------------------
    # Intent router
    # --------------------------------------------------------------

    @staticmethod
    def classify_intent(
        message: str,
    ) -> HospitalCopilotIntent:
        q = (
            message
            .strip()
            .lower()
        )

        if not q:
            return (
                HospitalCopilotIntent.UNKNOWN
            )

        if any(
            phrase in q
            for phrase in (
                "what can you do",
                "help",
                "capabilities",
            )
        ):
            return (
                HospitalCopilotIntent.HELP
            )

        if any(
            word in q
            for word in (
                "integration",
                "connector",
                "sync",
            )
        ):
            return (
                HospitalCopilotIntent.INTEGRATIONS
            )

        if any(
            phrase in q
            for phrase in (
                "recent change",
                "recent activity",
                "audit",
                "who changed",
            )
        ):
            return (
                HospitalCopilotIntent.RECENT_CHANGES
            )

        if any(
            word in q
            for word in (
                "schedule",
                "shift",
                "availability rule",
                "exception",
            )
        ):
            return (
                HospitalCopilotIntent.SCHEDULES
            )

        if any(
            word in q
            for word in (
                "capacity",
                "slot",
                "utilization",
            )
        ):
            return (
                HospitalCopilotIntent.CAPACITY
            )

        if any(
            word in q
            for word in (
                "doctor",
                "physician",
                "specialist",
            )
        ):
            return (
                HospitalCopilotIntent.DOCTORS
            )

        if any(
            word in q
            for word in (
                "staff",
                "member",
                "admin",
                "role",
            )
        ):
            return (
                HospitalCopilotIntent.STAFF
            )

        if any(
            word in q
            for word in (
                "appointment",
                "booking",
                "booked",
                "cancelled",
                "canceled",
                "rescheduled",
            )
        ):
            return (
                HospitalCopilotIntent.APPOINTMENTS
            )

        if any(
            phrase in q
            for phrase in (
                "overview",
                "summary",
                "today",
                "how are we doing",
                "hospital status",
            )
        ):
            return (
                HospitalCopilotIntent.OVERVIEW
            )

        return (
            HospitalCopilotIntent.UNKNOWN
        )



    async def interpret(
        self,
        message: str,
    ) -> tuple[
        HospitalCopilotIntent,
        str,
    ]:
        deterministic = (
            self.classify_intent(
                message
            )
        )

        if (
            deterministic
            !=
            HospitalCopilotIntent.UNKNOWN
        ):
            return (
                deterministic,
                "deterministic",
            )

        llm_intent = await interpret_intent(
            message
        )

        if (
            llm_intent is not None
        ):
            return (
                llm_intent,
                "llm_grounded",
            )

        return (
            HospitalCopilotIntent.UNKNOWN,
            "deterministic",
        )


    # --------------------------------------------------------------
    # Safe SQL identifier helpers
    # --------------------------------------------------------------

    @staticmethod
    def _table(
        key: str,
    ) -> str | None:
        value = (
            MODEL_CONFIG.get(
                key
            )
        )

        if isinstance(
            value,
            str,
        ):
            return value

        return None


    @staticmethod
    def _fields(
        key: str,
    ) -> set[str]:
        value = (
            MODEL_CONFIG.get(
                key
            )
        )

        if not isinstance(
            value,
            list,
        ):
            return set()

        return {
            str(
                item
            )
            for item in value
        }


    async def _scalar(
        self,
        sql: str,
        params: dict[
            str,
            Any
        ] | None = None,
    ) -> Any:
        result = await self.session.execute(
            text(
                sql
            ),
            params or {},
        )

        return result.scalar()


    async def _mappings(
        self,
        sql: str,
        params: dict[
            str,
            Any
        ] | None = None,
    ) -> list[
        dict[
            str,
            Any
        ]
    ]:
        result = await self.session.execute(
            text(
                sql
            ),
            params or {},
        )

        return [
            dict(
                row
            )
            for row in result.mappings()
        ]


    # --------------------------------------------------------------
    # Appointments
    # --------------------------------------------------------------

    async def appointments(
        self,
    ) -> HospitalCopilotToolResult:
        table_name = self._table(
            "appointment_table"
        )

        fields = self._fields(
            "appointment_fields"
        )

        if (
            not table_name
            or "hospital_id"
            not in fields
        ):
            return HospitalCopilotToolResult(
                tool="appointments",
                available=False,
                note=(
                    "Appointment model is not available "
                    "with a hospital_id field."
                ),
            )

        total = await self._scalar(
            f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE hospital_id = :hospital_id
            """,
            {
                "hospital_id":
                    self.hospital_id,
            },
        )

        data: dict[
            str,
            Any
        ] = {
            "total":
                int(
                    total or 0
                ),
        }

        if (
            "status"
            in fields
        ):
            rows = await self._mappings(
                f"""
                SELECT status,
                       COUNT(*) AS count
                FROM {table_name}
                WHERE hospital_id = :hospital_id
                GROUP BY status
                ORDER BY count DESC
                """,
                {
                    "hospital_id":
                        self.hospital_id,
                },
            )

            data[
                "by_status"
            ] = rows

        datetime_field = None

        for candidate in (
            "scheduled_at",
            "appointment_time",
            "starts_at",
            "start_time",
            "created_at",
        ):
            if candidate in fields:
                datetime_field = (
                    candidate
                )

                break

        if datetime_field:
            today = await self._scalar(
                f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE hospital_id = :hospital_id
                  AND DATE({datetime_field})
                      = CURRENT_DATE
                """,
                {
                    "hospital_id":
                        self.hospital_id,
                },
            )

            data[
                "today"
            ] = int(
                today or 0
            )

        return HospitalCopilotToolResult(
            tool="appointments",
            data=data,
        )


    # --------------------------------------------------------------
    # Doctors
    # --------------------------------------------------------------

    async def doctors(
        self,
    ) -> HospitalCopilotToolResult:
        mapping_table = self._table(
            "hospital_doctor_table"
        )

        mapping_fields = self._fields(
            "hospital_doctor_fields"
        )

        doctor_table = self._table(
            "doctor_table"
        )

        doctor_fields = self._fields(
            "doctor_fields"
        )

        if (
            mapping_table
            and "hospital_id"
            in mapping_fields
        ):
            total = await self._scalar(
                f"""
                SELECT COUNT(*)
                FROM {mapping_table}
                WHERE hospital_id = :hospital_id
                """,
                {
                    "hospital_id":
                        self.hospital_id,
                },
            )

            data: dict[
                str,
                Any
            ] = {
                "total":
                    int(
                        total or 0
                    ),
            }

            if (
                "is_active"
                in mapping_fields
            ):
                active = await self._scalar(
                    f"""
                    SELECT COUNT(*)
                    FROM {mapping_table}
                    WHERE hospital_id = :hospital_id
                      AND is_active = TRUE
                    """,
                    {
                        "hospital_id":
                            self.hospital_id,
                    },
                )

                data[
                    "active"
                ] = int(
                    active or 0
                )

            return HospitalCopilotToolResult(
                tool="doctors",
                data=data,
            )

        if (
            doctor_table
            and "hospital_id"
            in doctor_fields
        ):
            total = await self._scalar(
                f"""
                SELECT COUNT(*)
                FROM {doctor_table}
                WHERE hospital_id = :hospital_id
                """,
                {
                    "hospital_id":
                        self.hospital_id,
                },
            )

            return HospitalCopilotToolResult(
                tool="doctors",
                data={
                    "total":
                        int(
                            total or 0
                        ),
                },
            )

        return HospitalCopilotToolResult(
            tool="doctors",
            available=False,
            note=(
                "Hospital doctor mapping was not "
                "discovered in the current model schema."
            ),
        )


    # --------------------------------------------------------------
    # Schedules / Capacity
    # --------------------------------------------------------------

    async def schedules(
        self,
    ) -> HospitalCopilotToolResult:
        rule_table = self._table(
            "schedule_rule_table"
        )

        rule_fields = self._fields(
            "schedule_rule_fields"
        )

        exception_table = self._table(
            "schedule_exception_table"
        )

        exception_fields = self._fields(
            "schedule_exception_fields"
        )

        data: dict[
            str,
            Any
        ] = {}

        available = False

        if (
            rule_table
            and "hospital_id"
            in rule_fields
        ):
            available = True

            count = await self._scalar(
                f"""
                SELECT COUNT(*)
                FROM {rule_table}
                WHERE hospital_id = :hospital_id
                """,
                {
                    "hospital_id":
                        self.hospital_id,
                },
            )

            data[
                "rules"
            ] = int(
                count or 0
            )

        if (
            exception_table
            and "hospital_id"
            in exception_fields
        ):
            available = True

            count = await self._scalar(
                f"""
                SELECT COUNT(*)
                FROM {exception_table}
                WHERE hospital_id = :hospital_id
                """,
                {
                    "hospital_id":
                        self.hospital_id,
                },
            )

            data[
                "exceptions"
            ] = int(
                count or 0
            )

        return HospitalCopilotToolResult(
            tool="schedules",
            available=available,
            data=data,
            note=(
                None
                if available
                else (
                    "No hospital-scoped schedule "
                    "tables were discovered."
                )
            ),
        )


    async def capacity(
        self,
    ) -> HospitalCopilotToolResult:
        appointments = await self.appointments()

        schedules = await self.schedules()

        data = {
            "appointments":
                appointments.data,

            "schedules":
                schedules.data,
        }

        return HospitalCopilotToolResult(
            tool="capacity",
            available=(
                appointments.available
                or schedules.available
            ),
            data=data,
            note=(
                None
                if (
                    appointments.available
                    or schedules.available
                )
                else (
                    "Capacity data sources are "
                    "not available."
                )
            ),
        )


    # --------------------------------------------------------------
    # Integrations
    # --------------------------------------------------------------

    async def integrations(
        self,
    ) -> HospitalCopilotToolResult:
        table_name = self._table(
            "integration_table"
        )

        fields = self._fields(
            "integration_fields"
        )

        if (
            not table_name
            or "hospital_id"
            not in fields
        ):
            return HospitalCopilotToolResult(
                tool="integrations",
                available=False,
                note=(
                    "Integration model was not "
                    "discovered with hospital scoping."
                ),
            )

        total = await self._scalar(
            f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE hospital_id = :hospital_id
            """,
            {
                "hospital_id":
                    self.hospital_id,
            },
        )

        data: dict[
            str,
            Any
        ] = {
            "total":
                int(
                    total or 0
                ),
        }

        for field in (
            "status",
            "health_status",
            "sync_status",
        ):
            if field in fields:
                data[
                    "by_status"
                ] = await self._mappings(
                    f"""
                    SELECT {field} AS status,
                           COUNT(*) AS count
                    FROM {table_name}
                    WHERE hospital_id = :hospital_id
                    GROUP BY {field}
                    ORDER BY count DESC
                    """,
                    {
                        "hospital_id":
                            self.hospital_id,
                    },
                )

                break

        recent_fields = [
            field
            for field in (
                "last_checked_at",
                "last_health_check_at",
                "last_sync_at",
                "updated_at",
            )
            if field in fields
        ]

        if recent_fields:
            field = (
                recent_fields[
                    0
                ]
            )

            data[
                "last_activity"
            ] = await self._scalar(
                f"""
                SELECT MAX({field})
                FROM {table_name}
                WHERE hospital_id = :hospital_id
                """,
                {
                    "hospital_id":
                        self.hospital_id,
                },
            )

        return HospitalCopilotToolResult(
            tool="integrations",
            data=data,
        )


    # --------------------------------------------------------------
    # Staff
    # --------------------------------------------------------------

    async def staff(
        self,
    ) -> HospitalCopilotToolResult:
        table_name = self._table(
            "membership_table"
        )

        fields = self._fields(
            "membership_fields"
        )

        if (
            not table_name
            or "hospital_id"
            not in fields
        ):
            return HospitalCopilotToolResult(
                tool="staff",
                available=False,
                note=(
                    "Hospital membership model "
                    "was not discovered."
                ),
            )

        where = (
            "hospital_id = :hospital_id"
        )

        if (
            "is_active"
            in fields
        ):
            where += (
                " AND is_active = TRUE"
            )

        total = await self._scalar(
            f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE {where}
            """,
            {
                "hospital_id":
                    self.hospital_id,
            },
        )

        data: dict[
            str,
            Any
        ] = {
            "active_staff":
                int(
                    total or 0
                ),
        }

        if (
            "role"
            in fields
        ):
            data[
                "by_role"
            ] = await self._mappings(
                f"""
                SELECT role,
                       COUNT(*) AS count
                FROM {table_name}
                WHERE {where}
                GROUP BY role
                ORDER BY count DESC
                """,
                {
                    "hospital_id":
                        self.hospital_id,
                },
            )

        return HospitalCopilotToolResult(
            tool="staff",
            data=data,
        )


    # --------------------------------------------------------------
    # Recent changes / audit
    # --------------------------------------------------------------

    async def recent_changes(
        self,
    ) -> HospitalCopilotToolResult:
        table_name = self._table(
            "audit_table"
        )

        fields = self._fields(
            "audit_fields"
        )

        if (
            not table_name
            or "hospital_id"
            not in fields
        ):
            return HospitalCopilotToolResult(
                tool="recent_changes",
                available=False,
                note=(
                    "Hospital audit model was not "
                    "discovered with hospital scoping."
                ),
            )

        time_field = None

        for candidate in (
            "created_at",
            "occurred_at",
            "timestamp",
        ):
            if candidate in fields:
                time_field = (
                    candidate
                )

                break

        if not time_field:
            return HospitalCopilotToolResult(
                tool="recent_changes",
                available=False,
                note=(
                    "Audit source has no supported "
                    "timestamp field."
                ),
            )

        columns = [
            field
            for field in (
                "action",
                "event",
                "entity_type",
                "entity_id",
                "actor_id",
                "actor_email",
                time_field,
            )
            if field in fields
        ]

        rows = await self._mappings(
            f"""
            SELECT {", ".join(columns)}
            FROM {table_name}
            WHERE hospital_id = :hospital_id
            ORDER BY {time_field} DESC
            LIMIT 10
            """,
            {
                "hospital_id":
                    self.hospital_id,
            },
        )

        return HospitalCopilotToolResult(
            tool="recent_changes",
            data={
                "items":
                    rows,
            },
        )


    # --------------------------------------------------------------
    # Overview
    # --------------------------------------------------------------

    async def overview(
        self,
    ) -> list[
        HospitalCopilotToolResult
    ]:
        return [
            await self.appointments(),
            await self.doctors(),
            await self.integrations(),
            await self.staff(),
        ]


    # --------------------------------------------------------------
    # Tool dispatch
    # --------------------------------------------------------------

    async def run(
        self,
        intent: HospitalCopilotIntent,
    ) -> list[
        HospitalCopilotToolResult
    ]:
        if (
            intent
            ==
            HospitalCopilotIntent.OVERVIEW
        ):
            return await self.overview()

        if (
            intent
            ==
            HospitalCopilotIntent.APPOINTMENTS
        ):
            return [
                await self.appointments()
            ]

        if (
            intent
            ==
            HospitalCopilotIntent.DOCTORS
        ):
            return [
                await self.doctors()
            ]

        if (
            intent
            ==
            HospitalCopilotIntent.CAPACITY
        ):
            return [
                await self.capacity()
            ]

        if (
            intent
            ==
            HospitalCopilotIntent.SCHEDULES
        ):
            return [
                await self.schedules()
            ]

        if (
            intent
            ==
            HospitalCopilotIntent.INTEGRATIONS
        ):
            return [
                await self.integrations()
            ]

        if (
            intent
            ==
            HospitalCopilotIntent.STAFF
        ):
            return [
                await self.staff()
            ]

        if (
            intent
            ==
            HospitalCopilotIntent.RECENT_CHANGES
        ):
            return [
                await self.recent_changes()
            ]

        return []


    # --------------------------------------------------------------
    # Deterministic response rendering
    # --------------------------------------------------------------

    @staticmethod
    def render(
        intent: HospitalCopilotIntent,
        tools: list[
            HospitalCopilotToolResult
        ],
    ) -> str:
        if (
            intent
            ==
            HospitalCopilotIntent.HELP
        ):
            return (
                "I can answer hospital-scoped questions about "
                "appointments, doctors, capacity, schedules, "
                "integrations, staff, and recent operational changes. "
                "I only use deterministic hospital data for factual answers."
            )

        if (
            intent
            ==
            HospitalCopilotIntent.UNKNOWN
        ):
            return (
                "I could not map that request to a supported hospital "
                "operations tool yet. Ask about appointments, doctors, "
                "capacity, schedules, integrations, staff, or recent changes."
            )

        available = [
            tool
            for tool in tools
            if tool.available
        ]

        if not available:
            notes = [
                tool.note
                for tool in tools
                if tool.note
            ]

            if notes:
                return (
                    "That hospital operation is not available from "
                    "the current deterministic data layer. "
                    + " ".join(
                        notes
                    )
                )

            return (
                "No deterministic hospital data was available "
                "for that request."
            )

        if (
            intent
            ==
            HospitalCopilotIntent.OVERVIEW
        ):
            parts = []

            for tool in available:
                parts.append(
                    f"{tool.tool}: {tool.data}"
                )

            return (
                "Current hospital operations overview — "
                + "; ".join(
                    parts
                )
                + "."
            )

        tool = available[
            0
        ]

        return (
            f"{tool.tool.replace('_', ' ').title()}: "
            f"{tool.data}"
        )
