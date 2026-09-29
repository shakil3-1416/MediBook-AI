from app.main import app

from app.schemas.hospital_copilot import (
    HospitalCopilotIntent,
)

from app.services.hospital_copilot import (
    HospitalCopilotService,
)


def test_copilot_route_registered():
    schema = app.openapi()

    path = (
        "/api/v1/hospital-operations/"
        "{hospital_slug}/copilot/query"
    )

    assert (
        path
        in schema["paths"]
    )

    assert (
        "post"
        in schema["paths"][
            path
        ]
    )


def test_copilot_intent_appointments():
    assert (
        HospitalCopilotService.classify_intent(
            "How many appointments do we have today?"
        )
        ==
        HospitalCopilotIntent.APPOINTMENTS
    )


def test_copilot_intent_doctors():
    assert (
        HospitalCopilotService.classify_intent(
            "How many doctors are active?"
        )
        ==
        HospitalCopilotIntent.DOCTORS
    )


def test_copilot_intent_integrations():
    assert (
        HospitalCopilotService.classify_intent(
            "Are our integrations healthy?"
        )
        ==
        HospitalCopilotIntent.INTEGRATIONS
    )


def test_copilot_intent_recent_changes():
    assert (
        HospitalCopilotService.classify_intent(
            "Show recent changes"
        )
        ==
        HospitalCopilotIntent.RECENT_CHANGES
    )


def test_copilot_unknown_is_safe():
    assert (
        HospitalCopilotService.classify_intent(
            "Write a poem about the hospital"
        )
        ==
        HospitalCopilotIntent.UNKNOWN
    )
