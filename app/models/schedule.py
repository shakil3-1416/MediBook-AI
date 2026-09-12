from datetime import date, time
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DoctorSlot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "doctor_slots"

    __table_args__ = (
        UniqueConstraint(
            "doctor_id",
            "slot_date",
            "start_time",
            name="uq_doctor_slot",
        ),
    )

    doctor_id: Mapped[UUID] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    slot_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    doctor: Mapped["Doctor"] = relationship(
        back_populates="slots",
    )
