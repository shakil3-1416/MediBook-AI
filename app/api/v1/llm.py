from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.llm.fast_router import (
    fast_route,
)
from app.services.llm.gateway import (
    llm_gateway,
)
from app.services.llm.policy import (
    MEDIBOOK_SYSTEM_POLICY,
)


router = APIRouter()


class StreamRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )


async def stream_text(
    text: str,
) -> AsyncIterator[str]:
    yield text


async def stream_llm_response(
    message: str,
) -> AsyncIterator[str]:

    routed = fast_route(
        message
    )

    # Fast deterministic path:
    # no Ollama request required.
    if routed.matched:
        yield routed.response or ""
        return

    async for token in (
        llm_gateway.stream_chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        MEDIBOOK_SYSTEM_POLICY
                    ),
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            temperature=0.1,
            num_predict=220,
        )
    ):
        yield token


@router.post(
    "/stream",
    response_class=StreamingResponse,
)
async def stream_llm(
    request: StreamRequest,
) -> StreamingResponse:

    return StreamingResponse(
        stream_llm_response(
            request.message
        ),
        media_type=(
            "text/plain; charset=utf-8"
        ),
        headers={
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": (
                "nosniff"
            ),
        },
    )
