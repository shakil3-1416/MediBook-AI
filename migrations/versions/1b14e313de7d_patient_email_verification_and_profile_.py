"""patient email verification and profile identity"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1b14e313de7d"
down_revision: Union[str, None] = "1cc15c164b86"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "gender",
            sa.String(length=32),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "profile_image_url",
            sa.String(length=1000),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "email_verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Existing users were created before OTP existed.
    # Preserve their access.
    op.execute(
        """
        UPDATE users
        SET email_verified_at = NOW()
        WHERE email_verified_at IS NULL
        """
    )

    op.create_table(
        "email_verification_challenges",

        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
        ),

        sa.Column(
            "email",
            sa.String(length=320),
            nullable=False,
        ),

        sa.Column(
            "full_name",
            sa.String(length=200),
            nullable=False,
        ),

        sa.Column(
            "phone",
            sa.String(length=32),
            nullable=False,
        ),

        sa.Column(
            "gender",
            sa.String(length=32),
            nullable=False,
        ),

        sa.Column(
            "password_hash",
            sa.String(length=500),
            nullable=False,
        ),

        sa.Column(
            "profile_image_url",
            sa.String(length=1000),
            nullable=True,
        ),

        sa.Column(
            "code_hash",
            sa.String(length=128),
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
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "resend_available_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index(
        "ix_email_verification_challenges_email",
        "email_verification_challenges",
        ["email"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_email_verification_challenges_email",
        table_name="email_verification_challenges",
    )

    op.drop_table(
        "email_verification_challenges",
    )

    op.drop_column(
        "users",
        "email_verified_at",
    )

    op.drop_column(
        "users",
        "profile_image_url",
    )

    op.drop_column(
        "users",
        "gender",
    )
