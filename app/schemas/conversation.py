from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ConversationSummary(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    actions: list[dict[str, Any]] | None = None
    created_at: datetime


class ConversationDetail(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[ConversationMessageResponse]


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummary]


class NewConversationResponse(BaseModel):
    id: UUID
    title: str
