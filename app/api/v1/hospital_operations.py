from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.auth import CurrentUser


router = APIRouter(
    prefix="/hospital-operations",
    tags=["hospital-operations"],
)


async def _hospital_row(
    session: AsyncSession,
    hospital_slug: str,
):
    result = await session.execute(
        text(
            """
            SELECT
                id,
                slug,
                name,
                is_active,
                timezone
            FROM hospitals
            WHERE slug = :slug
            LIMIT 1
            """
        ),
        {
            "slug":
                hospital_slug,
        },
    )

    return result.mappings().first()


async def _require_access(
    session: AsyncSession,
    current_user: CurrentUser,
    hospital_id: str,
):
    role = str(
        getattr(
            current_user,
            "role",
            "",
        )
        or ""
    ).lower()

    # MediBook platform admins may inspect hospital
    # operations for support/administration.
    if role in {
        "platform_admin",
        "super_admin",
        "admin",
    }:
        return


    user_id = getattr(
        current_user,
        "id",
        None,
    )

    if user_id is None:
        raise HTTPException(
            status_code=403,
            detail=(
                "Hospital dashboard access denied."
            ),
        )


    result = await session.execute(
        text(
            """
            SELECT 1
            FROM hospital_memberships
            WHERE hospital_id = :hospital_id
              AND user_id = :user_id
            LIMIT 1
            """
        ),
        {
            "hospital_id":
                str(
                    hospital_id
                ),

            "user_id":
                str(
                    user_id
                ),
        },
    )


    if result.first() is None:
        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have access "
                "to this hospital."
            ),
        )


async def _scalar(
    session: AsyncSession,
    query: str,
    params: dict,
):
    result = await session.execute(
        text(query),
        params,
    )

    return result.scalar()


@router.get(
    "/{hospital_slug}/summary"
)
async def hospital_summary(
    hospital_slug: str,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(
            get_db_session
        ),
    ],
):
    hospital = await _hospital_row(
        session,
        hospital_slug,
    )


    if hospital is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Hospital not found."
            ),
        )


    await _require_access(
        session,
        current_user,
        str(
            hospital["id"]
        ),
    )


    hospital_id = str(
        hospital["id"]
    )

    params = {
        "hospital_id":
            hospital_id,

        "today":
            date.today(),
    }


    # --------------------------------------------------
    # Doctors
    # --------------------------------------------------

    total_doctors = await _scalar(
        session,
        """
        SELECT COUNT(DISTINCT hd.doctor_id)
        FROM hospital_doctors hd
        JOIN doctors d
          ON d.id = hd.doctor_id
        WHERE hd.hospital_id = :hospital_id
        """,
        params,
    )


    specialty_count = await _scalar(
        session,
        """
        SELECT COUNT(
            DISTINCT d.specialty_id
        )
        FROM hospital_doctors hd
        JOIN doctors d
          ON d.id = hd.doctor_id
        WHERE hd.hospital_id = :hospital_id
        """,
        params,
    )


    # --------------------------------------------------
    # Appointments
    #
    # Appointment belongs to the hospital through the
    # mapped doctor. We intentionally do not aggregate
    # appointments for doctors outside this hospital.
    # --------------------------------------------------

    today_appointments = await _scalar(
        session,
        """
        SELECT COUNT(*)
        FROM appointments a
        JOIN hospital_doctors hd
          ON hd.doctor_id = a.doctor_id
        JOIN doctor_slots ds
          ON ds.id = a.doctor_slot_id
        WHERE hd.hospital_id = :hospital_id
          AND ds.slot_date = :today
          AND a.status <> 'cancelled'
        """,
        params,
    )


    upcoming_appointments = await _scalar(
        session,
        """
        SELECT COUNT(*)
        FROM appointments a
        JOIN hospital_doctors hd
          ON hd.doctor_id = a.doctor_id
        JOIN doctor_slots ds
          ON ds.id = a.doctor_slot_id
        WHERE hd.hospital_id = :hospital_id
          AND ds.slot_date >= :today
          AND a.status <> 'cancelled'
        """,
        params,
    )


    confirmed_appointments = await _scalar(
        session,
        """
        SELECT COUNT(*)
        FROM appointments a
        JOIN hospital_doctors hd
          ON hd.doctor_id = a.doctor_id
        WHERE hd.hospital_id = :hospital_id
          AND a.status = 'confirmed'
        """,
        params,
    )


    cancelled_appointments = await _scalar(
        session,
        """
        SELECT COUNT(*)
        FROM appointments a
        JOIN hospital_doctors hd
          ON hd.doctor_id = a.doctor_id
        WHERE hd.hospital_id = :hospital_id
          AND a.status = 'cancelled'
        """,
        params,
    )


    # --------------------------------------------------
    # Slots
    # --------------------------------------------------

    available_slots = await _scalar(
        session,
        """
        SELECT COUNT(*)
        FROM doctor_slots ds
        JOIN hospital_doctors hd
          ON hd.doctor_id = ds.doctor_id
        WHERE hd.hospital_id = :hospital_id
          AND ds.slot_date >= :today
          AND ds.is_available = TRUE
        """,
        params,
    )


    unavailable_slots = await _scalar(
        session,
        """
        SELECT COUNT(*)
        FROM doctor_slots ds
        JOIN hospital_doctors hd
          ON hd.doctor_id = ds.doctor_id
        WHERE hd.hospital_id = :hospital_id
          AND ds.slot_date >= :today
          AND ds.is_available = FALSE
        """,
        params,
    )


    # --------------------------------------------------
    # Reschedule event count
    # --------------------------------------------------

    rescheduled_count = 0

    try:
        rescheduled_count = (
            await _scalar(
                session,
                """
                SELECT COUNT(*)
                FROM appointment_events ae
                JOIN appointments a
                  ON a.id = ae.appointment_id
                JOIN hospital_doctors hd
                  ON hd.doctor_id = a.doctor_id
                WHERE hd.hospital_id = :hospital_id
                  AND ae.event_type = 'rescheduled'
                """,
                params,
            )
            or 0
        )

    except Exception:
        # Older development schemas may not yet contain
        # the event table. Dashboard remains usable.
        await session.rollback()

        rescheduled_count = 0


    # --------------------------------------------------
    # Recent appointments
    # --------------------------------------------------

    recent_result = await session.execute(
        text(
            """
            SELECT
                a.id AS appointment_id,
                a.confirmation_code,
                a.status,
                d.full_name AS doctor_name,
                ds.slot_date AS appointment_date,
                ds.start_time AS appointment_time,
                a.booked_at
            FROM appointments a
            JOIN hospital_doctors hd
              ON hd.doctor_id = a.doctor_id
            JOIN doctors d
              ON d.id = a.doctor_id
            LEFT JOIN doctor_slots ds
              ON ds.id = a.doctor_slot_id
            WHERE hd.hospital_id = :hospital_id
            ORDER BY a.booked_at DESC
            LIMIT 10
            """
        ),
        params,
    )


    recent = []

    for row in (
        recent_result
        .mappings()
        .all()
    ):
        recent.append(
            {
                "appointment_id":
                    str(
                        row[
                            "appointment_id"
                        ]
                    ),

                "confirmation_code":
                    row[
                        "confirmation_code"
                    ],

                "status":
                    row["status"],

                "doctor_name":
                    row[
                        "doctor_name"
                    ],

                "date":
                    (
                        row[
                            "appointment_date"
                        ].isoformat()
                        if row[
                            "appointment_date"
                        ]
                        else None
                    ),

                "time":
                    (
                        row[
                            "appointment_time"
                        ].strftime(
                            "%H:%M"
                        )
                        if row[
                            "appointment_time"
                        ]
                        else None
                    ),

                "booked_at":
                    (
                        row[
                            "booked_at"
                        ].isoformat()
                        if row[
                            "booked_at"
                        ]
                        else None
                    ),
            }
        )


    # --------------------------------------------------
    # Integration health
    #
    # Do not hard-code optional integration column names.
    # hospital_integrations has evolved during development,
    # so PostgreSQL provides the actual row as JSON and the
    # application maps known semantic fields conservatively.
    # --------------------------------------------------

    integration_result = await session.execute(
        text(
            """
            SELECT
                row_to_json(hi) AS integration
            FROM hospital_integrations hi
            WHERE hi.hospital_id = :hospital_id
            LIMIT 5
            """
        ),
        params,
    )


    integrations = []


    for row in (
        integration_result
        .mappings()
        .all()
    ):
        raw = (
            row.get(
                "integration"
            )
            or {}
        )


        if not isinstance(
            raw,
            dict,
        ):
            try:
                raw = dict(
                    raw
                )
            except Exception:
                raw = {}


        integration_type = (
            raw.get(
                "integration_type"
            )
            or raw.get(
                "type"
            )
            or raw.get(
                "provider"
            )
            or raw.get(
                "provider_type"
            )
            or raw.get(
                "adapter_type"
            )
            or raw.get(
                "kind"
            )
            or raw.get(
                "name"
            )
            or "Hospital integration"
        )


        status = (
            raw.get(
                "status"
            )
            or raw.get(
                "connection_status"
            )
            or raw.get(
                "sync_status"
            )
        )


        if not status:
            active_value = raw.get(
                "is_active"
            )

            enabled_value = raw.get(
                "enabled"
            )

            connected_value = raw.get(
                "is_connected"
            )


            if (
                connected_value
                is True
            ):
                status = "connected"

            elif (
                active_value
                is True
                or enabled_value
                is True
            ):
                status = "active"

            elif (
                active_value
                is False
                or enabled_value
                is False
            ):
                status = "inactive"

            else:
                status = "configured"


        updated_at = (
            raw.get(
                "updated_at"
            )
            or raw.get(
                "last_synced_at"
            )
            or raw.get(
                "last_sync_at"
            )
            or raw.get(
                "created_at"
            )
        )


        if (
            updated_at is not None
            and hasattr(
                updated_at,
                "isoformat",
            )
        ):
            updated_at = (
                updated_at
                .isoformat()
            )


        integrations.append(
            {
                "type":
                    str(
                        integration_type
                    ),

                "status":
                    str(
                        status
                    ),

                "updated_at":
                    (
                        str(
                            updated_at
                        )
                        if updated_at
                        is not None
                        else None
                    ),
            }
        )



    return {
        "hospital": {
            "id":
                hospital_id,

            "slug":
                hospital[
                    "slug"
                ],

            "name":
                hospital[
                    "name"
                ],

            "active":
                bool(
                    hospital[
                        "is_active"
                    ]
                ),

            "timezone":
                hospital[
                    "timezone"
                ],
        },

        "metrics": {
            "doctors":
                int(
                    total_doctors
                    or 0
                ),

            "specialties":
                int(
                    specialty_count
                    or 0
                ),

            "appointments_today":
                int(
                    today_appointments
                    or 0
                ),

            "appointments_upcoming":
                int(
                    upcoming_appointments
                    or 0
                ),

            "appointments_confirmed":
                int(
                    confirmed_appointments
                    or 0
                ),

            "appointments_cancelled":
                int(
                    cancelled_appointments
                    or 0
                ),

            "appointments_rescheduled":
                int(
                    rescheduled_count
                    or 0
                ),

            "available_slots":
                int(
                    available_slots
                    or 0
                ),

            "unavailable_slots":
                int(
                    unavailable_slots
                    or 0
                ),
        },

        "recent_appointments":
            recent,

        "integrations":
            integrations,

        "generated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }


# ============================================================
# MEDIBOOK_HOSPITAL_APPOINTMENTS_WORKSPACE_V1
# ============================================================

@router.get(
    "/{hospital_slug}/appointments"
)
async def hospital_appointments(
    hospital_slug: str,
    current_user: CurrentUser,
    session: Annotated[
        AsyncSession,
        Depends(
            get_db_session
        ),
    ],
    status: str | None = Query(
        default=None
    ),
    date_from: date | None = Query(
        default=None
    ),
    date_to: date | None = Query(
        default=None
    ),
    search: str | None = Query(
        default=None,
        max_length=120,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
):
    hospital = await _hospital_row(
        session,
        hospital_slug,
    )

    if hospital is None:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found.",
        )


    hospital_id = str(
        hospital["id"]
    )


    await _require_access(
        session,
        current_user,
        hospital_id,
    )


    clauses = [
        "a.hospital_id = :hospital_id"
    ]


    params: dict = {
        "hospital_id":
            hospital_id,

        "limit":
            limit,
    }


    normalized_status = (
        status.strip().lower()
        if status
        else None
    )


    if (
        normalized_status
        and normalized_status
        != "all"
    ):
        clauses.append(
            "LOWER(a.status) = :status"
        )

        params[
            "status"
        ] = normalized_status


    if date_from is not None:
        clauses.append(
            "ds.slot_date >= :date_from"
        )

        params[
            "date_from"
        ] = date_from


    if date_to is not None:
        clauses.append(
            "ds.slot_date <= :date_to"
        )

        params[
            "date_to"
        ] = date_to


    normalized_search = (
        search.strip()
        if search
        else ""
    )


    if normalized_search:
        clauses.append(
            """
            (
                a.confirmation_code ILIKE :search
                OR d.full_name ILIKE :search
                OR CAST(a.id AS TEXT) ILIKE :search
                OR CAST(p.id AS TEXT) ILIKE :search
                OR row_to_json(p)::text ILIKE :search
            )
            """
        )

        params[
            "search"
        ] = (
            "%"
            + normalized_search
            + "%"
        )


    where_clause = (
        " AND ".join(
            clauses
        )
    )


    query = f"""
        SELECT
            a.id AS appointment_id,
            a.confirmation_code,
            a.status,
            a.booked_at,
            a.cancelled_at,

            d.id AS doctor_id,
            d.full_name AS doctor_name,

            ds.id AS slot_id,
            ds.slot_date,
            ds.start_time,

            row_to_json(p) AS patient

        FROM appointments a


        JOIN doctors d
          ON d.id = a.doctor_id

        JOIN patients p
          ON p.id = a.patient_id

        LEFT JOIN doctor_slots ds
          ON ds.id = a.doctor_slot_id

        WHERE {where_clause}

        ORDER BY
            ds.slot_date DESC NULLS LAST,
            ds.start_time DESC NULLS LAST,
            a.booked_at DESC

        LIMIT :limit
    """


    result = await session.execute(
        text(
            query
        ),
        params,
    )


    rows = []


    for row in (
        result
        .mappings()
        .all()
    ):
        patient_raw = (
            row.get(
                "patient"
            )
            or {}
        )


        if not isinstance(
            patient_raw,
            dict,
        ):
            try:
                patient_raw = dict(
                    patient_raw
                )
            except Exception:
                patient_raw = {}


        patient_name = (
            patient_raw.get(
                "full_name"
            )
            or patient_raw.get(
                "name"
            )
            or patient_raw.get(
                "patient_name"
            )
            or "Patient"
        )


        patient_phone = (
            patient_raw.get(
                "phone"
            )
            or patient_raw.get(
                "mobile"
            )
            or patient_raw.get(
                "phone_number"
            )
            or patient_raw.get(
                "mobile_number"
            )
        )


        patient_email = (
            patient_raw.get(
                "email"
            )
            or patient_raw.get(
                "email_address"
            )
        )


        rows.append(
            {
                "appointment_id":
                    str(
                        row[
                            "appointment_id"
                        ]
                    ),

                "confirmation_code":
                    row[
                        "confirmation_code"
                    ],

                "status":
                    row[
                        "status"
                    ],

                "doctor": {
                    "id":
                        str(
                            row[
                                "doctor_id"
                            ]
                        ),

                    "name":
                        row[
                            "doctor_name"
                        ],
                },

                "patient": {
                    "name":
                        str(
                            patient_name
                        ),

                    "phone":
                        (
                            str(
                                patient_phone
                            )
                            if patient_phone
                            is not None
                            else None
                        ),

                    "email":
                        (
                            str(
                                patient_email
                            )
                            if patient_email
                            is not None
                            else None
                        ),
                },

                "slot": {
                    "id":
                        (
                            str(
                                row[
                                    "slot_id"
                                ]
                            )
                            if row[
                                "slot_id"
                            ]
                            is not None
                            else None
                        ),

                    "date":
                        (
                            row[
                                "slot_date"
                            ].isoformat()
                            if row[
                                "slot_date"
                            ]
                            is not None
                            else None
                        ),

                    "time":
                        (
                            row[
                                "start_time"
                            ].strftime(
                                "%H:%M"
                            )
                            if row[
                                "start_time"
                            ]
                            is not None
                            else None
                        ),
                },

                "booked_at":
                    (
                        row[
                            "booked_at"
                        ].isoformat()
                        if row[
                            "booked_at"
                        ]
                        is not None
                        else None
                    ),

                "cancelled_at":
                    (
                        row[
                            "cancelled_at"
                        ].isoformat()
                        if row[
                            "cancelled_at"
                        ]
                        is not None
                        else None
                    ),
            }
        )


    return {
        "hospital": {
            "id":
                hospital_id,

            "slug":
                hospital[
                    "slug"
                ],

            "name":
                hospital[
                    "name"
                ],
        },

        "filters": {
            "status":
                normalized_status
                or "all",

            "date_from":
                (
                    date_from.isoformat()
                    if date_from
                    else None
                ),

            "date_to":
                (
                    date_to.isoformat()
                    if date_to
                    else None
                ),

            "search":
                normalized_search
                or None,

            "limit":
                limit,
        },

        "count":
            len(
                rows
            ),

        "appointments":
            rows,
    }
