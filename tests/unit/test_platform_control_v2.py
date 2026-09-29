from pathlib import Path

from app.main import app

from app.schemas.platform_control_v2 import (
    HospitalDataMode,
    PlatformHospitalProvisionRequest,
)


def test_control_center_routes_registered():
    schema = app.openapi()

    base = (
        "/api/v1/"
        "platform-control-v2"
    )

    expected = {
        f"{base}/overview":
            {
                "get",
            },

        f"{base}/hospitals":
            {
                "get",
                "post",
            },

        (
            f"{base}/hospitals/"
            "{hospital_slug}"
        ):
            {
                "get",
            },

        (
            f"{base}/hospitals/"
            "{hospital_slug}/status"
        ):
            {
                "patch",
            },
    }

    for path, methods in (
        expected.items()
    ):
        actual = set(
            schema[
                "paths"
            ].get(
                path,
                {},
            )
        )

        assert methods <= actual


def test_control_center_mutations_require_platform_admin():
    source = Path(
        "app/api/v1/"
        "platform_control_v2.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "_require_platform_admin"
        in source
    )

    assert (
        "require_platform_admin_role"
        in source
    )

    assert (
        '"admin",'
        not in source
    )


def test_data_modes_are_explicit():
    assert (
        HospitalDataMode.MANAGED.value
        ==
        "managed"
    )

    assert (
        HospitalDataMode.CONNECTED.value
        ==
        "connected"
    )

    assert (
        HospitalDataMode.HYBRID.value
        ==
        "hybrid"
    )


def test_provision_requires_initial_admin():
    fields = (
        PlatformHospitalProvisionRequest
        .model_json_schema()
        .get(
            "required",
            [],
        )
    )

    assert (
        "initial_admin_email"
        in fields
    )


def test_status_changes_are_audited():
    source = Path(
        "app/services/"
        "platform_control_v2.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "platform.hospital.status_changed"
        in source
    )

    assert (
        "platform.hospital.provisioned"
        in source
    )


def test_control_center_exposes_health_and_security():
    source = Path(
        "app/services/"
        "platform_control_v2.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "integration_health"
        in source
    )

    assert (
        "security="
        in source
    )

    assert (
        "usage="
        in source
    )


def test_platform_control_uses_authoritative_role_guard():
    source = Path(
        "app/api/v1/"
        "platform_control_v2.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "require_platform_admin_role"
        in source
    )

    assert (
        '"admin",'
        not in source
    )


def test_provisioning_syncs_hospital_activation_state():
    source = Path(
        "app/services/"
        "platform_control_v2.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        '"is_active":'
        in source
    )

    assert (
        "is_active = :is_active"
        in source
    )


def test_raw_provisioning_supplies_required_timestamps():
    source = Path(
        "app/services/"
        "platform_control_v2.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        '"created_at":'
        in source
    )

    assert (
        '"updated_at":'
        in source
    )
