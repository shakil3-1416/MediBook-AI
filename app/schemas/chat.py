from typing import Any
from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )

    conversation_id: str | None = None


class ChatAction(BaseModel):
    id: str

    type: Literal[
        "send_message",
        "book_slot",
        "confirm",
        "cancel",
        "reschedule",
    ]

    label: str

    message: str

    payload: dict[str, Any] | None = None

    variant: Literal[
        "primary",
        "secondary",
        "danger",
    ] = "secondary"


class ChatResponse(BaseModel):
    response: str

    conversation_id: str

    actions: list[ChatAction] = Field(
        default_factory=list
    )

from typing import Literal


class ChatStreamEvent(BaseModel):
    type: Literal[
        "status",
        "text_delta",
        "actions",
        "done",
        "error",
    ]

    message: str | None = None
    delta: str | None = None
    actions: list[ChatAction] | None = None
    conversation_id: str | None = None
