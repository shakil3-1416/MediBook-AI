from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.appointment import Appointment
from app.models.schedule import DoctorSlot
from app.services.appointment_service import AppointmentService


def test_slot_capacity_schema_contract():
    columns = DoctorSlot.__table__.columns

    assert "hospital_doctor_id" in columns
    assert "capacity" in columns
    assert "is_enabled" in columns


def test_active_appointment_index_is_not_unique():
    index = next(
        item
        for item in Appointment.__table__.indexes
        if item.name == "ix_active_appointment_slot"
    )

    assert index.unique is False


@pytest.mark.asyncio
async def test_refresh_slot_availability_with_remaining_capacity():
    service = object.__new__(
        AppointmentService
    )

    service.active_slot_count = AsyncMock(
        return_value=1
    )

    slot = SimpleNamespace(
        id=uuid4(),
        capacity=2,
        is_enabled=True,
        is_available=False,
    )

    active = await service.refresh_slot_availability(
        slot=slot,
    )

    assert active == 1
    assert slot.is_available is True


@pytest.mark.asyncio
async def test_refresh_slot_availability_when_full():
    service = object.__new__(
        AppointmentService
    )

    service.active_slot_count = AsyncMock(
        return_value=2
    )

    slot = SimpleNamespace(
        id=uuid4(),
        capacity=2,
        is_enabled=True,
        is_available=True,
    )

    await service.refresh_slot_availability(
        slot=slot,
    )

    assert slot.is_available is False


@pytest.mark.asyncio
async def test_disabled_slot_never_becomes_available():
    service = object.__new__(
        AppointmentService
    )

    service.active_slot_count = AsyncMock(
        return_value=0
    )

    slot = SimpleNamespace(
        id=uuid4(),
        capacity=5,
        is_enabled=False,
        is_available=True,
    )

    await service.refresh_slot_availability(
        slot=slot,
    )

    assert slot.is_available is False


def test_booking_engine_uses_row_lock_and_capacity():
    from pathlib import Path

    source = Path(
        "app/services/appointment_service.py"
    ).read_text()

    assert ".with_for_update()" in source
    assert "active_count >= slot.capacity" in source
    assert "destination_count >= new_slot.capacity" in source
    assert "refresh_slot_availability" in source
