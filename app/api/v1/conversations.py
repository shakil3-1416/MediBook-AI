from fastapi import (
    APIRouter,
    HTTPException,
)

from app.core.auth import CurrentUser
from app.core.database import AsyncSessionFactory

from app.schemas.conversation import (
    ConversationDetail,
    ConversationListResponse,
    ConversationMessageResponse,
    ConversationSummary,
    NewConversationResponse,
)

from app.services.conversation_service import (
    ConversationNotFoundError,
    ConversationService,
)


router = APIRouter()


@router.get(
    "",
    response_model=ConversationListResponse,
)
async def list_conversations(
    current_user: CurrentUser,
) -> ConversationListResponse:

    async with AsyncSessionFactory() as session:

        service = ConversationService(
            session
        )

        conversations = (
            await service.list_conversations(
                current_user.id
            )
        )

    return ConversationListResponse(
        conversations=[
            ConversationSummary(
                id=item.id,
                title=item.title,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in conversations
        ]
    )


@router.post(
    "",
    response_model=NewConversationResponse,
    status_code=201,
)
async def new_conversation(
    current_user: CurrentUser,
) -> NewConversationResponse:

    async with AsyncSessionFactory() as session:

        service = ConversationService(
            session
        )

        conversation = (
            await service.create_conversation(
                current_user.id
            )
        )

        await session.commit()

    return NewConversationResponse(
        id=conversation.id,
        title=conversation.title,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetail,
)
async def get_conversation(
    conversation_id: str,
    current_user: CurrentUser,
) -> ConversationDetail:

    try:

        async with AsyncSessionFactory() as session:

            service = ConversationService(
                session
            )

            conversation = (
                await service.get_conversation(
                    conversation_id=conversation_id,
                    user_id=current_user.id,
                )
            )

            messages = [
                ConversationMessageResponse(
                    id=item.id,
                    role=item.role,
                    content=item.content,
                    actions=item.actions,
                    created_at=item.created_at,
                )
                for item in conversation.messages
            ]

            return ConversationDetail(
                id=conversation.id,
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                messages=messages,
            )

    except ConversationNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        ) from exc


@router.delete(
    "/{conversation_id}",
    status_code=204,
)
async def delete_conversation(
    conversation_id: str,
    current_user: CurrentUser,
):

    try:

        async with AsyncSessionFactory() as session:

            service = ConversationService(
                session
            )

            await service.archive_conversation(
                conversation_id=conversation_id,
                user_id=current_user.id,
            )

            await session.commit()

    except ConversationNotFoundError as exc:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        ) from exc
