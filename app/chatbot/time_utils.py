import re

from datetime import time


TWELVE_HOUR_PATTERN = re.compile(
    r"\b"
    r"(?P<hour>1[0-2]|0?[1-9])"
    r"(?:\s*:\s*(?P<minute>[0-5]\d))?"
    r"\s*(?P<period>am|pm)"
    r"\b",
    re.IGNORECASE,
)


TWENTY_FOUR_HOUR_PATTERN = re.compile(
    r"\b"
    r"(?P<hour>[01]?\d|2[0-3])"
    r"\s*:\s*"
    r"(?P<minute>[0-5]\d)"
    r"\b",
)


def resolve_booking_time(
    text: str,
) -> time | None:
    """
    Deterministically parse appointment time text into a
    datetime.time object suitable for PostgreSQL TIME columns.

    Examples:
        5 PM       -> time(17, 0)
        5:30 PM    -> time(17, 30)
        12 PM      -> time(12, 0)
        12 AM      -> time(0, 0)
        17:30      -> time(17, 30)
    """

    if not text:
        return None

    value = text.strip()


    # --------------------------------------------------
    # Explicit 12-hour clock
    # --------------------------------------------------

    match = TWELVE_HOUR_PATTERN.search(
        value
    )

    if match:

        hour = int(
            match.group("hour")
        )

        minute = int(
            match.group("minute")
            or "00"
        )

        period = (
            match.group("period")
            .lower()
        )


        if period == "am":

            if hour == 12:
                hour = 0

        else:

            if hour != 12:
                hour += 12


        return time(
            hour,
            minute,
        )


    # --------------------------------------------------
    # Explicit 24-hour clock
    # --------------------------------------------------

    match = (
        TWENTY_FOUR_HOUR_PATTERN
        .search(
            value
        )
    )

    if match:

        return time(
            int(
                match.group("hour")
            ),
            int(
                match.group("minute")
            ),
        )


    return None


def canonical_time(
    value: str | time,
) -> time | None:

    if isinstance(
        value,
        time,
    ):
        return value

    return resolve_booking_time(
        value
    )


def time_is_available(
    requested_time: str | time,
    available_times: list[str | time],
) -> bool:

    requested = canonical_time(
        requested_time
    )

    if requested is None:
        return False

    normalized = {
        canonical_time(value)
        for value in available_times
    }

    normalized.discard(
        None
    )

    return requested in normalized
