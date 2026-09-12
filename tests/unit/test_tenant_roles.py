from app.core.roles import (
    HOSPITAL_ADMIN,
    HOSPITAL_ROLES,
    HOSPITAL_STAFF,
    PLATFORM_ADMIN,
)


def test_platform_role_separate_from_hospital_roles():
    assert PLATFORM_ADMIN not in HOSPITAL_ROLES


def test_hospital_admin_registered():
    assert HOSPITAL_ADMIN in HOSPITAL_ROLES


def test_hospital_staff_registered():
    assert HOSPITAL_STAFF in HOSPITAL_ROLES
