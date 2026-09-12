from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.hospital_directory_service import (
    HospitalDirectoryService,
)


SEARCH_VERBS = (
    "find",
    "show",
    "list",
    "search",
    "recommend",
    "looking for",
    "look for",
)


DOCTOR_WORDS = (
    "doctor",
    "doctors",
    "specialist",
    "specialists",
    "physician",
    "physicians",
)


def _normalize(
    value: str,
) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        value.lower(),
    ).strip()


def is_explicit_doctor_search(
    message: str,
) -> bool:
    value = _normalize(
        message
    )

    has_doctor_word = any(
        word in value
        for word in DOCTOR_WORDS
    )

    has_search_verb = any(
        verb in value
        for verb in SEARCH_VERBS
    )

    return (
        has_doctor_word
        and
        has_search_verb
    )


def _specialty_matches(
    message: str,
    specialty: str,
) -> bool:
    msg = _normalize(
        message
    )

    spec = _normalize(
        specialty
    )

    if not spec:
        return False

    if spec in msg:
        return True

    msg_tokens = {
        token
        for token in msg.split()
        if len(token) >= 5
    }

    spec_tokens = {
        token
        for token in spec.split()
        if len(token) >= 5
    }

    for left in msg_tokens:
        for right in spec_tokens:

            prefix = min(
                len(left),
                len(right),
                6,
            )

            if (
                prefix >= 5
                and
                left[:prefix]
                ==
                right[:prefix]
            ):
                return True

    aliases = {
        "orthopedic": (
            "orthopedic",
            "orthopaedic",
            "orthopedics",
            "orthopaedics",
        ),
        "cardiology": (
            "cardiology",
            "cardiologist",
            "cardiac",
        ),
        "dermatology": (
            "dermatology",
            "dermatologist",
            "skin",
        ),
        "neurology": (
            "neurology",
            "neurologist",
        ),
        "ent": (
            "ent",
            "ear nose throat",
            "otolaryngology",
        ),
        "gynecology": (
            "gynecology",
            "gynaecology",
            "gynecologist",
            "gynaecologist",
        ),
        "pediatrics": (
            "pediatrics",
            "paediatrics",
            "pediatrician",
            "paediatrician",
        ),
    }

    for family in aliases.values():
        message_hit = any(
            alias in msg
            for alias in family
        )

        specialty_hit = any(
            alias in spec
            for alias in family
        )

        if (
            message_hit
            and
            specialty_hit
        ):
            return True

    return False


def _doctor_payload(
    doctor: Any,
) -> dict:
    specialty = getattr(
        doctor,
        "specialty",
        None,
    )

    specialty_name = getattr(
        specialty,
        "name",
        None,
    )

    return {
        "component":
            "doctor_card",

        "doctor_name":
            doctor.full_name,

        "specialty":
            specialty_name,

        "qualification":
            getattr(
                doctor,
                "qualification",
                None,
            ),

        "experience_years":
            getattr(
                doctor,
                "experience_years",
                None,
            ),

        "clinic_name":
            getattr(
                doctor,
                "clinic_name",
                None,
            ),

        "clinic_location":
            getattr(
                doctor,
                "clinic_location",
                None,
            ),

        "professional_interests":
            getattr(
                doctor,
                "professional_interests",
                None,
            ),

        "profile_image_url":
            getattr(
                doctor,
                "profile_image_url",
                None,
            ),
    }


async def grounded_doctor_directory_result(
    session: AsyncSession,
    *,
    hospital_id: uuid.UUID,
    message: str,
) -> dict | None:

    if not is_explicit_doctor_search(
        message
    ):
        return None

    service = HospitalDirectoryService(
        session
    )

    doctors = await service.list_doctors(
        hospital_id=hospital_id,
        limit=500,
    )

    if not doctors:
        return {
            "response": (
                "I could not find any doctors "
                "available through this hospital."
            ),
            "actions": [],
            "references": [],
        }

    specialties = []

    for doctor in doctors:
        specialty = getattr(
            getattr(
                doctor,
                "specialty",
                None,
            ),
            "name",
            None,
        )

        if (
            specialty
            and
            specialty not in specialties
        ):
            specialties.append(
                specialty
            )

    mentioned = [
        specialty
        for specialty in specialties
        if _specialty_matches(
            message,
            specialty,
        )
    ]

    if mentioned:
        doctors = [
            doctor
            for doctor in doctors
            if getattr(
                getattr(
                    doctor,
                    "specialty",
                    None,
                ),
                "name",
                None,
            )
            in mentioned
        ]

    normalized = _normalize(
        message
    )

    if (
        "female" in normalized
        or
        "woman doctor" in normalized
    ):
        doctors = [
            doctor
            for doctor in doctors
            if _normalize(
                str(
                    getattr(
                        doctor,
                        "gender",
                        "",
                    )
                )
            )
            == "female"
        ]

    elif (
        "male doctor" in normalized
    ):
        doctors = [
            doctor
            for doctor in doctors
            if _normalize(
                str(
                    getattr(
                        doctor,
                        "gender",
                        "",
                    )
                )
            )
            == "male"
        ]

    if not doctors:
        return {
            "response": (
                "I could not find a matching "
                "doctor in this hospital."
            ),
            "actions": [],
            "references": [],
        }

    visible = doctors[:6]

    references = []

    actions = []

    for index, doctor in enumerate(
        visible,
        1,
    ):
        specialty = getattr(
            getattr(
                doctor,
                "specialty",
                None,
            ),
            "name",
            None,
        )

        reference = {
            "position":
                index,

            "id":
                str(
                    doctor.id
                ),

            "doctor_id":
                str(
                    doctor.id
                ),

            "doctor_name":
                doctor.full_name,

            "full_name":
                doctor.full_name,

            "specialty":
                specialty,
        }

        references.append(
            reference
        )

        actions.append({
            "id":
                f"doctor:{doctor.id}",

            "type":
                "send_message",

            "label":
                doctor.full_name,

            "message":
                (
                    "Tell me about "
                    f"{doctor.full_name}"
                ),

            "variant":
                "secondary",

            "payload":
                _doctor_payload(
                    doctor
                ),
        })

    count = len(
        visible
    )

    response = (
        f"I found {count} matching "
        f"{'doctor' if count == 1 else 'doctors'} "
        "in this hospital. "
        "You can ask me about any of them, "
        "their availability, or their schedule."
    )

    return {
        "response":
            response,

        "actions":
            actions,

        "references":
            references,
    }
