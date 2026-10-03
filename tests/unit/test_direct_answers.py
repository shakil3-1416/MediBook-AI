"""Direct answers: which questions skip the language model, and the doctor-search wording."""

from datetime import date

import pytest

from app.chatbot.direct_answers import classify, specialty_matches
from app.chatbot.hospital_grounded_directory import is_explicit_doctor_search

SATURDAY = date(2026, 10, 3)


@pytest.mark.parametrize(
    ("message", "kind", "specialty"),
    [
        ("what's the weather today?", "off_topic", None),
        ("where is the hospital?", "hospital_info", None),
        ("what is your phone number", "hospital_info", None),
        ("what is the consultation fee for cardiology?", "fees", "cardio"),
        ("how much does a skin doctor cost", "fees", "dermat"),
        ("which doctors are available tomorrow?", "availability", None),
        ("book a dermatologist tomorrow evening", "availability", "dermat"),
        ("any ENT slots available on monday", "availability", "ent"),
        ("I want to book an appointment", "availability", None),
    ],
)
def test_questions_answered_directly(message, kind, specialty):
    question = classify(message, SATURDAY)
    assert question is not None
    assert question.kind == kind
    assert question.specialty_key == specialty


@pytest.mark.parametrize(
    "message",
    [
        "find a cardiologist",
        "hi",
        "my appointments",
        "cancel my appointment tomorrow",
        "is dr afsana kabir available tomorrow",
        "doctor dekhate chai",
        "i'm feeling pain in my chest",
    ],
)
def test_other_messages_continue_to_the_normal_flow(message):
    assert classify(message, SATURDAY) is None


def test_dates_and_times_are_understood():
    question = classify("book a dermatologist tomorrow evening", SATURDAY)
    assert question.start == date(2026, 10, 4)
    assert question.window == "evening"
    assert classify("which doctors are available on saturday", SATURDAY).start == SATURDAY


def test_ent_is_not_confused_with_dentistry():
    assert specialty_matches("ENT", "ent")
    assert specialty_matches("Dentistry", "ent") is False
    assert specialty_matches("Cardiology", "cardio")


@pytest.mark.parametrize("message", ["find a cardiologist", "show ENT doctors", "doctor dekhate chai", "I need a dermatologist"])
def test_doctor_searches_are_recognised(message):
    assert is_explicit_doctor_search(message)


@pytest.mark.parametrize("message", ["show my appointments", "what is the consultation fee", "hi"])
def test_non_searches_are_left_alone(message):
    assert is_explicit_doctor_search(message) is False
