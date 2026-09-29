from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)
import json
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.schemas.platform_control_v2 import (
    HospitalDataMode,
    PlatformControlHospitalDetail,
    PlatformControlHospitalSummary,
    PlatformControlOverview,
    PlatformHospitalProvisionRequest,
    PlatformHospitalStatusUpdate,
)


TABLES = {'hospital': 'hospitals', 'membership': 'hospital_memberships', 'user': 'users', 'doctor': 'doctors', 'hospital_doctor': 'hospital_doctors', 'appointment': 'appointments', 'schedule_rule': 'doctor_schedule_rules', 'schedule_exception': 'doctor_schedule_exceptions', 'integration': 'hospital_integrations'}


class PlatformControlError(
    RuntimeError
):
    pass


class PlatformControlService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        actor_user_id,
    ) -> None:
        self.session = session

        self.actor_user_id = str(
            actor_user_id
        )


    @staticmethod
    def _table(
        name: str,
    ) -> str | None:
        value = TABLES.get(
            name
        )

        return (
            value
            if isinstance(
                value,
                str,
            )
            and value
            else None
        )


    async def _scalar(
        self,
        sql: str,
        params: dict[
            str,
            Any,
        ] | None = None,
    ) -> Any:
        return (
            await self.session.execute(
                text(
                    sql
                ),
                params or {},
            )
        ).scalar()


    async def _rows(
        self,
        sql: str,
        params: dict[
            str,
            Any,
        ] | None = None,
    ) -> list[
        dict[
            str,
            Any,
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
            for row
            in result.mappings()
        ]


    async def _event(
        self,
        event_type: str,
        detail: dict[
            str,
            Any,
        ],
        *,
        hospital_id:
            str | None = None,
    ) -> None:
        await self.session.execute(
            text(
                """
                INSERT INTO platform_control_events
                    (
                        id,
                        hospital_id,
                        actor_user_id,
                        event_type,
                        detail,
                        created_at
                    )
                VALUES
                    (
                        :id,
                        :hospital_id,
                        :actor_user_id,
                        :event_type,
                        CAST(:detail AS json),
                        :created_at
                    )
                """
            ),
            {
                "id":
                    str(
                        uuid.uuid4()
                    ),

                "hospital_id":
                    hospital_id,

                "actor_user_id":
                    self.actor_user_id,

                "event_type":
                    event_type,

                "detail":
                    json.dumps(
                        detail,
                        default=str,
                    ),

                "created_at":
                    datetime.now(
                        timezone.utc
                    ),
            },
        )


    async def _hospital_row(
        self,
        slug: str,
    ) -> dict[
        str,
        Any,
    ]:
        hospital_table = self._table(
            "hospital"
        )

        rows = await self._rows(
            f"""
            SELECT *
            FROM {hospital_table}
            WHERE slug = :slug
            LIMIT 1
            """,
            {
                "slug":
                    slug,
            },
        )

        if not rows:
            raise PlatformControlError(
                "Hospital not found."
            )

        return rows[
            0
        ]


    async def _count(
        self,
        table_name:
            str | None,
        *,
        hospital_id: str,
        hospital_column:
            str = "hospital_id",
    ) -> int:
        if not table_name:
            return 0

        try:
            value = await self._scalar(
                f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE {hospital_column}
                    = :hospital_id
                """,
                {
                    "hospital_id":
                        hospital_id,
                },
            )

            return int(
                value or 0
            )

        except Exception:
            # Optional legacy tables may not be directly
            # hospital-scoped. Fail closed as unavailable.
            return 0


    async def _data_mode(
        self,
        hospital_id: str,
    ) -> str:
        value = await self._scalar(
            """
            SELECT data_mode
            FROM hospital_platform_settings
            WHERE hospital_id = :hospital_id
            """,
            {
                "hospital_id":
                    hospital_id,
            },
        )

        return str(
            value or "managed"
        )


    async def hospital_summary(
        self,
        hospital:
            dict[
                str,
                Any,
            ],
    ) -> PlatformControlHospitalSummary:
        hospital_id = str(
            hospital[
                "id"
            ]
        )

        membership_table = self._table(
            "membership"
        )

        integration_table = self._table(
            "integration"
        )

        hospital_doctor_table = self._table(
            "hospital_doctor"
        )

        appointment_table = self._table(
            "appointment"
        )

        rule_table = self._table(
            "schedule_rule"
        )

        exception_table = self._table(
            "schedule_exception"
        )


        doctors = await self._count(
            hospital_doctor_table,
            hospital_id=
                hospital_id,
        )

        appointments = await self._count(
            appointment_table,
            hospital_id=
                hospital_id,
        )

        staff = await self._count(
            membership_table,
            hospital_id=
                hospital_id,
        )

        integrations = await self._count(
            integration_table,
            hospital_id=
                hospital_id,
        )


        schedule_rules = 0

        schedule_exceptions = 0


        # Schedule tables are commonly linked through
        # hospital_doctors, not direct hospital_id.
        if (
            rule_table
            and hospital_doctor_table
        ):
            try:
                schedule_rules = int(
                    await self._scalar(
                        f"""
                        SELECT COUNT(*)
                        FROM {rule_table} r
                        JOIN {hospital_doctor_table} hd
                          ON hd.id =
                             r.hospital_doctor_id
                        WHERE hd.hospital_id =
                              :hospital_id
                        """,
                        {
                            "hospital_id":
                                hospital_id,
                        },
                    )
                    or 0
                )

            except Exception:
                schedule_rules = 0


        if (
            exception_table
            and hospital_doctor_table
        ):
            try:
                schedule_exceptions = int(
                    await self._scalar(
                        f"""
                        SELECT COUNT(*)
                        FROM {exception_table} e
                        JOIN {hospital_doctor_table} hd
                          ON hd.id =
                             e.hospital_doctor_id
                        WHERE hd.hospital_id =
                              :hospital_id
                        """,
                        {
                            "hospital_id":
                                hospital_id,
                        },
                    )
                    or 0
                )

            except Exception:
                schedule_exceptions = 0


        integration_health = {
            "total":
                integrations,
        }


        if integration_table:
            try:
                columns = await self._rows(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = :table_name
                    """,
                    {
                        "table_name":
                            integration_table,
                    },
                )

                field_names = {
                    str(
                        item[
                            "column_name"
                        ]
                    )
                    for item in columns
                }

                health_field = next(
                    (
                        candidate
                        for candidate in (
                            "health_status",
                            "status",
                            "sync_status",
                        )
                        if candidate
                        in field_names
                    ),
                    None,
                )


                if health_field:
                    health_rows = (
                        await self._rows(
                            f"""
                            SELECT
                                {health_field}
                                    AS status,
                                COUNT(*) AS count
                            FROM {integration_table}
                            WHERE hospital_id =
                                  :hospital_id
                            GROUP BY
                                {health_field}
                            """,
                            {
                                "hospital_id":
                                    hospital_id,
                            },
                        )
                    )

                    integration_health[
                        "by_status"
                    ] = health_rows

            except Exception:
                pass


        status = str(
            hospital.get(
                "status"
            )
            or "active"
        )


        return PlatformControlHospitalSummary(
            id=hospital_id,

            slug=str(
                hospital.get(
                    "slug"
                )
                or ""
            ),

            name=str(
                hospital.get(
                    "name"
                )
                or hospital.get(
                    "slug"
                )
                or hospital_id
            ),

            timezone=(
                str(
                    hospital.get(
                        "timezone"
                    )
                )
                if hospital.get(
                    "timezone"
                )
                is not None
                else None
            ),

            status=status,

            data_mode=
                await self._data_mode(
                    hospital_id
                ),

            doctors=
                doctors,

            appointments=
                appointments,

            staff=
                staff,

            integrations=
                integrations,

            schedule_rules=
                schedule_rules,

            schedule_exceptions=
                schedule_exceptions,

            integration_health=
                integration_health,

            security={
                "active_memberships":
                    staff,

                "suspended":
                    (
                        status
                        ==
                        "suspended"
                    ),
            },

            usage={
                "appointments":
                    appointments,

                "schedule_rules":
                    schedule_rules,

                "copilot_enabled":
                    True,
            },
        )


    async def list_hospitals(
        self,
    ) -> list[
        PlatformControlHospitalSummary
    ]:
        table_name = self._table(
            "hospital"
        )

        rows = await self._rows(
            f"""
            SELECT *
            FROM {table_name}
            ORDER BY
                name NULLS LAST,
                slug
            """
        )

        result = []

        for row in rows:
            result.append(
                await self.hospital_summary(
                    row
                )
            )

        return result


    async def detail(
        self,
        slug: str,
    ) -> PlatformControlHospitalDetail:
        hospital = await self._hospital_row(
            slug
        )

        summary = await self.hospital_summary(
            hospital
        )

        hospital_id = summary.id


        recent_integrations = []

        integration_table = self._table(
            "integration"
        )

        if integration_table:
            try:
                recent_integrations = (
                    await self._rows(
                        f"""
                        SELECT *
                        FROM {integration_table}
                        WHERE hospital_id =
                              :hospital_id
                        ORDER BY
                            updated_at DESC
                            NULLS LAST
                        LIMIT 10
                        """,
                        {
                            "hospital_id":
                                hospital_id,
                        },
                    )
                )

            except Exception:
                pass


        recent_appointments = []

        appointment_table = self._table(
            "appointment"
        )

        if appointment_table:
            try:
                recent_appointments = (
                    await self._rows(
                        f"""
                        SELECT *
                        FROM {appointment_table}
                        WHERE hospital_id =
                              :hospital_id
                        ORDER BY
                            created_at DESC
                            NULLS LAST
                        LIMIT 10
                        """,
                        {
                            "hospital_id":
                                hospital_id,
                        },
                    )
                )

            except Exception:
                pass


        events = await self._rows(
            """
            SELECT
                id,
                event_type,
                detail,
                actor_user_id,
                created_at
            FROM platform_control_events
            WHERE hospital_id =
                  :hospital_id
            ORDER BY created_at DESC
            LIMIT 20
            """,
            {
                "hospital_id":
                    hospital_id,
            },
        )


        return PlatformControlHospitalDetail(
            **summary.model_dump(),

            recent_integrations=
                recent_integrations,

            recent_appointments=
                recent_appointments,

            recent_platform_events=
                events,
        )


    async def overview(
        self,
    ) -> PlatformControlOverview:
        hospitals = await self.list_hospitals()

        copilot_total = int(
            await self._scalar(
                """
                SELECT COUNT(*)
                FROM hospital_copilot_proposals
                """
            )
            or 0
        )

        copilot_failed = int(
            await self._scalar(
                """
                SELECT COUNT(*)
                FROM hospital_copilot_proposals
                WHERE status = 'failed'
                """
            )
            or 0
        )


        unhealthy = 0

        for hospital in hospitals:
            for item in (
                hospital
                .integration_health
                .get(
                    "by_status",
                    [],
                )
            ):
                status = str(
                    item.get(
                        "status"
                    )
                    or ""
                ).lower()

                if status in {
                    "failed",
                    "error",
                    "unhealthy",
                    "degraded",
                    "disconnected",
                }:
                    unhealthy += int(
                        item.get(
                            "count"
                        )
                        or 0
                    )


        return PlatformControlOverview(
            hospitals_total=
                len(
                    hospitals
                ),

            hospitals_active=
                sum(
                    1
                    for item
                    in hospitals
                    if item.status
                    == "active"
                ),

            hospitals_suspended=
                sum(
                    1
                    for item
                    in hospitals
                    if item.status
                    == "suspended"
                ),

            appointments_total=
                sum(
                    item.appointments
                    for item
                    in hospitals
                ),

            doctors_total=
                sum(
                    item.doctors
                    for item
                    in hospitals
                ),

            staff_total=
                sum(
                    item.staff
                    for item
                    in hospitals
                ),

            integrations_total=
                sum(
                    item.integrations
                    for item
                    in hospitals
                ),

            unhealthy_integrations=
                unhealthy,

            copilot_proposals_total=
                copilot_total,

            copilot_failed_executions=
                copilot_failed,
        )


    async def provision(
        self,
        payload:
            PlatformHospitalProvisionRequest,
    ) -> PlatformControlHospitalDetail:
        hospital_table = self._table(
            "hospital"
        )

        user_table = self._table(
            "user"
        )

        membership_table = self._table(
            "membership"
        )


        duplicate = await self._scalar(
            f"""
            SELECT COUNT(*)
            FROM {hospital_table}
            WHERE slug = :slug
            """,
            {
                "slug":
                    payload.slug,
            },
        )

        if int(
            duplicate or 0
        ) > 0:
            raise PlatformControlError(
                "Hospital slug already exists."
            )


        user_rows = await self._rows(
            f"""
            SELECT *
            FROM {user_table}
            WHERE LOWER(email) =
                  LOWER(:email)
            LIMIT 1
            """,
            {
                "email":
                    payload.initial_admin_email,
            },
        )


        if not user_rows:
            raise PlatformControlError(
                "Initial administrator must already "
                "have a MediBook account."
            )


        admin = user_rows[
            0
        ]


        hospital_id = str(
            uuid.uuid4()
        )


        # Inspect actual Hospital columns so we only
        # write fields that really exist.
        column_rows = await self._rows(
            """
            SELECT
                column_name,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table
            """,
            {
                "table":
                    hospital_table,
            },
        )


        columns = {
            item[
                "column_name"
            ]:
                item
            for item
            in column_rows
        }


        now = datetime.now(
            timezone.utc
        )

        values = {
            "id":
                hospital_id,

            "slug":
                payload.slug,

            "name":
                payload.name,

            "timezone":
                payload.timezone,

            "status":
                (
                    "active"
                    if payload.activate
                    else "suspended"
                ),

            "is_active":
                bool(
                    payload.activate
                ),

            "created_at":
                now,

            "updated_at":
                now,
        }


        usable = {
            key:
                value
            for key, value
            in values.items()
            if key in columns
        }


        required_without_value = []

        for name, meta in columns.items():
            if (
                name in usable

            ):
                continue

            if (
                str(
                    meta[
                        "is_nullable"
                    ]
                )
                == "NO"
                and meta[
                    "column_default"
                ]
                is None
            ):
                required_without_value.append(
                    name
                )


        if required_without_value:
            raise PlatformControlError(
                "Hospital provisioning requires "
                "additional model fields: "
                + ", ".join(
                    sorted(
                        required_without_value
                    )
                )
            )


        fields = list(
            usable
        )

        binds = [
            f":{field}"
            for field in fields
        ]


        await self.session.execute(
            text(
                f"""
                INSERT INTO {hospital_table}
                    (
                        {", ".join(fields)}
                    )
                VALUES
                    (
                        {", ".join(binds)}
                    )
                """
            ),
            usable,
        )


        await self.session.execute(
            text(
                """
                INSERT INTO hospital_platform_settings
                    (
                        hospital_id,
                        data_mode,
                        created_at,
                        updated_at
                    )
                VALUES
                    (
                        :hospital_id,
                        :data_mode,
                        :now,
                        :now
                    )
                """
            ),
            {
                "hospital_id":
                    hospital_id,

                "data_mode":
                    payload.data_mode.value,

                "now":
                    now,
            },
        )


        membership_columns = await self._rows(
            """
            SELECT
                column_name,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table
            """,
            {
                "table":
                    membership_table,
            },
        )


        member_fields = {
            item[
                "column_name"
            ]
            for item
            in membership_columns
        }


        membership_values = {
            "id":
                str(
                    uuid.uuid4()
                ),

            "hospital_id":
                hospital_id,

            "user_id":
                str(
                    admin[
                        "id"
                    ]
                ),

            "role":
                "hospital_admin",

            "is_active":
                True,

            "created_at":
                now,
        }


        membership_values = {
            key:
                value
            for key, value
            in membership_values.items()
            if key in member_fields
        }


        fields = list(
            membership_values
        )


        await self.session.execute(
            text(
                f"""
                INSERT INTO {membership_table}
                    (
                        {", ".join(fields)}
                    )
                VALUES
                    (
                        {", ".join(
                            f":{field}"
                            for field
                            in fields
                        )}
                    )
                """
            ),
            membership_values,
        )


        await self._event(
            "platform.hospital.provisioned",
            {
                "slug":
                    payload.slug,

                "name":
                    payload.name,

                "timezone":
                    payload.timezone,

                "data_mode":
                    payload.data_mode.value,

                "initial_admin_email":
                    payload.initial_admin_email,

                "activated":
                    payload.activate,
            },
            hospital_id=
                hospital_id,
        )


        await self.session.commit()


        return await self.detail(
            payload.slug
        )


    async def update_status(
        self,
        slug: str,
        payload:
            PlatformHospitalStatusUpdate,
    ) -> PlatformControlHospitalDetail:
        hospital = await self._hospital_row(
            slug
        )

        hospital_id = str(
            hospital[
                "id"
            ]
        )

        hospital_table = self._table(
            "hospital"
        )


        column = await self._scalar(
            """
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table
              AND column_name = 'status'
            """,
            {
                "table":
                    hospital_table,
            },
        )


        if int(
            column or 0
        ) != 1:
            raise PlatformControlError(
                "Hospital model has no status column."
            )


        await self.session.execute(
            text(
                f"""
                UPDATE {hospital_table}
                SET status = :status,
                    is_active = :is_active,
                    updated_at = :updated_at
                WHERE id = :hospital_id
                """
            ),
            {
                "status":
                    payload.status.value,

                "is_active":
                    (
                        payload.status.value
                        == "active"
                    ),

                "updated_at":
                    datetime.now(
                        timezone.utc
                    ),

                "hospital_id":
                    hospital_id,
            },
        )


        await self._event(
            "platform.hospital.status_changed",
            {
                "old_status":
                    hospital.get(
                        "status"
                    ),

                "new_status":
                    payload.status.value,

                "reason":
                    payload.reason,
            },
            hospital_id=
                hospital_id,
        )


        await self.session.commit()


        return await self.detail(
            slug
        )
