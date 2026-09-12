from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionFactory


router = APIRouter(
    prefix="/widget-conversations",
    tags=["widget-conversations"],
)


async def get_session():
    async with AsyncSessionFactory() as session:
        yield session


class ConversationCreate(BaseModel):
    hospital_slug: str
    visitor_id: str = Field(min_length=8, max_length=128)


class MessageCreate(BaseModel):
    visitor_id: str = Field(min_length=8, max_length=128)
    role: str
    content: str = Field(min_length=1)


class MessageEdit(BaseModel):
    visitor_id: str = Field(min_length=8, max_length=128)
    content: str = Field(min_length=1)


async def resolve_hospital_id(
    session: AsyncSession,
    hospital_slug: str,
):
    result = await session.execute(
        text(
            """
            SELECT id
            FROM hospitals
            WHERE slug=:slug
              AND is_active=TRUE
            """
        ),
        {
            "slug": hospital_slug,
        },
    )

    value = result.scalar_one_or_none()

    if value is None:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found.",
        )

    return value


async def require_owner(
    session: AsyncSession,
    conversation_id: uuid.UUID,
    visitor_id: str,
):
    result = await session.execute(
        text(
            """
            SELECT
                wc.id,
                wc.hospital_id,
                h.slug AS hospital_slug,
                wc.title,
                wc.created_at,
                wc.updated_at
            FROM widget_conversations wc
            JOIN hospitals h
              ON h.id=wc.hospital_id
            WHERE wc.id=:conversation_id
              AND wc.visitor_id=:visitor_id
            """
        ),
        {
            "conversation_id": conversation_id,
            "visitor_id": visitor_id,
        },
    )

    row = result.mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return row


@router.post("")
async def create_conversation(
    payload: ConversationCreate,
    session: AsyncSession = Depends(get_session),
):
    hospital_id = await resolve_hospital_id(
        session,
        payload.hospital_slug,
    )

    conversation_id = uuid.uuid4()

    await session.execute(
        text(
            """
            INSERT INTO widget_conversations(
                id,
                hospital_id,
                visitor_id
            )
            VALUES(
                :id,
                :hospital_id,
                :visitor_id
            )
            """
        ),
        {
            "id": conversation_id,
            "hospital_id": hospital_id,
            "visitor_id": payload.visitor_id,
        },
    )

    await session.commit()

    return {
        "id": str(conversation_id),
        "hospital_slug": payload.hospital_slug,
        "title": "New appointment chat",
        "messages": [],
    }


@router.get("/{hospital_slug}")
async def list_conversations(
    hospital_slug: str,
    visitor_id: str,
    session: AsyncSession = Depends(get_session),
):
    hospital_id = await resolve_hospital_id(
        session,
        hospital_slug,
    )

    result = await session.execute(
        text(
            """
            SELECT
                id,
                title,
                created_at,
                updated_at
            FROM widget_conversations
            WHERE hospital_id=:hospital_id
              AND visitor_id=:visitor_id
            ORDER BY updated_at DESC
            LIMIT 100
            """
        ),
        {
            "hospital_id": hospital_id,
            "visitor_id": visitor_id,
        },
    )

    return [
        {
            "id": str(row["id"]),
            "title": row["title"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in result.mappings()
    ]


@router.get(
    "/{hospital_slug}/{conversation_id}"
)
async def get_conversation(
    hospital_slug: str,
    conversation_id: uuid.UUID,
    visitor_id: str,
    session: AsyncSession = Depends(get_session),
):
    owner = await require_owner(
        session,
        conversation_id,
        visitor_id,
    )

    if owner["hospital_slug"] != hospital_slug:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    result = await session.execute(
        text(
            """
            SELECT
                id,
                role,
                content,
                sequence_no,
                edited_at,
                created_at
            FROM widget_messages
            WHERE conversation_id=:conversation_id
            ORDER BY sequence_no
            """
        ),
        {
            "conversation_id": conversation_id,
        },
    )

    messages = [
        {
            "id": str(row["id"]),
            "role": row["role"],
            "content": row["content"],
            "sequence_no": row["sequence_no"],
            "edited_at": row["edited_at"],
            "created_at": row["created_at"],
        }
        for row in result.mappings()
    ]

    return {
        "id": str(owner["id"]),
        "hospital_slug": hospital_slug,
        "title": owner["title"],
        "messages": messages,
    }


@router.post(
    "/{conversation_id}/messages"
)
async def add_message(
    conversation_id: uuid.UUID,
    payload: MessageCreate,
    session: AsyncSession = Depends(get_session),
):
    await require_owner(
        session,
        conversation_id,
        payload.visitor_id,
    )

    if payload.role not in {
        "user",
        "assistant",
    }:
        raise HTTPException(
            status_code=422,
            detail="Invalid role.",
        )

    result = await session.execute(
        text(
            """
            SELECT COALESCE(
                MAX(sequence_no),
                0
            )
            FROM widget_messages
            WHERE conversation_id=:conversation_id
            """
        ),
        {
            "conversation_id": conversation_id,
        },
    )

    sequence = int(
        result.scalar_one()
    ) + 1

    message_id = uuid.uuid4()

    await session.execute(
        text(
            """
            INSERT INTO widget_messages(
                id,
                conversation_id,
                role,
                content,
                sequence_no
            )
            VALUES(
                :id,
                :conversation_id,
                :role,
                :content,
                :sequence
            )
            """
        ),
        {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": payload.role,
            "content": payload.content,
            "sequence": sequence,
        },
    )

    if (
        sequence == 1
        and payload.role == "user"
    ):
        title = (
            payload.content.strip()
            .replace("\n", " ")
        )[:80]

        await session.execute(
            text(
                """
                UPDATE widget_conversations
                SET title=:title
                WHERE id=:conversation_id
                """
            ),
            {
                "title": title,
                "conversation_id": conversation_id,
            },
        )

    await session.execute(
        text(
            """
            UPDATE widget_conversations
            SET updated_at=NOW()
            WHERE id=:conversation_id
            """
        ),
        {
            "conversation_id": conversation_id,
        },
    )

    await session.commit()

    return {
        "id": str(message_id),
        "sequence_no": sequence,
    }


@router.patch(
    "/{conversation_id}/messages/{message_id}"
)
async def edit_user_message(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    payload: MessageEdit,
    session: AsyncSession = Depends(get_session),
):
    await require_owner(
        session,
        conversation_id,
        payload.visitor_id,
    )

    result = await session.execute(
        text(
            """
            SELECT
                role,
                sequence_no
            FROM widget_messages
            WHERE id=:message_id
              AND conversation_id=:conversation_id
            """
        ),
        {
            "message_id": message_id,
            "conversation_id": conversation_id,
        },
    )

    row = result.mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Message not found.",
        )

    if row["role"] != "user":
        raise HTTPException(
            status_code=409,
            detail="Only patient messages can be edited.",
        )

    sequence = row["sequence_no"]

    # Critical semantics:
    # editing chat history does NOT touch appointments.
    # Only later conversational messages are truncated.
    await session.execute(
        text(
            """
            DELETE FROM widget_messages
            WHERE conversation_id=:conversation_id
              AND sequence_no>:sequence
            """
        ),
        {
            "conversation_id": conversation_id,
            "sequence": sequence,
        },
    )

    await session.execute(
        text(
            """
            UPDATE widget_messages
            SET
                content=:content,
                edited_at=NOW()
            WHERE id=:message_id
            """
        ),
        {
            "content": payload.content,
            "message_id": message_id,
        },
    )

    await session.execute(
        text(
            """
            UPDATE widget_conversations
            SET updated_at=NOW()
            WHERE id=:conversation_id
            """
        ),
        {
            "conversation_id": conversation_id,
        },
    )

    await session.commit()

    return {
        "message_id": str(message_id),
        "sequence_no": sequence,
        "regenerate_from": sequence,
        "appointments_changed": False,
    }
