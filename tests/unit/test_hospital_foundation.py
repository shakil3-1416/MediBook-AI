from app.models import Base


def test_hospital_tables_registered():
    tables = set(
        Base.metadata.tables
    )

    assert "hospitals" in tables
    assert "hospital_memberships" in tables
    assert "hospital_doctors" in tables
    assert "hospital_integrations" in tables
