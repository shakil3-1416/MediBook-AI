"""integration center v1

Revision ID: e82a61fc9470
Revises: c4b7d2a91e5f
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e82a61fc9470"
down_revision = "c4b7d2a91e5f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "hospital_integrations",
        sa.Column(
            "integration_type",
            sa.String(64),
            nullable=False,
            server_default="custom",
        ),
    )

    op.add_column(
        "hospital_integrations",
        sa.Column(
            "source_mode",
            sa.String(32),
            nullable=False,
            server_default="managed",
        ),
    )

    op.add_column(
        "hospital_integrations",
        sa.Column(
            "sync_status",
            sa.String(32),
            nullable=False,
            server_default="idle",
        ),
    )

    op.add_column(
        "hospital_integrations",
        sa.Column(
            "ownership",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    op.add_column(
        "hospital_integrations",
        sa.Column(
            "last_sync_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "hospital_integrations",
        sa.Column(
            "last_error",
            sa.String(500),
            nullable=True,
        ),
    )

    op.add_column(
        "hospital_integrations",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.create_check_constraint(
        "ck_hospital_integrations_source_mode",
        "hospital_integrations",
        "source_mode IN ('managed', 'connected', 'hybrid')",
    )

    op.create_check_constraint(
        "ck_hospital_integrations_sync_status",
        "hospital_integrations",
        "sync_status IN ('idle', 'running', 'succeeded', 'failed')",
    )

    op.create_index(
        "ix_hospital_integrations_hospital_status",
        "hospital_integrations",
        ["hospital_id", "status"],
    )


def downgrade():
    op.drop_index(
        "ix_hospital_integrations_hospital_status",
        table_name="hospital_integrations",
    )

    op.drop_constraint(
        "ck_hospital_integrations_sync_status",
        "hospital_integrations",
        type_="check",
    )

    op.drop_constraint(
        "ck_hospital_integrations_source_mode",
        "hospital_integrations",
        type_="check",
    )

    for name in (
        "is_active",
        "last_error",
        "last_sync_at",
        "ownership",
        "sync_status",
        "source_mode",
        "integration_type",
    ):
        op.drop_column(
            "hospital_integrations",
            name,
        )
