"""M5-C platform control center.

Revision ID: m5ccontrol20260929
Revises: m5b2copilot20260929
Create Date: 2026-09-29
"""

from alembic import op
import sqlalchemy as sa


revision = "m5ccontrol20260929"
down_revision = "m5b2copilot20260929"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_control_events",

        sa.Column(
            "id",
            sa.String(length=36),
            primary_key=True,
        ),

        sa.Column(
            "hospital_id",
            sa.String(length=36),
            nullable=True,
        ),

        sa.Column(
            "actor_user_id",
            sa.String(length=36),
            nullable=False,
        ),

        sa.Column(
            "event_type",
            sa.String(length=80),
            nullable=False,
        ),

        sa.Column(
            "detail",
            sa.JSON(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=
                sa.func.now(),
        ),
    )

    op.create_index(
        "ix_platform_control_events_hospital_created",
        "platform_control_events",
        [
            "hospital_id",
            "created_at",
        ],
    )

    op.create_index(
        "ix_platform_control_events_actor_created",
        "platform_control_events",
        [
            "actor_user_id",
            "created_at",
        ],
    )

    op.create_table(
        "hospital_platform_settings",

        sa.Column(
            "hospital_id",
            sa.String(length=36),
            primary_key=True,
        ),

        sa.Column(
            "data_mode",
            sa.String(length=32),
            nullable=False,
            server_default="managed",
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=
                sa.func.now(),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=
                sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table(
        "hospital_platform_settings"
    )

    op.drop_index(
        "ix_platform_control_events_actor_created",
        table_name=
            "platform_control_events",
    )

    op.drop_index(
        "ix_platform_control_events_hospital_created",
        table_name=
            "platform_control_events",
    )

    op.drop_table(
        "platform_control_events"
    )
