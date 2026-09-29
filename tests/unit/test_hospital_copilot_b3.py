from pathlib import Path

from app.main import app


def test_execute_route_registered():
    schema = app.openapi()

    path = (
        "/api/v1/hospital-operations/"
        "{hospital_slug}/copilot/"
        "proposals/{proposal_id}/execute"
    )

    assert path in schema["paths"]

    assert (
        "post"
        in schema[
            "paths"
        ][
            path
        ]
    )


def test_execute_endpoint_is_admin_only():
    source = Path(
        "app/api/v1/"
        "hospital_copilot.py"
    ).read_text(
        encoding="utf-8",
    )

    start = source.index(
        "async def execute_copilot_proposal"
    )

    block = source[
        start:
    ]

    assert (
        "admin=True"
        in block
    )


def test_executor_reuses_existing_schedule_api():
    source = Path(
        "app/services/"
        "hospital_copilot_schedule_executor.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "app.api.v1.hospital_schedules"
        in source
    )

    assert (
        "update_rule"
        in source
    )

    assert (
        "create_exception"
        in source
    )


def test_executor_uses_typed_schedule_contracts():
    source = Path(
        "app/services/"
        "hospital_copilot_schedule_executor.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "ScheduleRuleUpdate"
        in source
    )

    assert (
        "ScheduleExceptionCreate"
        in source
    )


def test_executor_does_not_write_schedule_tables_directly():
    source = Path(
        "app/services/"
        "hospital_copilot_schedule_executor.py"
    ).read_text(
        encoding="utf-8",
    )

    forbidden = [
        "UPDATE doctor_schedule_rules",
        "INSERT INTO doctor_schedule_rules",
        "DELETE FROM doctor_schedule_rules",
        "UPDATE doctor_schedule_exceptions",
        "INSERT INTO doctor_schedule_exceptions",
        "DELETE FROM doctor_schedule_exceptions",
    ]

    for statement in forbidden:
        assert statement not in source


def test_execution_requires_confirmed_proposal():
    source = Path(
        "app/services/"
        "hospital_copilot_proposals.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "Only confirmed proposals can be executed."
        in source
    )


def test_executor_receives_deterministic_impact():
    source = Path(
        "app/services/"
        "hospital_copilot_proposals.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "proposal.impact"
        in source
    )


def test_execution_terminal_states_are_persisted():
    source = Path(
        "app/services/"
        "hospital_copilot_proposals.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "status = 'executed'"
        in source
    )

    assert (
        "status = 'failed'"
        in source
    )

    assert (
        "execution_result"
        in source
    )


def test_execution_audit_events_are_recorded():
    source = Path(
        "app/services/"
        "hospital_copilot_proposals.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "copilot.proposal.executed"
        in source
    )

    assert (
        "copilot.proposal.execution_failed"
        in source
    )
