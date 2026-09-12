from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional
import json
import os

import redis


@dataclass
class ConversationState:
    intent: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None
    slot_date: Optional[str] = None
    start_time: Optional[str] = None
    awaiting_confirmation: bool = False


_REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://127.0.0.1:6379/0",
)

_client = redis.Redis.from_url(
    _REDIS_URL,
    decode_responses=True,
)

_TTL = 60 * 60 * 6


def _key(conversation_id: str) -> str:
    return f"medibook:conversation-state:{conversation_id}"


def load_state(
    conversation_id: str | None,
) -> ConversationState:
    if not conversation_id:
        return ConversationState()

    try:
        raw = _client.get(
            _key(conversation_id)
        )
    except Exception:
        return ConversationState()

    if not raw:
        return ConversationState()

    try:
        data = json.loads(raw)
        return ConversationState(
            **{
                key: data.get(key)
                for key in ConversationState.__dataclass_fields__
            }
        )
    except Exception:
        return ConversationState()


def save_state(
    conversation_id: str,
    state: ConversationState,
) -> None:
    try:
        _client.setex(
            _key(conversation_id),
            _TTL,
            json.dumps(asdict(state)),
        )
    except Exception:
        pass


def clear_state(
    conversation_id: str | None,
) -> None:
    if not conversation_id:
        return

    try:
        _client.delete(
            _key(conversation_id)
        )
    except Exception:
        pass
