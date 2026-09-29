from pathlib import Path

from app.main import app


def test_doctor_mutation_routes_registered():
    schema = app.openapi()

    collection = (
        "/api/v1/hospital-operations/"
        "{hospital_slug}/doctors"
    )

    member = (
        "/api/v1/hospital-operations/"
        "{hospital_slug}/doctors/"
        "{doctor_id}"
    )

    activation = (
        "/api/v1/hospital-operations/"
        "{hospital_slug}/doctors/"
        "{doctor_id}/activation"
    )

    assert "post" in schema["paths"][
        collection
    ]

    assert "patch" in schema["paths"][
        member
    ]

    assert "patch" in schema["paths"][
        activation
    ]


def test_doctor_mutations_use_admin_guard():
    source = Path(
        "app/api/v1/"
        "hospital_doctor_registry.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "require_hospital_admin"
        in source
    )

    assert (
        "_require_doctor_mutation_admin"
        in source
    )

    for name in (
        "create_hospital_doctor",
        "update_hospital_doctor",
        "set_hospital_doctor_activation",
    ):
        start = source.index(
            f"async def {name}"
        )

        next_def = source.find(
            "\nasync def ",
            start + 10,
        )

        if next_def < 0:
            block = source[start:]
        else:
            block = source[
                start:
                next_def
            ]

        assert (
            "_require_doctor_mutation_admin("
            in block
        )


def test_staff_mutations_remain_admin_guarded():
    source = Path(
        "app/api/v1/"
        "hospital_staff_admin.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "require_hospital_admin"
        in source
    )

    assert (
        "async def add_hospital_staff"
        in source
    )

    assert (
        "async def update_hospital_staff"
        in source
    )
