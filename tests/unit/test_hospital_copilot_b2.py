from pathlib import Path

from app.main import app

from app.schemas.hospital_copilot import (
    HospitalCopilotActionType,
    HospitalCopilotIntent,
)

from app.services.hospital_copilot import (
    HospitalCopilotService,
)


def test_b2_routes_registered():
    schema = app.openapi()

    base = (
        "/api/v1/hospital-operations/"
        "{hospital_slug}/copilot"
    )

    expected = {
        f"{base}/query":
            {
                "post",
            },

        f"{base}/proposals":
            {
                "post",
            },

        (
            f"{base}/proposals/"
            "{proposal_id}"
        ):
            {
                "get",
            },

        (
            f"{base}/proposals/"
            "{proposal_id}/confirm"
        ):
            {
                "post",
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

        assert (
            methods
            <= actual
        ), (
            path,
            methods,
            actual,
        )


def test_deterministic_known_intents_still_work():
    assert (
        HospitalCopilotService
        .classify_intent(
            "appointments today"
        )
        ==
        HospitalCopilotIntent
        .APPOINTMENTS
    )

    assert (
        HospitalCopilotService
        .classify_intent(
            "integration health"
        )
        ==
        HospitalCopilotIntent
        .INTEGRATIONS
    )


def test_action_types_are_typed():
    assert (
        HospitalCopilotActionType
        .SCHEDULE_CAPACITY_CHANGE
        .value
        ==
        "schedule_capacity_change"
    )

    assert (
        HospitalCopilotActionType
        .SCHEDULE_CLOSURE
        .value
        ==
        "schedule_closure"
    )


def test_proposal_service_never_directly_updates_schedule_engine_tables():
    source = Path(
        "app/services/"
        "hospital_copilot_proposals.py"
    ).read_text(
        encoding="utf-8",
    )

    forbidden = [
        (
            "UPDATE doctor_schedule_rules"
        ),

        (
            "INSERT INTO "
            "doctor_schedule_exceptions"
        ),

        (
            "DELETE FROM "
            "doctor_schedule_rules"
        ),
    ]

    for value in forbidden:
        assert (
            value
            not in source
        ), value


def test_llm_interpreter_is_classification_only():
    source = Path(
        "app/services/"
        "hospital_copilot_llm.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "Do not answer the user's factual question."
        in source
    )

    assert (
        "Do not return SQL."
        in source
    )

    assert (
        "ALLOWED_INTENTS"
        in source
    )


def test_confirmation_is_explicit():
    source = Path(
        "app/schemas/"
        "hospital_copilot.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "HospitalCopilotProposalConfirmation"
        in source
    )

    assert (
        "confirm: bool"
        in source
    )
