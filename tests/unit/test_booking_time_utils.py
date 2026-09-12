from datetime import time

import pytest

from app.chatbot.actions import (
    pretty_time,
)
from app.chatbot.time_utils import (
    resolve_booking_time,
    time_is_available,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Book the 5 PM one",
            time(17, 0),
        ),
        (
            "Book the 5:00 PM one",
            time(17, 0),
        ),
        (
            "Book the 5:30 PM one",
            time(17, 30),
        ),
        (
            "book 6 pm",
            time(18, 0),
        ),
        (
            "Book 6:30 PM",
            time(18, 30),
        ),
        (
            "Book 7 PM",
            time(19, 0),
        ),
        (
            "Book at 12 PM",
            time(12, 0),
        ),
        (
            "Book at 12 AM",
            time(0, 0),
        ),
        (
            "Book 17:30",
            time(17, 30),
        ),
        (
            "Book 05:30",
            time(5, 30),
        ),
    ],
)
def test_booking_time_normalization(
    text,
    expected,
):
    assert (
        resolve_booking_time(text)
        == expected
    )


def test_pm_does_not_become_am():

    assert (
        resolve_booking_time(
            "Book the 5:30 PM one"
        )
        != time(5, 30)
    )


def test_real_slot_match():

    available = [
        time(17, 0),
        time(17, 30),
        time(18, 0),
        time(18, 30),
        time(19, 0),
    ]

    assert time_is_available(
        time(17, 30),
        available,
    )

    assert not time_is_available(
        time(5, 30),
        available,
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            time(17, 0),
            "5:00 PM",
        ),
        (
            time(17, 30),
            "5:30 PM",
        ),
        (
            time(18, 0),
            "6:00 PM",
        ),
        (
            time(0, 0),
            "12:00 AM",
        ),
        (
            time(12, 0),
            "12:00 PM",
        ),
    ],
)
def test_action_display_time(
    value,
    expected,
):

    assert (
        pretty_time(value)
        == expected
    )
