from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Appointment(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
):
    __tablename__ = "appointments"

    doctor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "doctors.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    doctor_slot_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "doctor_slots.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "patients.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    hospital_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "hospitals.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    consultation_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="confirmed",
        index=True,
    )

    confirmation_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        unique=True,
        index=True,
    )

    booked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    doctor = relationship(
        "Doctor",
    )

    slot = relationship(
        "DoctorSlot",
    )

    patient = relationship(
        "Patient",
    )

    __table_args__ = (
        Index(
            "ix_active_appointment_slot",
            "doctor_slot_id",
            unique=False,
            postgresql_where=text(
                "status IN ('confirmed', 'checked_in')"
            ),
        ),
    )
