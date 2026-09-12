import time

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.llm.gateway import (
    llm_gateway,
)

from app.services.llm.router import (
    route_message,
)


router = APIRouter()


class RoutingRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )


@router.get(
    "/health",
)
async def llm_health() -> dict:

    started = time.perf_counter()

    healthy = (
        await llm_gateway.health()
    )

    elapsed = (
        time.perf_counter()
        - started
    ) * 1000

    return {
        "healthy": healthy,
        "model": (
            llm_gateway.model
        ),
        "latency_ms": round(
            elapsed,
            2,
        ),
    }


@router.post(
    "/route",
)
async def inspect_route(
    request: RoutingRequest,
) -> dict:

    started = (
        time.perf_counter()
    )

    decision = (
        await route_message(
            request.message
        )
    )

    elapsed = (
        time.perf_counter()
        - started
    ) * 1000

    return {
        "source": decision.source,
        "intent": decision.intent,
        "confidence": (
            decision.confidence
        ),
        "entities": (
            decision.entities
        ),
        "deterministic_response": (
            decision.response
        ),
        "degraded": (
            decision.degraded
        ),
        "routing_latency_ms": round(
            elapsed,
            2,
        ),
    }
