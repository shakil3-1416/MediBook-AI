from datetime import date, time
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.hospital_schedule_engine import (
    HospitalScheduleEngine,
    ScheduleOwnershipError,
)


def test_connected_schedule_is_read_only():
    mapping = SimpleNamespace(
        source_mode="connected"
    )

    with pytest.raises(
        ScheduleOwnershipError
    ):
        (
            HospitalScheduleEngine
            .assert_local_schedule_writable(
                mapping
            )
        )


def test_managed_schedule_is_writable():
    mapping = SimpleNamespace(
        source_mode="managed"
    )

    (
        HospitalScheduleEngine
        .assert_local_schedule_writable(
            mapping
        )
    )


def test_hybrid_schedule_is_writable():
    mapping = SimpleNamespace(
        source_mode="hybrid"
    )

    (
        HospitalScheduleEngine
        .assert_local_schedule_writable(
            mapping
        )
    )


def test_window_materialization():
    slots = (
        HospitalScheduleEngine
        ._generate_window(
            slot_date=date(
                2026,
                9,
                14,
            ),
            start_time=time(
                9,
                0,
            ),
            end_time=time(
                10,
                0,
            ),
            duration=20,
            capacity=2,
        )
    )

    assert len(slots) == 3

    assert [
        item["start_time"]
        for item in slots
    ] == [
        time(9, 0),
        time(9, 20),
        time(9, 40),
    ]

    assert all(
        item["capacity"] == 2
        for item in slots
    )


def test_partial_exception_overlap():
    exception = SimpleNamespace(
        start_time=time(9, 20),
        end_time=time(9, 40),
    )

    assert (
        HospitalScheduleEngine
        ._overlaps(
            {
                "start_time": time(9, 20),
                "end_time": time(9, 40),
            },
            exception,
        )
    )


def test_full_day_exception_overlap():
    exception = SimpleNamespace(
        start_time=None,
        end_time=None,
    )

    assert (
        HospitalScheduleEngine
        ._overlaps(
            {
                "start_time": time(9, 0),
                "end_time": time(9, 20),
            },
            exception,
        )
    )


def test_schedule_routes_registered():
    from app.main import app

    paths = app.openapi()["paths"]

    prefix = (
        "/api/v1/hospital-operations/"
        "{hospital_slug}/doctors/"
        "{doctor_id}/schedule"
    )

    assert prefix in paths
    assert prefix + "/rules" in paths
    assert prefix + "/exceptions" in paths
    assert prefix + "/preview" in paths
    assert prefix + "/apply" in paths


def test_schedule_apply_has_no_force_override():
    from pathlib import Path

    source = Path(
        "app/api/v1/hospital_schedules.py"
    ).read_text()

    assert "force=" not in source
    assert "force: bool" not in source


def test_slot_tenancy_uses_hospital_doctor():
    from pathlib import Path

    source = Path(
        "app/services/appointment_service.py"
    ).read_text()

    assert (
        "HospitalDoctor.id"
        in source
    )

    assert (
        "DoctorSlot.hospital_doctor_id"
        in source
    )
