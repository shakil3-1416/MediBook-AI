import json
import re
from datetime import date, timedelta
from typing import Any

from ollama import AsyncClient

from app.chatbot.prompt import SYSTEM_PROMPT
from app.chatbot.tools import TOOL_REGISTRY
from app.core.config import settings


client = AsyncClient(
    host=settings.ollama_base_url,
)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_doctors",
            "description": (
                "Search the verified MediBook doctor database. "
                "Use for actual doctor discovery and doctor lookup."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "specialty": {
                        "type": ["string", "null"],
                    },
                    "location": {
                        "type": ["string", "null"],
                    },
                    "gender": {
                        "type": ["string", "null"],
                    },
                    "max_fee": {
                        "type": ["number", "null"],
                    },
                    "name": {
                        "type": ["string", "null"],
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_doctor_slots",
            "description": (
                "Get real available appointment slots for a specific "
                "MediBook doctor on a specific date."
            ),
            "parameters": {
                "type": "object",
                "required": [
                    "doctor_id",
                    "date",
                ],
                "properties": {
                    "doctor_id": {
                        "type": "string",
                        "description": (
                            "The doctor UUID returned by search_doctors."
                        ),
                    },
                    "date": {
                        "type": "string",
                        "description": (
                            "Calendar date in YYYY-MM-DD format."
                        ),
                    },
                },
                "additionalProperties": False,
            },
        },
    },
]


MEDICAL_HINTS = (
    "what medicine",
    "which medicine",
    "what medication",
    "prescribe",
    "dosage",
    "diagnose",
)


URGENT_HINTS = (
    "chest pain",
    "can't breathe",
    "cannot breathe",
    "severe bleeding",
    "unconscious",
)


GREETING_WORDS = {
    "hello",
    "hi",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
}


def normalize(
    text: str,
) -> str:
    return " ".join(
        text.lower().strip().split()
    )


def is_greeting(
    message: str,
) -> bool:
    return normalize(message) in GREETING_WORDS


def is_medical_request(
    message: str,
) -> bool:
    text = normalize(message)

    return any(
        hint in text
        for hint in MEDICAL_HINTS
    )


def has_urgent_symptom(
    message: str,
) -> bool:
    # One source of truth for emergencies: the safety router.
    from app.services.llm.safety_router import safety_route

    return safety_route(message).route == "emergency"


def looks_like_fake_tool_call(
    content: str,
) -> bool:

    if not content:
        return False

    return bool(
        re.search(
            r'^\s*\{\s*"(name|function|tool)"',
            content,
            re.IGNORECASE,
        )
    )


def date_context() -> str:
    today = date.today()
    tomorrow = today + timedelta(days=1)

    return (
        f"Current system date: {today.isoformat()}. "
        f"Tomorrow is {tomorrow.isoformat()}."
    )


async def execute_tool_call(
    tool_call: Any,
) -> str:

    tool_name = tool_call.function.name
    arguments = tool_call.function.arguments or {}

    tool = TOOL_REGISTRY.get(
        tool_name
    )

    if tool is None:
        return json.dumps(
            {
                "error": "unknown_tool",
                "tool": tool_name,
            }
        )

    try:
        result = await tool(
            **arguments
        )

        return json.dumps(
            result,
            ensure_ascii=False,
            default=str,
        )

    except Exception as exc:
        return json.dumps(
            {
                "error": "tool_execution_failed",
                "detail": str(exc),
            }
        )


async def safe_medical_response(
    message: str,
) -> str:

    if has_urgent_symptom(message):
        return (
            "I can't diagnose chest pain or recommend medication. "
            "If the pain is severe, sudden, worsening, or associated "
            "with breathing difficulty, fainting, or other concerning "
            "symptoms, seek urgent medical care. "
            "I can help you find a cardiologist and check their "
            "available appointment times."
        )

    return (
        "I can't diagnose conditions or recommend medication. "
        "I can help you find an appropriate doctor and check "
        "their real appointment availability."
    )


async def greeting_response() -> str:
    return (
        "Hi! I'm MediBook AI. I can help you find a doctor, "
        "compare consultation fees, check real appointment availability, "
        "and help you book or manage appointments. "
        "What kind of doctor are you looking for?"
    )


async def chat_with_ollama(
    message: str,
) -> str:

    if is_greeting(message):
        return await greeting_response()

    if is_medical_request(message):
        return await safe_medical_response(
            message
        )

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                SYSTEM_PROMPT
                + "\n\n"
                + date_context()
            ),
        },
        {
            "role": "user",
            "content": message,
        },
    ]

    for _ in range(5):

        response = await client.chat(
            model=settings.ollama_model,
            messages=messages,
            tools=TOOLS,
            options={
                "temperature": 0,
            },
        )

        assistant = response.message

        tool_calls = (
            assistant.tool_calls
            or []
        )

        if not tool_calls:

            content = (
                assistant.content
                or ""
            ).strip()

            if looks_like_fake_tool_call(content):
                return (
                    "I couldn't complete that reliably. "
                    "Please tell me the doctor name or specialty "
                    "and the date you want to check."
                )

            return (
                content
                or "I couldn't complete that request."
            )

        messages.append(
            {
                "role": "assistant",
                "content": assistant.content or "",
                "tool_calls": tool_calls,
            }
        )

        for tool_call in tool_calls:

            result = await execute_tool_call(
                tool_call
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_name": (
                        tool_call.function.name
                    ),
                    "content": result,
                }
            )

    return (
        "I couldn't complete that request reliably. "
        "Please try again with a doctor name and date."
    )
