from app.services.hospital_context import (
    DEFAULT_HOSPITAL_SLUG,
    HospitalContextError,
    HospitalDoctorAccessError,
)


def test_default_hospital_is_explicit():
    assert (
        DEFAULT_HOSPITAL_SLUG
        == "medibook-demo"
    )


def test_tenant_errors_are_distinct():
    assert (
        HospitalContextError
        is not
        HospitalDoctorAccessError
    )
