"""add multi hospital foundation

Revision ID: 1cc15c164b86
Revises: bef3f8952bdd
Create Date: 2026-08-29 00:39:16.004729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1cc15c164b86'
down_revision: Union[str, Sequence[str], None] = 'bef3f8952bdd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.create_table(
        "hospitals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "slug",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "timezone",
            sa.String(length=64),
            nullable=False,
            server_default="Asia/Dhaka",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "slug",
            name="uq_hospitals_slug",
        ),
    )

    op.create_table(
        "hospital_memberships",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "hospital_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "hospitals.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(length=32),
            nullable=False,
            server_default="hospital_staff",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "hospital_id",
            "user_id",
            name="uq_hospital_membership",
        ),
    )

    op.create_table(
        "hospital_doctors",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "hospital_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "hospitals.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "doctor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "doctors.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "hospital_id",
            "doctor_id",
            name="uq_hospital_doctor",
        ),
    )

    op.create_table(
        "hospital_integrations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "hospital_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "hospitals.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "provider",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="not_configured",
        ),
        sa.Column(
            "config",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "last_checked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "hospital_id",
            "provider",
            name="uq_hospital_integration",
        ),
    )

    op.execute(
        """
        INSERT INTO hospitals (
            id,
            slug,
            name,
            status,
            timezone,
            is_active,
            created_at,
            updated_at
        )
        VALUES (
            '00000000-0000-0000-0000-000000000001',
            'medibook-demo',
            'MediBook Demo Hospital',
            'active',
            'Asia/Dhaka',
            TRUE,
            NOW(),
            NOW()
        )
        ON CONFLICT (slug) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO hospital_doctors (
            id,
            hospital_id,
            doctor_id,
            created_at
        )
        SELECT
            gen_random_uuid(),
            '00000000-0000-0000-0000-000000000001',
            id,
            NOW()
        FROM doctors
        ON CONFLICT (
            hospital_id,
            doctor_id
        )
        DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table(
        "hospital_integrations"
    )

    op.drop_table(
        "hospital_doctors"
    )

    op.drop_table(
        "hospital_memberships"
    )

    op.drop_table(
        "hospitals"
    )
