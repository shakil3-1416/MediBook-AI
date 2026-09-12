from app.services.llm.fast_router import (
    fast_route,
)

from app.services.llm.safety_router import (
    safety_route,
)

from app.services.llm.heuristic_router import (
    route_heuristically,
)


def status_for_message(
    message: str,
) -> str:

    fast = fast_route(
        message
    )

    if fast.matched:

        if fast.route == "search_doctor":
            return (
                "Searching the MediBook doctor directory…"
            )

        if fast.route == "capabilities":
            return (
                "Preparing MediBook capabilities…"
            )

        if fast.route == "greeting":
            return "Ready."

    safety = safety_route(
        message
    )

    if safety.matched:
        return (
            "Checking the request against MediBook safety rules…"
        )

    heuristic = route_heuristically(
        message
    )

    statuses = {
        "check_availability":
            "Checking real appointment availability…",

        "book_appointment":
            "Preparing your appointment request…",

        "list_appointments":
            "Looking up your MediBook appointments…",

        "cancel_appointment":
            "Preparing the cancellation request…",

        "reschedule_appointment":
            "Checking your rescheduling options…",

        "search_doctor":
            "Searching the MediBook doctor directory…",
    }

    return statuses.get(
        heuristic.intent,
        "Working on your request…",
    )
