from __future__ import annotations

import re
from typing import Any


def normalize_name(
    value: str,
) -> str:
    value = value.lower().strip()

    value = re.sub(
        r"\bdr\.?\s*",
        "",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def exact_doctor_match(
    doctors: list[Any],
    requested_name: str,
):
    target = normalize_name(
        requested_name
    )

    exact = []

    for doctor in doctors:
        if isinstance(
            doctor,
            dict,
        ):
            name = (
                doctor.get("full_name")
                or doctor.get("name")
                or ""
            )
        else:
            name = (
                getattr(
                    doctor,
                    "full_name",
                    None,
                )
                or getattr(
                    doctor,
                    "name",
                    "",
                )
            )

        if (
            normalize_name(
                str(name)
            )
            == target
        ):
            exact.append(
                doctor
            )

    if len(exact) == 1:
        return exact[0]

    return None


def extract_doctor_name(
    message: str,
) -> str | None:
    patterns = [
        r"\bdr\.?\s+([a-zA-Z][a-zA-Z .'-]*?\d{0,4})(?=[,.]|\s+(?:on|at|tomorrow|today|for|check|book|give|please|availability)\b|$)",
        r"\bdoctor\s+([a-zA-Z][a-zA-Z .'-]*?\d{0,4})(?=[,.]|\s+(?:on|at|tomorrow|today|for|check|book|give|please|availability)\b|$)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            message,
            flags=re.IGNORECASE,
        )

        if match:
            value = match.group(1).strip()

            if value:
                return f"Dr. {value}"

    return None
