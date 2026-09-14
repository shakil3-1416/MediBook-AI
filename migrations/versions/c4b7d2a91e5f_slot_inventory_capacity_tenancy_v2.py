"""slot inventory capacity tenancy v2

Revision ID: c4b7d2a91e5f
Revises: 89ea55589c71
"""

from alembic import op
import sqlalchemy as sa


revision = "c4b7d2a91e5f"
down_revision = "89ea55589c71"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "doctor_slots",
        sa.Column(
            "hospital_doctor_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.add_column(
        "doctor_slots",
        sa.Column(
            "capacity",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
    )

    op.add_column(
        "doctor_slots",
        sa.Column(
            "is_enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )

    op.execute(
        sa.text(
            "DO $$ "
            "DECLARE bad_count integer; "
            "BEGIN "
            "SELECT COUNT(*) INTO bad_count "
            "FROM doctor_slots ds "
            "WHERE ("
            "SELECT COUNT(*) "
            "FROM hospital_doctors hd "
            "WHERE hd.doctor_id = ds.doctor_id"
            ") <> 1; "
            "IF bad_count > 0 THEN "
            "RAISE EXCEPTION 'APP_SLOT_OWNERSHIP_AMBIGUOUS'; "
            "END IF; "
            "END $$"
        )
    )

    op.execute(
        sa.text(
            "UPDATE doctor_slots ds "
            "SET hospital_doctor_id = hd.id "
            "FROM hospital_doctors hd "
            "WHERE hd.doctor_id = ds.doctor_id"
        )
    )

    op.alter_column(
        "doctor_slots",
        "hospital_doctor_id",
        nullable=False,
    )

    op.create_foreign_key(
        "fk_doctor_slots_hospital_doctor",
        "doctor_slots",
        "hospital_doctors",
        ["hospital_doctor_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_doctor_slots_hospital_doctor_id",
        "doctor_slots",
        ["hospital_doctor_id"],
        unique=False,
    )

    op.create_check_constraint(
        "ck_doctor_slots_capacity",
        "doctor_slots",
        "capacity BETWEEN 1 AND 50",
    )

    op.drop_constraint(
        "uq_doctor_slot",
        "doctor_slots",
        type_="unique",
    )

    op.create_unique_constraint(
        "uq_hospital_doctor_slot",
        "doctor_slots",
        [
            "hospital_doctor_id",
            "slot_date",
            "start_time",
        ],
    )

    op.drop_index(
        "uq_active_appointment_slot",
        table_name="appointments",
    )

    op.create_index(
        "ix_active_appointment_slot",
        "appointments",
        ["doctor_slot_id"],
        unique=False,
        postgresql_where=sa.text(
            "status IN ('confirmed', 'checked_in')"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_active_appointment_slot",
        table_name="appointments",
    )

    op.create_index(
        "uq_active_appointment_slot",
        "appointments",
        ["doctor_slot_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('confirmed', 'checked_in')"
        ),
    )

    op.drop_constraint(
        "uq_hospital_doctor_slot",
        "doctor_slots",
        type_="unique",
    )

    op.create_unique_constraint(
        "uq_doctor_slot",
        "doctor_slots",
        [
            "doctor_id",
            "slot_date",
            "start_time",
        ],
    )

    op.drop_constraint(
        "ck_doctor_slots_capacity",
        "doctor_slots",
        type_="check",
    )

    op.drop_index(
        "ix_doctor_slots_hospital_doctor_id",
        table_name="doctor_slots",
    )

    op.drop_constraint(
        "fk_doctor_slots_hospital_doctor",
        "doctor_slots",
        type_="foreignkey",
    )

    op.drop_column(
        "doctor_slots",
        "is_enabled",
    )

    op.drop_column(
        "doctor_slots",
        "capacity",
    )

    op.drop_column(
        "doctor_slots",
        "hospital_doctor_id",
    )
