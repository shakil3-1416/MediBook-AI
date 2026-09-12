from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Specialty(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "specialties"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    doctors: Mapped[list["Doctor"]] = relationship(
        back_populates="specialty",
    )


class Doctor(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "doctors"

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    gender: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )

    qualification: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    experience_years: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    specialty_id: Mapped[UUID] = mapped_column(
        ForeignKey("specialties.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    clinic_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    clinic_location: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
        index=True,
    )

    consultation_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    specialty: Mapped["Specialty"] = relationship(
        back_populates="doctors",
    )

    slots: Mapped[list["DoctorSlot"]] = relationship(
        back_populates="doctor",
        cascade="all, delete-orphan",
    )
