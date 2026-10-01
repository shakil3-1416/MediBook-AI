"""M6-B2 durable sync queue and retry runtime.

Revision ID: m6b2queue20260930
Revises: m6b1sync20260930
Create Date: 2026-09-30
"""

from alembic import op
import sqlalchemy as sa


revision = "m6b2queue20260930"
down_revision = "m6b1sync20260930"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "integration_sync_runs",
        sa.Column(
            "max_attempts",
            sa.Integer(),
            nullable=False,
            server_default="3",
        ),
    )

    op.add_column(
        "integration_sync_runs",
        sa.Column(
            "next_attempt_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
    )

    op.add_column(
        "integration_sync_runs",
        sa.Column(
            "heartbeat_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
    )

    op.add_column(
        "integration_sync_runs",
        sa.Column(
            "claimed_by",
            sa.String(length=120),
            nullable=True,
        ),
    )

    op.add_column(
        "integration_sync_runs",
        sa.Column(
            "last_attempt_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_integration_sync_runs_queue",
        "integration_sync_runs",
        [
            "status",
            "next_attempt_at",
            "created_at",
        ],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_integration_sync_runs_queue",
        table_name=
            "integration_sync_runs",
    )

    op.drop_column(
        "integration_sync_runs",
        "last_attempt_at",
    )

    op.drop_column(
        "integration_sync_runs",
        "claimed_by",
    )

    op.drop_column(
        "integration_sync_runs",
        "heartbeat_at",
    )

    op.drop_column(
        "integration_sync_runs",
        "next_attempt_at",
    )

    op.drop_column(
        "integration_sync_runs",
        "max_attempts",
    )
