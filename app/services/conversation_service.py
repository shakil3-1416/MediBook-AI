from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import (
    Conversation,
    ConversationMessage,
)


class ConversationNotFoundError(Exception):
    pass


class ConversationOwnershipError(Exception):
    pass


def build_conversation_title(
    message: str,
) -> str:

    clean = " ".join(
        message.strip().split()
    )

    if not clean:
        return "New conversation"

    words = clean.split()

    title = " ".join(
        words[:7]
    )

    if len(title) > 58:
        title = title[:58].rstrip()

    if len(words) > 7:
        title += "…"

    return title


class ConversationService:

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session


    async def ensure_conversation(
        self,
        *,
        conversation_id: str,
        user_id: UUID,
        first_message: str,
    ) -> Conversation:

        try:
            conversation_uuid = UUID(
                str(conversation_id)
            )
        except ValueError as exc:
            raise ConversationNotFoundError() from exc

        conversation = await self.session.get(
            Conversation,
            conversation_uuid,
        )

        if conversation is not None:

            if (
                conversation.user_id
                != user_id
            ):
                raise ConversationOwnershipError()

            if conversation.archived_at is not None:
                raise ConversationNotFoundError()

            return conversation

        conversation = Conversation(
            id=conversation_uuid,
            user_id=user_id,
            title=build_conversation_title(
                first_message
            ),
        )

        self.session.add(
            conversation
        )

        await self.session.flush()

        return conversation


    async def append_message(
        self,
        *,
        conversation_id: str,
        user_id: UUID,
        role: str,
        content: str,
        actions: list | None = None,
    ) -> ConversationMessage:

        conversation = await self._owned(
            conversation_id,
            user_id,
        )

        message = ConversationMessage(
            conversation_id=conversation.id,
            role=role,
            content=content,
            actions=actions,
        )

        self.session.add(message)

        conversation.updated_at = (
            datetime.now(
                timezone.utc
            )
        )

        await self.session.flush()

        return message


    async def list_conversations(
        self,
        user_id: UUID,
    ) -> list[Conversation]:

        result = await self.session.scalars(
            select(Conversation)
            .where(
                Conversation.user_id
                == user_id,
                Conversation.archived_at
                .is_(None),
            )
            .order_by(
                Conversation.updated_at.desc()
            )
        )

        return list(
            result.all()
        )


    async def get_conversation(
        self,
        *,
        conversation_id: str,
        user_id: UUID,
    ) -> Conversation:

        try:
            conversation_uuid = UUID(
                str(conversation_id)
            )
        except ValueError as exc:
            raise ConversationNotFoundError() from exc

        conversation = await self.session.scalar(
            select(Conversation)
            .options(
                selectinload(
                    Conversation.messages
                )
            )
            .where(
                Conversation.id
                == conversation_uuid,
                Conversation.user_id
                == user_id,
                Conversation.archived_at
                .is_(None),
            )
        )

        if conversation is None:
            raise ConversationNotFoundError()

        conversation.messages.sort(
            key=lambda item: (
                item.created_at,
                str(item.id),
            )
        )

        return conversation


    async def create_conversation(
        self,
        user_id: UUID,
    ) -> Conversation:

        conversation = Conversation(
            user_id=user_id,
            title="New conversation",
        )

        self.session.add(
            conversation
        )

        await self.session.flush()

        return conversation


    async def archive_conversation(
        self,
        *,
        conversation_id: str,
        user_id: UUID,
    ) -> None:

        conversation = await self._owned(
            conversation_id,
            user_id,
        )

        conversation.archived_at = (
            datetime.now(
                timezone.utc
            )
        )

        await self.session.flush()


    async def _owned(
        self,
        conversation_id: str,
        user_id: UUID,
    ) -> Conversation:

        try:
            conversation_uuid = UUID(
                str(conversation_id)
            )
        except ValueError as exc:
            raise ConversationNotFoundError() from exc

        conversation = await self.session.scalar(
            select(Conversation)
            .where(
                Conversation.id
                == conversation_uuid,
                Conversation.user_id
                == user_id,
                Conversation.archived_at
                .is_(None),
            )
        )

        if conversation is None:
            raise ConversationNotFoundError()

        return conversation
