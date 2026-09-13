from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.main import app
from app.services.hospital_doctor_registry import (
    HospitalDoctorRegistryService,
)


def test_doctor_registry_routes_are_registered():
    paths = app.openapi()["paths"]

    assert (
        "/api/v1/hospital-operations/{hospital_slug}/doctors"
        in paths
    )

    assert (
        "/api/v1/hospital-operations/{hospital_slug}/doctors/{doctor_id}"
        in paths
    )

    assert (
        "/api/v1/hospital-operations/{hospital_slug}/doctors/{doctor_id}/activation"
        in paths
    )


def test_source_modes_are_strict():
    service = HospitalDoctorRegistryService

    assert service.validate_source_mode("managed") == "managed"
    assert service.validate_source_mode("CONNECTED") == "connected"
    assert service.validate_source_mode(" hybrid ") == "hybrid"

    with pytest.raises(ValueError):
        service.validate_source_mode("unknown")


def test_connected_doctor_requires_external_identity():
    service = HospitalDoctorRegistryService

    service.validate_external_identity(
        source_mode="managed",
        external_doctor_id=None,
    )

    service.validate_external_identity(
        source_mode="hybrid",
        external_doctor_id=None,
    )

    service.validate_external_identity(
        source_mode="connected",
        external_doctor_id="EXT-123",
    )

    with pytest.raises(ValueError):
        service.validate_external_identity(
            source_mode="connected",
            external_doctor_id=None,
        )

    with pytest.raises(ValueError):
        service.validate_external_identity(
            source_mode="connected",
            external_doctor_id="   ",
        )


def test_registry_serialization_prefers_hospital_specific_fields():
    doctor_id = uuid4()
    specialty_id = uuid4()
    mapping_id = uuid4()

    doctor = SimpleNamespace(
        id=doctor_id,
        full_name="Dr Registry",
        specialty_id=specialty_id,
        specialty=SimpleNamespace(
            name="Cardiology",
        ),
        gender="female",
        qualification="MBBS",
        experience_years=12,
    )

    mapping = SimpleNamespace(
        id=mapping_id,
        clinic_name="Hospital Chamber",
        clinic_location="Dhaka",
        consultation_fee=Decimal("1700"),
        source_mode="managed",
        external_doctor_id=None,
        is_active=True,
        public_profile={
            "bio": "Public profile",
        },
        operational_metadata={
            "internal_code": "D-100",
        },
    )

    result = HospitalDoctorRegistryService.serialize(
        doctor,
        mapping,
    )

    assert result["hospital_doctor_id"] == mapping_id
    assert result["doctor_id"] == doctor_id
    assert result["specialty_name"] == "Cardiology"
    assert result["clinic_name"] == "Hospital Chamber"
    assert result["clinic_location"] == "Dhaka"
    assert result["consultation_fee"] == Decimal("1700")
    assert result["source_mode"] == "managed"


def test_patient_directory_uses_active_hospital_doctor_guard():
    source = (
        __import__(
            "pathlib"
        )
        .Path(
            "app/services/hospital_directory_service.py"
        )
        .read_text()
    )

    assert "require_active_hospital_doctor" in source
    assert "HospitalDoctor.is_active.is_(True)" in source


def test_registry_has_no_destructive_delete_route():
    paths = app.openapi()["paths"]

    collection = paths[
        "/api/v1/hospital-operations/{hospital_slug}/doctors"
    ]

    item = paths[
        "/api/v1/hospital-operations/{hospital_slug}/doctors/{doctor_id}"
    ]

    assert "delete" not in collection
    assert "delete" not in item
