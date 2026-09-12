from __future__ import annotations

import re
from typing import Any


Record = dict[str, Any]


def _text(
    value: Any,
) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _normalize(
    value: Any,
) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        _text(value).lower(),
    ).strip()


def _pick(
    source: Record,
    *keys: str,
) -> Any:
    for key in keys:
        value = source.get(key)

        if value not in (
            None,
            "",
            [],
            {},
        ):
            return value

    return None


def _walk_records(
    value: Any,
    depth: int = 0,
):
    if depth > 6:
        return

    if isinstance(value, dict):
        yield value

        for child in value.values():
            yield from _walk_records(
                child,
                depth + 1,
            )

    elif isinstance(value, list):
        for child in value:
            yield from _walk_records(
                child,
                depth + 1,
            )


def _specialty(
    record: Record,
) -> str:
    value = _pick(
        record,
        "specialty",
        "specialty_name",
    )

    if isinstance(value, dict):
        return _text(
            _pick(
                value,
                "name",
                "specialty_name",
            )
        )

    return _text(value)


def _doctor_name(
    record: Record,
) -> str:
    return _text(
        _pick(
            record,
            "doctor_name",
            "full_name",
        )
    )


def _doctor_candidates(
    state: Record,
) -> list[Record]:
    result: list[Record] = []
    seen: set[str] = set()

    for record in _walk_records(state):
        name = _doctor_name(record)

        if not name:
            continue

        has_professional_data = any(
            key in record
            for key in (
                "specialty",
                "specialty_name",
                "qualification",
                "experience_years",
                "clinic_name",
                "clinic_location",
            )
        )

        if not has_professional_data:
            continue

        identity = _normalize(name)

        if not identity or identity in seen:
            continue

        seen.add(identity)
        result.append(record)

    return result


def _slot_candidates(
    state: Record,
) -> list[Record]:
    result: list[Record] = []
    seen: set[str] = set()

    for record in _walk_records(state):
        time = _text(
            _pick(
                record,
                "start_time",
                "time",
                "appointment_time",
            )
        )

        if not time:
            continue

        has_slot_marker = any(
            key in record
            for key in (
                "slot_date",
                "date",
                "doctor_slot_id",
                "slot_id",
                "is_available",
                "available",
            )
        )

        if not has_slot_marker:
            continue

        date = _text(
            _pick(
                record,
                "slot_date",
                "date",
                "appointment_date",
            )
        )

        identity = (
            f"{_normalize(date)}:"
            f"{_normalize(time)}:"
            f"{_normalize(_doctor_name(record))}"
        )

        if identity in seen:
            continue

        seen.add(identity)
        result.append(record)

    return result


def _doctor_payload(
    record: Record,
) -> Record:
    interests = _pick(
        record,
        "professional_interests",
        "interests",
        "expertise",
    )

    return {
        "component":
            "doctor_card",

        "doctor_name":
            _doctor_name(record),

        "specialty":
            _specialty(record),

        "qualification":
            _text(
                _pick(
                    record,
                    "qualification",
                    "qualifications",
                )
            ),

        "experience_years":
            _pick(
                record,
                "experience_years",
                "years_experience",
            ),

        "clinic_name":
            _text(
                _pick(
                    record,
                    "clinic_name",
                    "hospital_name",
                )
            ),

        "clinic_location":
            _text(
                _pick(
                    record,
                    "clinic_location",
                    "location",
                )
            ),

        "professional_interests":
            interests,

        "profile_image_url":
            _text(
                _pick(
                    record,
                    "profile_image_url",
                    "photo_url",
                    "image_url",
                )
            ),
    }


def _slot_payload(
    record: Record,
) -> Record:
    return {
        "component":
            "availability_slot",

        "doctor_name":
            _doctor_name(record),

        "date":
            _text(
                _pick(
                    record,
                    "slot_date",
                    "date",
                    "appointment_date",
                )
            ),

        "start_time":
            _text(
                _pick(
                    record,
                    "start_time",
                    "time",
                    "appointment_time",
                )
            ),

        "clinic_name":
            _text(
                _pick(
                    record,
                    "clinic_name",
                    "hospital_name",
                )
            ),
    }


def _booking_payload(
    record: Record,
) -> Record:
    return {
        "component":
            "appointment_preview",

        "doctor_name":
            _doctor_name(record),

        "specialty":
            _specialty(record),

        "clinic_name":
            _text(
                _pick(
                    record,
                    "clinic_name",
                    "hospital_name",
                )
            ),

        "date":
            _text(
                _pick(
                    record,
                    "date",
                    "slot_date",
                    "appointment_date",
                )
            ),

        "start_time":
            _text(
                _pick(
                    record,
                    "time",
                    "start_time",
                    "appointment_time",
                )
            ),

        "consultation_fee":
            _pick(
                record,
                "consultation_fee",
                "fee",
            ),
    }


def _matches(
    action: Record,
    value: str,
) -> bool:
    needle = _normalize(value)

    if not needle:
        return False

    haystack = _normalize(
        " ".join(
            [
                _text(
                    action.get(
                        "label"
                    )
                ),
                _text(
                    action.get(
                        "message"
                    )
                ),
            ]
        )
    )

    return (
        needle in haystack
        or
        haystack in needle
    )


def enrich_chat_actions(
    raw_actions: list[Record],
    state: Record,
) -> list[Record]:
    actions = [
        dict(action)
        for action in raw_actions
    ]

    doctors = _doctor_candidates(
        state
    )

    slots = _slot_candidates(
        state
    )

    unused_doctors = list(doctors)
    unused_slots = list(slots)

    for action in actions:
        action_type = _text(
            action.get("type")
        )

        if action_type == "send_message":
            match = None

            for doctor in unused_doctors:
                name = _doctor_name(
                    doctor
                )

                if _matches(
                    action,
                    name,
                ):
                    match = doctor
                    break

            if (
                match is None
                and unused_doctors
            ):
                match = (
                    unused_doctors[0]
                )

            if match is not None:
                action["payload"] = (
                    _doctor_payload(
                        match
                    )
                )

                unused_doctors.remove(
                    match
                )

        elif action_type == "book_slot":
            match = None

            for slot in unused_slots:
                time = _text(
                    _pick(
                        slot,
                        "start_time",
                        "time",
                    )
                )

                if _matches(
                    action,
                    time,
                ):
                    match = slot
                    break

            if (
                match is None
                and unused_slots
            ):
                match = (
                    unused_slots[0]
                )

            if match is not None:
                action["payload"] = (
                    _slot_payload(
                        match
                    )
                )

                unused_slots.remove(
                    match
                )

        elif action_type == "confirm":
            pending = state.get(
                "pending_booking"
            )

            if isinstance(
                pending,
                dict,
            ):
                action["payload"] = (
                    _booking_payload(
                        pending
                    )
                )

    return actions
