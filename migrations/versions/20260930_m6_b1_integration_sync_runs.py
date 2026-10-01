"""M6-B1 durable integration sync runs.

Revision ID: m6b1sync20260930
Revises: m5ccontrol20260929
Create Date: 2026-09-30
"""

from alembic import op
import sqlalchemy as sa


revision = "m6b1sync20260930"
down_revision = "m5ccontrol20260929"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_sync_runs",

        sa.Column(
            "id",
            sa.String(length=36),
            primary_key=True,
        ),

        sa.Column(
            "hospital_id",
            sa.String(length=36),
            nullable=False,
        ),

        sa.Column(
            "integration_id",
            sa.String(length=36),
            nullable=False,
        ),

        sa.Column(
            "provider",
            sa.String(length=64),
            nullable=False,
        ),

        sa.Column(
            "resource",
            sa.String(length=80),
            nullable=False,
        ),

        sa.Column(
            "direction",
            sa.String(length=16),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(length=24),
            nullable=False,
        ),

        sa.Column(
            "idempotency_key",
            sa.String(length=200),
            nullable=False,
        ),

        sa.Column(
            "attempt",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),

        sa.Column(
            "records_seen",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "records_changed",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "last_error",
            sa.String(length=1000),
            nullable=True,
        ),

        sa.Column(
            "result",
            sa.JSON(),
            nullable=False,
            server_default=sa.text(
                "'{}'::json"
            ),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.Column(
            "started_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.Column(
            "completed_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.UniqueConstraint(
            "integration_id",
            "idempotency_key",
            name=
                "uq_integration_sync_runs_idempotency",
        ),
    )

    op.create_index(
        "ix_integration_sync_runs_hospital_created",
        "integration_sync_runs",
        [
            "hospital_id",
            "created_at",
        ],
    )

    op.create_index(
        "ix_integration_sync_runs_integration_created",
        "integration_sync_runs",
        [
            "integration_id",
            "created_at",
        ],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_integration_sync_runs_integration_created",
        table_name=
            "integration_sync_runs",
    )

    op.drop_index(
        "ix_integration_sync_runs_hospital_created",
        table_name=
            "integration_sync_runs",
    )

    op.drop_table(
        "integration_sync_runs"
    )
