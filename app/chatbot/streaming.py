import asyncio
import json
from collections.abc import AsyncIterator

from app.schemas.chat import (
    ChatAction,
    ChatStreamEvent,
)


def encode_event(
    event: ChatStreamEvent,
) -> str:
    return (
        json.dumps(
            event.model_dump(
                exclude_none=True
            ),
            ensure_ascii=False,
        )
        + "\n"
    )


async def stream_text_chunks(
    text: str,
    *,
    chunk_size: int = 20,
) -> AsyncIterator[str]:
    if not text:
        return

    for index in range(
        0,
        len(text),
        chunk_size,
    ):
        yield text[
            index:
            index + chunk_size
        ]

        # Yield control to the event loop.
        await asyncio.sleep(0)


async def stream_grounded_response(
    *,
    response: str,
    conversation_id: str,
    actions: list[ChatAction] | None = None,
) -> AsyncIterator[str]:

    async for chunk in stream_text_chunks(
        response
    ):
        yield encode_event(
            ChatStreamEvent(
                type="text_delta",
                delta=chunk,
            )
        )

    if actions:
        yield encode_event(
            ChatStreamEvent(
                type="actions",
                actions=actions,
            )
        )

    yield encode_event(
        ChatStreamEvent(
            type="done",
            conversation_id=(
                conversation_id
            ),
        )
    )
