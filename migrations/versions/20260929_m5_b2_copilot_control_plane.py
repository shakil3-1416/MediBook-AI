"""M5-B2 hospital Copilot control plane.

Revision ID: m5b2copilot20260929
Revises: e82a61fc9470
Create Date: 2026-09-29
"""

from alembic import op
import sqlalchemy as sa


revision = "m5b2copilot20260929"
down_revision = "e82a61fc9470"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hospital_copilot_proposals",

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
            "created_by_user_id",
            sa.String(length=36),
            nullable=False,
        ),

        sa.Column(
            "action_type",
            sa.String(length=64),
            nullable=False,
        ),

        sa.Column(
            "payload",
            sa.JSON(),
            nullable=False,
        ),

        sa.Column(
            "impact",
            sa.JSON(),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),

        sa.Column(
            "execution_supported",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        sa.Column(
            "execution_result",
            sa.JSON(),
            nullable=True,
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
            "confirmed_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.Column(
            "executed_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.Column(
            "cancelled_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
    )


    op.create_index(
        "ix_copilot_proposals_hospital_status",
        "hospital_copilot_proposals",
        [
            "hospital_id",
            "status",
        ],
    )


    op.create_table(
        "hospital_copilot_events",

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
            "user_id",
            sa.String(length=36),
            nullable=False,
        ),

        sa.Column(
            "event_type",
            sa.String(length=64),
            nullable=False,
        ),

        sa.Column(
            "proposal_id",
            sa.String(length=36),
            nullable=True,
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
        "ix_copilot_events_hospital_created",
        "hospital_copilot_events",
        [
            "hospital_id",
            "created_at",
        ],
    )


    op.create_index(
        "ix_copilot_events_proposal_id",
        "hospital_copilot_events",
        [
            "proposal_id",
        ],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_copilot_events_proposal_id",
        table_name=
            "hospital_copilot_events",
    )

    op.drop_index(
        "ix_copilot_events_hospital_created",
        table_name=
            "hospital_copilot_events",
    )

    op.drop_table(
        "hospital_copilot_events"
    )

    op.drop_index(
        "ix_copilot_proposals_hospital_status",
        table_name=
            "hospital_copilot_proposals",
    )

    op.drop_table(
        "hospital_copilot_proposals"
    )
