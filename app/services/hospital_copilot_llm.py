from __future__ import annotations

import inspect
import json
from typing import Any

from app.schemas.hospital_copilot import (
    HospitalCopilotIntent,
)


ALLOWED_INTENTS = {
    item.value
    for item in HospitalCopilotIntent
}


SYSTEM_PROMPT = """
You are a language interpreter for a hospital
operations control plane.

Classify the user's request only.

Allowed intents:
overview
appointments
doctors
capacity
schedules
integrations
staff
recent_changes
propose_capacity
propose_closure
help
unknown

Important:
- Do not answer the user's factual question.
- Do not invent hospital facts.
- Do not return SQL.
- Do not perform actions.
- Do not diagnose patients.
- Language understanding only.

Examples:
- "increase Dr X's slots" -> propose_capacity
- "set that rule capacity to 10" -> propose_capacity
- "close Dr X on Friday" -> propose_closure
- "block 2026-10-02" -> propose_closure
""".strip()


STRUCTURED_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": sorted(
                ALLOWED_INTENTS
            ),
        },
    },
    "required": [
        "intent",
    ],
    "additionalProperties": False,
}


def _parse_intent(
    value: Any,
) -> HospitalCopilotIntent | None:
    parsed: Any = value

    if hasattr(
        value,
        "content",
    ):
        parsed = getattr(
            value,
            "content",
        )

    if isinstance(
        parsed,
        str,
    ):
        raw = parsed.strip()

        if raw.startswith(
            "```"
        ):
            raw = raw.strip(
                "`"
            )

            if raw.startswith(
                "json"
            ):
                raw = raw[
                    4:
                ].strip()

        try:
            parsed = json.loads(
                raw
            )

        except Exception:
            start = raw.find(
                "{"
            )

            end = raw.rfind(
                "}"
            )

            if (
                start >= 0
                and end > start
            ):
                try:
                    parsed = json.loads(
                        raw[
                            start:
                            end + 1
                        ]
                    )
                except Exception:
                    return None
            else:
                return None

    if not isinstance(
        parsed,
        dict,
    ):
        return None

    # Some gateway wrappers may wrap structured data.
    for key in (
        "data",
        "result",
        "output",
    ):
        if (
            key in parsed
            and isinstance(
                parsed[key],
                dict,
            )
            and "intent"
            in parsed[key]
        ):
            parsed = parsed[
                key
            ]

            break

    intent = parsed.get(
        "intent"
    )

    if (
        not isinstance(
            intent,
            str,
        )
        or intent
        not in ALLOWED_INTENTS
    ):
        return None

    return HospitalCopilotIntent(
        intent
    )


async def _gateway_structured(
    message: str,
) -> HospitalCopilotIntent | None:
    try:
        from app.services.llm.gateway import (
            OllamaGateway,
        )

        gateway = OllamaGateway()

        result = await gateway.structured(
            messages=[
                {
                    "role":
                        "system",
                    "content":
                        SYSTEM_PROMPT,
                },
                {
                    "role":
                        "user",
                    "content":
                        message,
                },
            ],
            schema=
                STRUCTURED_SCHEMA,
            model=None,
        )

        return _parse_intent(
            result
        )

    except Exception:
        return None


async def _legacy_chat(
    message: str,
) -> HospitalCopilotIntent | None:
    try:
        from app.chatbot.ollama_client import (
            chat_with_ollama,
        )

        signature = inspect.signature(
            chat_with_ollama
        )

        if (
            "message"
            not in signature.parameters
            and len(
                signature.parameters
            )
            != 1
        ):
            return None

        prompt = (
            SYSTEM_PROMPT
            + "\n\n"
            + 'Return JSON only, for example '
              '{"intent":"appointments"}.\n\n'
            + "User request:\n"
            + message
        )

        result = chat_with_ollama(
            prompt
        )

        if inspect.isawaitable(
            result
        ):
            result = await result

        return _parse_intent(
            result
        )

    except Exception:
        return None


async def interpret_intent(
    user_message: str,
) -> HospitalCopilotIntent | None:
    intent = await _gateway_structured(
        user_message
    )

    if intent is not None:
        return intent

    return await _legacy_chat(
        user_message
    )
