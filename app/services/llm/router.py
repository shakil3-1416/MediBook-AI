from dataclasses import dataclass
from typing import Literal

from app.services.llm.fast_router import (
    fast_route,
)

from app.services.llm.heuristic_router import (
    route_heuristically,
)

from app.services.llm.safety_router import (
    safety_route,
)


RouteSource = Literal[
    "fast",
    "safety",
    "heuristic",
    "fallback",
]


@dataclass(slots=True)
class RoutingDecision:
    source: RouteSource
    intent: str
    confidence: float

    response: str | None = None

    entities: dict | None = None

    degraded: bool = False


async def route_message(
    message: str,
) -> RoutingDecision:

    # --------------------------------------------------
    # Tier 0A — high-confidence deterministic routes
    # --------------------------------------------------

    fast = fast_route(
        message
    )

    if fast.matched:
        return RoutingDecision(
            source="fast",
            intent=fast.route,
            confidence=1.0,
            response=fast.response,
            entities=fast.entities,
        )

    # --------------------------------------------------
    # Tier 0B — deterministic safety boundary
    # --------------------------------------------------

    safety = safety_route(
        message
    )

    if safety.matched:
        return RoutingDecision(
            source="safety",
            intent=safety.route,
            confidence=1.0,
            response=safety.response,
        )

    # --------------------------------------------------
    # Tier 0C — low-cost linguistic heuristics
    # --------------------------------------------------

    heuristic = route_heuristically(
        message
    )

    if heuristic.matched:
        return RoutingDecision(
            source="heuristic",
            intent=heuristic.intent,
            confidence=heuristic.confidence,
            entities=heuristic.entities,
        )

    # --------------------------------------------------
    # Unknown language does NOT block on an LLM.
    #
    # The conversational layer may subsequently use the
    # generation model, but routing itself remains fast.
    # --------------------------------------------------

    return RoutingDecision(
        source="fallback",
        intent="unknown",
        confidence=0.0,
        degraded=False,
    )
