from collections.abc import AsyncIterator

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
)

from fastapi.responses import (
    StreamingResponse,
)

from app.chatbot.chat_action_payloads import enrich_chat_actions
from app.chatbot.actions import (
    build_chat_actions,
)

from app.chatbot.hospital_grounded_directory import grounded_doctor_directory_result
from app.chatbot.hospital_grounded_followups import grounded_doctor_followup_result
from app.chatbot.orchestrator import (
    handle_conversation,
)

from app.chatbot.session import (
    create_conversation_id,
    load_session,
)

from app.chatbot.streaming import (
    encode_event,
    stream_grounded_response,
)

from app.chatbot.stream_status import (
    status_for_message,
)

from app.schemas.chat import (
    ChatAction,
    ChatRequest,
    ChatResponse,
    ChatStreamEvent,
)

from app.core.auth import CurrentUser
from app.core.database import AsyncSessionFactory
from app.services.hospital_context import (
    HospitalContextError,
    resolve_hospital,
)
from app.services.conversation_service import (
    ConversationNotFoundError,
    ConversationOwnershipError,
    ConversationService,
)


from app.chatbot.session import save_session

router = APIRouter()


# ============================================================
# Shared application service
# ============================================================

async def process_chat_request(
    request: ChatRequest,
    current_user: CurrentUser,
    hospital_slug: str,
) -> ChatResponse:

    conversation_id = (
        request.conversation_id
        or create_conversation_id()
    )

    async with AsyncSessionFactory() as db_session:
        try:
            hospital = await resolve_hospital(
                db_session,
                hospital_slug=hospital_slug,
            )
        except HospitalContextError as exc:
            raise HTTPException(
                status_code=404,
                detail="Hospital workspace not found.",
            ) from exc

    # --------------------------------------------------
    # Persist / validate conversation ownership first.
    # --------------------------------------------------

    async with AsyncSessionFactory() as db_session:

        history = ConversationService(
            db_session
        )

        try:
            await history.ensure_conversation(
                conversation_id=conversation_id,
                user_id=current_user.id,
                first_message=request.message,
            )

            await history.append_message(
                conversation_id=conversation_id,
                user_id=current_user.id,
                role="user",
                content=request.message,
            )

            await db_session.commit()

        except (
            ConversationNotFoundError,
            ConversationOwnershipError,
        ) as exc:
            await db_session.rollback()

            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            ) from exc

    # --------------------------------------------------
    # Redis owns only transient workflow state.
    # --------------------------------------------------

    state = await load_session(
        conversation_id
    )

    state["patient_phone"] = (
        current_user.phone
    )

    state["patient"] = {
        "name":
            current_user.full_name,

        "phone":
            current_user.phone,
    }

    state["authenticated_user_id"] = (
        str(current_user.id)
    )

    existing_hospital_id = state.get(
        "hospital_id"
    )

    if (
        existing_hospital_id
        and
        existing_hospital_id
        != str(hospital.id)
    ):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    state["hospital_id"] = str(
        hospital.id
    )

    state["hospital_slug"] = (
        hospital.slug
    )

    await save_session(
        conversation_id,
        state,
    )

    # --------------------------------------------------
    # Existing grounded MediBook orchestration.
    # --------------------------------------------------

    async with AsyncSessionFactory() as db_session:
        grounded_directory = (
            await grounded_doctor_directory_result(
                db_session,
                hospital_id=hospital.id,
                message=request.message,
            )
        )

    state = await load_session(
        conversation_id
    )

    grounded_followup = None

    if grounded_directory is None:
        async with AsyncSessionFactory() as db_session:
            grounded_followup = (
                await grounded_doctor_followup_result(
                    db_session,
                    hospital_id=hospital.id,
                    message=request.message,
                    state=state,
                )
            )

    if grounded_directory is not None:
        response = grounded_directory[
            "response"
        ]

        references = grounded_directory[
            "references"
        ]

        state[
            "grounded_doctor_results"
        ] = references

        state[
            "doctor_results"
        ] = references

        state[
            "last_doctors"
        ] = references

        state[
            "grounded_ui_actions"
        ] = grounded_directory[
            "actions"
        ]

        await save_session(
            conversation_id,
            state,
        )

    elif grounded_followup is not None:
        response = grounded_followup[
            "response"
        ]

        for key, value in (
            grounded_followup
            .get(
                "state_updates",
                {},
            )
            .items()
        ):
            state[key] = value

        state[
            "grounded_ui_actions"
        ] = grounded_followup.get(
            "actions",
            [],
        )

        await save_session(
            conversation_id,
            state,
        )

    else:
        response = await handle_conversation(
            conversation_id,
            request.message,
            hospital_id=hospital.id,
        )

    state = await load_session(
        conversation_id
    )

    raw_actions = enrich_chat_actions(
        build_chat_actions(state),
        state,
    )

    grounded_ui_actions = state.pop(
        "grounded_ui_actions",
        [],
    )

    if isinstance(
        grounded_ui_actions,
        list,
    ):
        raw_actions.extend(
            grounded_ui_actions
        )

    await save_session(
        conversation_id,
        state,
    )

    actions = [
        ChatAction(
            **action
        )
        for action in raw_actions
    ]

    # --------------------------------------------------
    # Persist completed assistant response.
    # --------------------------------------------------

    async with AsyncSessionFactory() as db_session:

        history = ConversationService(
            db_session
        )

        await history.append_message(
            conversation_id=conversation_id,
            user_id=current_user.id,
            role="assistant",
            content=response,
            actions=[
                action.model_dump()
                for action in actions
            ] or None,
        )

        await db_session.commit()

    return ChatResponse(
        response=response,
        conversation_id=conversation_id,
        actions=actions,
    )


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    current_user: CurrentUser,
    hospital_slug: str | None = Header(
        default=None,
        alias="X-MediBook-Hospital-Slug",
    ),
) -> ChatResponse:

    try:
        if not hospital_slug:
            raise HTTPException(
                status_code=400,
                detail="Hospital context is required.",
            )

        return await process_chat_request(
            request,
            current_user,
            hospital_slug,
        )

    except Exception as exc:

        print(
            "CHAT ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "MediBook AI is temporarily "
                "unable to complete that request."
            ),
        ) from exc


# ============================================================
# NDJSON streaming endpoint
# ============================================================

@router.post(
    "/stream",
    response_class=StreamingResponse,
)
async def stream_chat(
    request: ChatRequest,
    current_user: CurrentUser,
    hospital_slug: str | None = Header(
        default=None,
        alias="X-MediBook-Hospital-Slug",
    ),
) -> StreamingResponse:

    async def event_stream() -> AsyncIterator[str]:

        try:

            # Immediate operational feedback.
            yield encode_event(
                ChatStreamEvent(
                    type="status",
                    message=status_for_message(
                        request.message
                    ),
                )
            )

            # Run the exact same grounded MediBook workflow
            # used by the normal /chat endpoint.
            if not hospital_slug:
                raise HTTPException(
                    status_code=400,
                    detail="Hospital context is required.",
                )

            result = await process_chat_request(
                request,
                current_user,
                hospital_slug,
            )

            # Stream the already-grounded application response.
            async for event in stream_grounded_response(
                response=result.response,
                conversation_id=result.conversation_id,
                actions=result.actions,
            ):
                yield event

        except Exception as exc:

            # Keep this log during development.
            # It prevents streaming failures from becoming opaque.
            print(
                "CHAT STREAM ERROR:",
                repr(exc),
            )

            yield encode_event(
                ChatStreamEvent(
                    type="error",
                    message=(
                        "MediBook could not complete "
                        "that request."
                    ),
                )
            )

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff",
        },
    )
