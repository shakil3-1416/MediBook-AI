"""identity v2 verification challenges

Revision ID: 2c91d8f4e6a2
Revises: 1b14e313de7d
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "2c91d8f4e6a2"
down_revision = "1b14e313de7d"
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.create_table(
        "identity_verification_challenges",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "purpose",
            sa.String(
                length=32
            ),
            nullable=False,
        ),

        sa.Column(
            "user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "email",
            sa.String(
                length=320
            ),
            nullable=False,
        ),

        sa.Column(
            "code_hash",
            sa.String(
                length=64
            ),
            nullable=False,
        ),

        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "expires_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        sa.Column(
            "resend_available_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        sa.Column(
            "consumed_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_identity_verification_user_purpose",
        "identity_verification_challenges",
        [
            "user_id",
            "purpose",
        ],
    )

    op.create_index(
        "ix_identity_verification_email",
        "identity_verification_challenges",
        [
            "email",
        ],
    )


def downgrade() -> None:

    op.drop_index(
        "ix_identity_verification_email",
        table_name=(
            "identity_verification_challenges"
        ),
    )

    op.drop_index(
        "ix_identity_verification_user_purpose",
        table_name=(
            "identity_verification_challenges"
        ),
    )

    op.drop_table(
        "identity_verification_challenges"
    )
