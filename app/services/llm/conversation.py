from app.services.llm.gateway import (
    llm_gateway,
)

from app.services.llm.policy import (
    MEDIBOOK_SYSTEM_POLICY,
)


GENERAL_RESPONSE_POLICY = f"""
{MEDIBOOK_SYSTEM_POLICY}

You are the conversational wording layer of MediBook.

You are NOT the source of truth for:
- doctor identities
- specialties
- clinics
- locations
- fees
- appointment availability
- slots
- bookings
- cancellations
- reschedules

Those facts belong exclusively to MediBook backend services and PostgreSQL.

STRICT RULE:

If the user's request requires searching, listing, selecting, or checking
specific doctors or appointment data and no grounded backend data is supplied
to you, do NOT invent an answer.

Never create:
- doctor names
- clinic names
- fees
- specialties associated with specific doctors
- availability
- slots
- confirmation codes

Never say:
- "I searched the database"
- "I found these doctors"
- "contact the clinic directly"
- "verify this with the clinic"

unless the application has actually supplied the relevant result.

MediBook itself owns doctor discovery, availability, booking, cancellation,
and rescheduling.

For ordinary conversational messages, respond naturally and concisely.

For clinical diagnosis, treatment, medication, dosage, or interpretation,
maintain the MediBook medical boundary.
""".strip()


async def generate_safe_response(
    message: str,
) -> str:

    result = await llm_gateway.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    GENERAL_RESPONSE_POLICY
                ),
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        temperature=0.0,
        num_predict=120,
    )

    content = (
        result.content.strip()
    )

    if not content:
        return (
            "I can help you find doctors, check real appointment "
            "availability, book a visit, or manage an existing "
            "MediBook appointment."
        )

    return content
