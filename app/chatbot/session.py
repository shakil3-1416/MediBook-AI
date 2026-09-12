import json
from typing import Any
from uuid import uuid4

from redis.asyncio import Redis

from app.core.config import settings


SESSION_TTL_SECONDS = 60 * 60 * 4


redis_client = Redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


def create_conversation_id() -> str:
    return str(uuid4())


def session_key(
    conversation_id: str,
) -> str:
    return f"medibook:conversation:{conversation_id}"


async def load_session(
    conversation_id: str,
) -> dict[str, Any]:

    raw = await redis_client.get(
        session_key(conversation_id)
    )

    if not raw:
        return {
            "conversation_id": conversation_id,
            "last_doctor": None,
            "last_date": None,
            "last_slots": [],
            "pending_booking": None,
            "patient": None,
        }

    return json.loads(raw)


async def save_session(
    conversation_id: str,
    state: dict[str, Any],
) -> None:

    state["conversation_id"] = conversation_id

    await redis_client.set(
        session_key(conversation_id),
        json.dumps(
            state,
            ensure_ascii=False,
        ),
        ex=SESSION_TTL_SECONDS,
    )


async def clear_pending_booking(
    conversation_id: str,
) -> None:

    state = await load_session(
        conversation_id
    )

    state["pending_booking"] = None

    await save_session(
        conversation_id,
        state,
    )
