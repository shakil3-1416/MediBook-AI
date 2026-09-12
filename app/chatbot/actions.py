from datetime import time
from typing import Any


def pretty_time(
    value: str | time,
) -> str:

    if isinstance(value, time):

        hour = value.hour
        minute = f"{value.minute:02d}"

    else:

        hour_value, minute = (
            value.split(":")[:2]
        )

        hour = int(hour_value)

    period = (
        "PM"
        if hour >= 12
        else "AM"
    )

    display_hour = (
        hour % 12
        or 12
    )

    return (
        f"{display_hour}:{minute} "
        f"{period}"
    )


def build_chat_actions(
    state: dict[str, Any],
) -> list[dict[str, str]]:

    actions: list[
        dict[str, str]
    ] = []

    # -----------------------------------------------------
    # Destructive or state-changing action awaiting confirm
    # -----------------------------------------------------

    pending_action = state.get(
        "pending_action"
    )

    if pending_action:

        action_type = (
            pending_action.get(
                "type"
            )
        )

        if action_type == "cancel":
            return [
                {
                    "id": "confirm-cancel",
                    "type": "confirm",
                    "label": "Confirm cancellation",
                    "message": "Confirm",
                    "variant": "danger",
                },
                {
                    "id": "keep-appointment",
                    "type": "cancel",
                    "label": "Keep appointment",
                    "message": "Keep Appointment",
                    "variant": "secondary",
                },
            ]

        if action_type == "reschedule":
            return [
                {
                    "id": "confirm-reschedule",
                    "type": "confirm",
                    "label": "Confirm reschedule",
                    "message": "Confirm",
                    "variant": "primary",
                },
                {
                    "id": "keep-appointment",
                    "type": "cancel",
                    "label": "Keep appointment",
                    "message": "Keep Appointment",
                    "variant": "secondary",
                },
            ]

    # -----------------------------------------------------
    # Pending new booking
    # -----------------------------------------------------

    pending_booking = state.get(
        "pending_booking"
    )

    patient = state.get(
        "patient"
    )

    if (
        pending_booking
        and patient
    ):
        return [
            {
                "id": "confirm-booking",
                "type": "confirm",
                "label": "Confirm booking",
                "message": "Confirm",
                "variant": "primary",
            },
            {
                "id": "cancel-booking",
                "type": "cancel",
                "label": "Cancel",
                "message": "Cancel",
                "variant": "secondary",
            },
        ]

    # -----------------------------------------------------
    # Available slot choices
    # -----------------------------------------------------

    slots = state.get(
        "last_slots"
    ) or []

    if slots:

        for index, slot in enumerate(
            slots[:8]
        ):
            actions.append(
                {
                    "id": (
                        f"slot-{index}-{slot}"
                    ),
                    "type": "book_slot",
                    "label": pretty_time(
                        slot
                    ),
                    "message": (
                        "Book the "
                        f"{pretty_time(slot)} "
                        "one"
                    ),
                    "variant": "secondary",
                }
            )

        return actions

    # -----------------------------------------------------
    # Single selected appointment
    # -----------------------------------------------------

    selected = state.get(
        "selected_appointment"
    )

    if selected:

        return [
            {
                "id": "reschedule-appointment",
                "type": "reschedule",
                "label": "Reschedule",
                "message": (
                    "Reschedule this appointment"
                ),
                "variant": "primary",
            },
            {
                "id": "cancel-appointment",
                "type": "cancel",
                "label": "Cancel appointment",
                "message": (
                    "Cancel this appointment"
                ),
                "variant": "danger",
            },
        ]

    return []
