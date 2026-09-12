from app.core.config import settings

from app.schemas.llm_intent import (
    MediBookIntent,
)

from app.services.llm.gateway import (
    llm_gateway,
)


INTENT_SYSTEM_PROMPT = """
Classify a message for the MediBook doctor appointment system.

Allowed intents:
greeting
search_doctor
check_availability
book_appointment
list_appointments
cancel_appointment
reschedule_appointment
general_help
medical_request
unknown

Extract only explicitly supported information:
doctor_name, specialty, location, gender, date, time.

Rules:
- Do not invent values.
- diagnosis/treatment/medicine/dosage/clinical interpretation = medical_request
- doctor discovery = search_doctor
- schedule/free-slot request = check_availability
- new booking = book_appointment
- existing bookings = list_appointments
- cancellation = cancel_appointment
- moving/changing an appointment = reschedule_appointment
- MediBook capability question = general_help
- unclear = unknown

confidence must be between 0 and 1.
""".strip()


async def classify_intent(
    message: str,
) -> MediBookIntent:

    result = await llm_gateway.structured(
        messages=[
            {
                "role": "system",
                "content": (
                    INTENT_SYSTEM_PROMPT
                ),
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        schema=MediBookIntent,
        model=(
            settings.ollama_router_model
        ),
    )

    return MediBookIntent.model_validate(
        result
    )
