"""hospital control plane schema v1

Revision ID: 89ea55589c71
Revises: 3f7a2b91c6d4
Create Date: 2026-09-13 11:12:21.167214
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "89ea55589c71"
down_revision: Union[str, Sequence[str], None] = "3f7a2b91c6d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hospital_operations_audit",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("hospital_id", sa.UUID(), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=True),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("before_state", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("after_state", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hospital_operations_audit_action", "hospital_operations_audit", ["action"], unique=False)
    op.create_index("ix_hospital_operations_audit_actor_user_id", "hospital_operations_audit", ["actor_user_id"], unique=False)
    op.create_index("ix_hospital_operations_audit_entity_id", "hospital_operations_audit", ["entity_id"], unique=False)
    op.create_index("ix_hospital_operations_audit_entity_type", "hospital_operations_audit", ["entity_type"], unique=False)
    op.create_index("ix_hospital_operations_audit_hospital_id", "hospital_operations_audit", ["hospital_id"], unique=False)
    op.create_index("ix_hospital_ops_audit_hospital_created", "hospital_operations_audit", ["hospital_id", "created_at"], unique=False)

    op.add_column("hospital_doctors", sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False))
    op.add_column("hospital_doctors", sa.Column("source_mode", sa.String(length=32), server_default=sa.text("'managed'"), nullable=False))
    op.add_column("hospital_doctors", sa.Column("external_doctor_id", sa.String(length=255), nullable=True))
    op.add_column("hospital_doctors", sa.Column("clinic_name", sa.String(length=200), nullable=True))
    op.add_column("hospital_doctors", sa.Column("clinic_location", sa.String(length=250), nullable=True))
    op.add_column("hospital_doctors", sa.Column("consultation_fee", sa.Numeric(10, 2), nullable=True))
    op.add_column("hospital_doctors", sa.Column("public_profile", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False))
    op.add_column("hospital_doctors", sa.Column("operational_metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False))
    op.add_column("hospital_doctors", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))

    op.execute("""
        UPDATE hospital_doctors AS hd
        SET clinic_name = d.clinic_name,
            clinic_location = d.clinic_location,
            consultation_fee = d.consultation_fee
        FROM doctors AS d
        WHERE d.id = hd.doctor_id
    """)

    op.create_index("ix_hospital_doctors_doctor_id", "hospital_doctors", ["doctor_id"], unique=False)
    op.create_index("ix_hospital_doctors_hospital_id", "hospital_doctors", ["hospital_id"], unique=False)
    op.create_index("ix_hospital_doctors_external_doctor_id", "hospital_doctors", ["external_doctor_id"], unique=False)
    op.create_index("ix_hospital_doctors_is_active", "hospital_doctors", ["is_active"], unique=False)
    op.create_index("ix_hospital_doctors_source_mode", "hospital_doctors", ["source_mode"], unique=False)
    op.create_unique_constraint("uq_hospital_doctor_external_id", "hospital_doctors", ["hospital_id", "external_doctor_id"])
    op.create_check_constraint("ck_hospital_doctors_source_mode", "hospital_doctors", "source_mode IN ('managed', 'connected', 'hybrid')")

    op.create_table(
        "doctor_schedule_exceptions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("hospital_doctor_id", sa.UUID(), nullable=False),
        sa.Column("exception_date", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("slot_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("kind IN ('leave', 'closure', 'override', 'unavailable')", name="ck_schedule_exception_kind"),
        sa.CheckConstraint("(start_time IS NULL AND end_time IS NULL) OR (start_time IS NOT NULL AND end_time IS NOT NULL AND start_time < end_time)", name="ck_schedule_exception_time"),
        sa.CheckConstraint("capacity IS NULL OR capacity BETWEEN 1 AND 50", name="ck_schedule_exception_capacity"),
        sa.CheckConstraint("slot_duration_minutes IS NULL OR slot_duration_minutes BETWEEN 5 AND 240", name="ck_schedule_exception_duration"),
        sa.ForeignKeyConstraint(["hospital_doctor_id"], ["hospital_doctors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doctor_schedule_exceptions_exception_date", "doctor_schedule_exceptions", ["exception_date"], unique=False)
    op.create_index("ix_doctor_schedule_exceptions_hospital_doctor_id", "doctor_schedule_exceptions", ["hospital_doctor_id"], unique=False)
    op.create_index("ix_doctor_schedule_exceptions_is_active", "doctor_schedule_exceptions", ["is_active"], unique=False)
    op.create_index("ix_schedule_exception_hospital_doctor_date", "doctor_schedule_exceptions", ["hospital_doctor_id", "exception_date"], unique=False)

    op.create_table(
        "doctor_schedule_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("hospital_doctor_id", sa.UUID(), nullable=False),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("slot_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("capacity", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("capacity BETWEEN 1 AND 50", name="ck_schedule_rule_capacity"),
        sa.CheckConstraint("slot_duration_minutes BETWEEN 5 AND 240", name="ck_schedule_rule_duration"),
        sa.CheckConstraint("start_time < end_time", name="ck_schedule_rule_time"),
        sa.CheckConstraint("valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from", name="ck_schedule_rule_dates"),
        sa.CheckConstraint("weekday BETWEEN 0 AND 6", name="ck_schedule_rule_weekday"),
        sa.ForeignKeyConstraint(["hospital_doctor_id"], ["hospital_doctors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doctor_schedule_rules_hospital_doctor_id", "doctor_schedule_rules", ["hospital_doctor_id"], unique=False)
    op.create_index("ix_doctor_schedule_rules_is_active", "doctor_schedule_rules", ["is_active"], unique=False)
    op.create_index("ix_schedule_rule_hospital_doctor_active", "doctor_schedule_rules", ["hospital_doctor_id", "is_active"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_schedule_rule_hospital_doctor_active", table_name="doctor_schedule_rules")
    op.drop_index("ix_doctor_schedule_rules_is_active", table_name="doctor_schedule_rules")
    op.drop_index("ix_doctor_schedule_rules_hospital_doctor_id", table_name="doctor_schedule_rules")
    op.drop_table("doctor_schedule_rules")

    op.drop_index("ix_schedule_exception_hospital_doctor_date", table_name="doctor_schedule_exceptions")
    op.drop_index("ix_doctor_schedule_exceptions_is_active", table_name="doctor_schedule_exceptions")
    op.drop_index("ix_doctor_schedule_exceptions_hospital_doctor_id", table_name="doctor_schedule_exceptions")
    op.drop_index("ix_doctor_schedule_exceptions_exception_date", table_name="doctor_schedule_exceptions")
    op.drop_table("doctor_schedule_exceptions")

    op.drop_constraint("ck_hospital_doctors_source_mode", "hospital_doctors", type_="check")
    op.drop_constraint("uq_hospital_doctor_external_id", "hospital_doctors", type_="unique")
    op.drop_index("ix_hospital_doctors_source_mode", table_name="hospital_doctors")
    op.drop_index("ix_hospital_doctors_is_active", table_name="hospital_doctors")
    op.drop_index("ix_hospital_doctors_external_doctor_id", table_name="hospital_doctors")
    op.drop_index("ix_hospital_doctors_hospital_id", table_name="hospital_doctors")
    op.drop_index("ix_hospital_doctors_doctor_id", table_name="hospital_doctors")
    op.drop_column("hospital_doctors", "updated_at")
    op.drop_column("hospital_doctors", "operational_metadata")
    op.drop_column("hospital_doctors", "public_profile")
    op.drop_column("hospital_doctors", "consultation_fee")
    op.drop_column("hospital_doctors", "clinic_location")
    op.drop_column("hospital_doctors", "clinic_name")
    op.drop_column("hospital_doctors", "external_doctor_id")
    op.drop_column("hospital_doctors", "source_mode")
    op.drop_column("hospital_doctors", "is_active")

    op.drop_index("ix_hospital_ops_audit_hospital_created", table_name="hospital_operations_audit")
    op.drop_index("ix_hospital_operations_audit_hospital_id", table_name="hospital_operations_audit")
    op.drop_index("ix_hospital_operations_audit_entity_type", table_name="hospital_operations_audit")
    op.drop_index("ix_hospital_operations_audit_entity_id", table_name="hospital_operations_audit")
    op.drop_index("ix_hospital_operations_audit_actor_user_id", table_name="hospital_operations_audit")
    op.drop_index("ix_hospital_operations_audit_action", table_name="hospital_operations_audit")
    op.drop_table("hospital_operations_audit")
