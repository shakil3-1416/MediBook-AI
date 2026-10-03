"""The safety triage answers emergencies and clinical questions before any search or model call."""

import pytest

from app.services.llm.safety_router import safety_route

EMERGENCIES = [
    "i'm feeling pain in my chest, what to do",
    "my chest hurts",
    "Chest pain since morning",
    "I have tightness in my chest",
    "I can't breathe properly",
    "shortness of breath",
    "my father fainted",
    "I want to end my life",
    "my face is drooping and slurred speech",
    "she is bleeding heavily",
    "my son swallowed some pills",
    "buke betha korche",
    "আমার বুকে ব্যথা করছে",
    "শ্বাসকষ্ট হচ্ছে",
    "pregnant and bleeding",
]

CLINICAL = [
    "what medicine should I take for headache?",
    "do i have diabetes",
    "can you interpret my blood test report",
    "I have a skin rash, what should I do?",
    "I have fever for 3 days",
    "my baby has a cough",
    "I'm feeling anxious all the time",
    "আমার জ্বর",
]

NOT_CLINICAL = [
    "hi",
    "find a cardiologist",
    "show ENT doctors",
    "book a dermatologist tomorrow evening",
    "I have a skin rash, find a dermatologist",
    "which doctors are available tomorrow?",
    "my appointments",
    "what is the consultation fee for cardiology?",
    "where is the hospital?",
    "what's the weather today?",
    "I had food poisoning last week, book a doctor",
    "chest clinic location",
    "the app is not responding",
    "I hurt myself playing football",
]


@pytest.mark.parametrize("message", EMERGENCIES)
def test_emergencies_send_people_to_999(message):
    result = safety_route(message)
    assert result.route == "emergency"
    assert "999" in result.response or "৯৯৯" in result.response


@pytest.mark.parametrize("message", CLINICAL)
def test_clinical_questions_get_a_safe_answer(message):
    result = safety_route(message)
    assert result.route == "medical"
    assert result.response


@pytest.mark.parametrize("message", NOT_CLINICAL)
def test_normal_requests_go_on_to_search_and_booking(message):
    assert safety_route(message).matched is False


def test_chest_pain_offers_a_cardiology_follow_up():
    result = safety_route("i'm feeling pain in my chest")
    assert result.specialty == "cardiology"
    assert "cardiologist" in result.response


def test_symptoms_point_to_the_right_specialist():
    assert safety_route("I have a skin rash, what should I do?").specialty == "dermatology"
    assert safety_route("my baby has a cough").specialty == "pediatrics"
    assert safety_route("I have fever for 3 days").specialty == "medicine"


def test_bangla_messages_get_bangla_answers():
    assert "৯৯৯" in safety_route("আমার বুকে ব্যথা করছে").response
