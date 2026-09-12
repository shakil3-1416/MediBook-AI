from app.chatbot.orchestrator import (
    choose_appointment,
    extract_confirmation_code,
)


EXPECTED = "MED-1E3D139C96"


def test_extract_canonical_confirmation_code():
    assert (
        extract_confirmation_code(
            "Cancel MED-1E3D139C96"
        )
        == EXPECTED
    )


def test_extract_lowercase_confirmation_code():
    assert (
        extract_confirmation_code(
            "cancel med-1e3d139c96"
        )
        == EXPECTED
    )


def test_extract_normalized_space_confirmation_code():
    assert (
        extract_confirmation_code(
            "Cancel MED 1E3D139C96"
        )
        == EXPECTED
    )


def test_choose_exact_appointment_when_multiple_exist():

    appointments = [
        {
            "confirmation_code":
                "MED-1E3D139C96",
            "status":
                "confirmed",
        },
        {
            "confirmation_code":
                "MED-ECED7AFD02",
            "status":
                "confirmed",
        },
    ]

    selected = choose_appointment(
        "Reschedule MED-1E3D139C96 to 6 PM",
        appointments,
    )

    assert selected is not None

    assert (
        selected["confirmation_code"]
        == EXPECTED
    )


def test_cancel_confirmation_code_routes_to_cancel_intent():
    from app.chatbot.orchestrator import (
        CANCEL_APPOINTMENT_HINTS,
        contains_any,
    )

    assert contains_any(
        "Cancel MED-1E3D139C96",
        CANCEL_APPOINTMENT_HINTS,
    )
