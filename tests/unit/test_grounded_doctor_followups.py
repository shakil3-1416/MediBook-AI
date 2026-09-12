from app.chatbot.hospital_grounded_followups import (
    is_availability_followup,
    is_profile_followup,
    resolve_doctor_reference,
)


def _state():
    return {
        "last_doctors": [
            {
                "doctor_id": "11111111-1111-1111-1111-111111111111",
                "doctor_name": "Dr. First",
            },
            {
                "doctor_id": "22222222-2222-2222-2222-222222222222",
                "doctor_name": "Dr. Second",
            },
            {
                "doctor_id": "33333333-3333-3333-3333-333333333333",
                "doctor_name": "Dr. Third",
            },
        ]
    }


def test_second_one_resolves_second_doctor():
    selected = resolve_doctor_reference(
        "Tell me about the second one",
        _state(),
    )

    assert selected is not None
    assert (
        selected["doctor_name"]
        == "Dr. Second"
    )


def test_exact_doctor_name_resolves():
    selected = resolve_doctor_reference(
        "Tell me about Dr. Third",
        _state(),
    )

    assert selected is not None
    assert (
        selected["doctor_name"]
        == "Dr. Third"
    )


def test_selected_doctor_used_for_availability():
    state = _state()

    state[
        "grounded_selected_doctor"
    ] = state[
        "last_doctors"
    ][1]

    selected = resolve_doctor_reference(
        "Is this doctor available tomorrow?",
        state,
    )

    assert selected is not None
    assert (
        selected["doctor_name"]
        == "Dr. Second"
    )


def test_followup_intent_detection():
    assert is_profile_followup(
        "Tell me about the second one"
    )

    assert is_availability_followup(
        "Is this doctor available tomorrow?"
    )


def test_reschedule_does_not_route_as_availability():
    assert not is_availability_followup(
        "Reschedule appointment MED-ABC123 "
        "to 2026-09-08 at 09:00"
    )


def test_schedule_still_routes_as_availability():
    assert is_availability_followup(
        "What is this doctor's schedule tomorrow?"
    )


def test_booking_is_not_availability_followup():
    assert not is_availability_followup(
        "Book 09:00 with Dr. Example"
    )
