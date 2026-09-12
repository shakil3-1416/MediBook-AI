"""durable appointment hospital tenancy

Revision ID: 3f7a2b91c6d4
Revises: 2c91d8f4e6a2
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "3f7a2b91c6d4"
down_revision = "2c91d8f4e6a2"
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.add_column(
        "appointments",
        sa.Column(
            "hospital_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.execute(
        sa.text(
            """
            WITH resolved AS (
                SELECT
                    a.id AS appointment_id,
                    MIN(hd.hospital_id::text)::uuid
                        AS hospital_id
                FROM appointments a
                JOIN hospital_doctors hd
                  ON hd.doctor_id = a.doctor_id
                GROUP BY a.id
                HAVING COUNT(
                    DISTINCT hd.hospital_id
                ) = 1
            )
            UPDATE appointments a
            SET hospital_id = resolved.hospital_id
            FROM resolved
            WHERE resolved.appointment_id = a.id
            """
        )
    )

    bind = op.get_bind()

    unresolved = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM appointments
            WHERE hospital_id IS NULL
            """
        )
    ).scalar_one()

    if unresolved:
        raise RuntimeError(
            "Appointment hospital backfill "
            f"left {unresolved} unresolved rows."
        )

    op.alter_column(
        "appointments",
        "hospital_id",
        existing_type=postgresql.UUID(
            as_uuid=True
        ),
        nullable=False,
    )

    op.create_foreign_key(
        "fk_appointments_hospital_id_hospitals",
        "appointments",
        "hospitals",
        ["hospital_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.create_index(
        "ix_appointments_hospital_id",
        "appointments",
        ["hospital_id"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_appointments_hospital_id",
        table_name="appointments",
    )

    op.drop_constraint(
        "fk_appointments_hospital_id_hospitals",
        "appointments",
        type_="foreignkey",
    )

    op.drop_column(
        "appointments",
        "hospital_id",
    )
