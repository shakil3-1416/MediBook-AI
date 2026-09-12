from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)

import hashlib
import hmac
import os
import re
import secrets
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password

from app.services.verification_email_service import (
    EmailDeliveryNotConfigured,
    send_verification_code,
)


router = APIRouter(
    prefix="/auth/signup",
    tags=["authentication"],
)


OTP_TTL_SECONDS = 600
OTP_RESEND_SECONDS = 60
OTP_MAX_ATTEMPTS = 5


class StartSignupRequest(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=200,
    )

    email: EmailStr

    phone: str = Field(
        min_length=6,
        max_length=32,
    )

    gender: str = Field(
        min_length=1,
        max_length=32,
    )

    password: str = Field(
        min_length=8,
        max_length=256,
    )

    profile_image_url: (
        str | None
    ) = Field(
        default=None,
        max_length=1000,
    )


class VerifySignupRequest(BaseModel):
    email: EmailStr

    code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )


class ResendSignupRequest(BaseModel):
    email: EmailStr


def now_utc() -> datetime:
    return datetime.now(
        timezone.utc
    )


def normalize_email(
    value: str,
) -> str:
    return (
        value.strip().lower()
    )


def normalize_phone(
    value: str,
) -> str:
    value = re.sub(
        r"[^\d+]",
        "",
        value.strip(),
    )

    if (
        value.startswith("01")
        and
        len(value) == 11
    ):
        return (
            "+880"
            +
            value[1:]
        )

    if (
        value.startswith("880")
        and
        not value.startswith("+")
    ):
        return (
            "+"
            +
            value
        )

    return value


def normalize_gender(
    value: str,
) -> str:
    value = (
        value.strip().lower()
    )

    allowed = {
        "male",
        "female",
        "other",
        "prefer_not_to_say",
    }

    if value not in allowed:
        raise HTTPException(
            status_code=422,
            detail=(
                "Gender must be male, female, other, "
                "or prefer_not_to_say."
            ),
        )

    return value


def verification_secret() -> bytes:
    secret = (
        os.getenv(
            "MEDIBOOK_OTP_SECRET",
            "",
        )
        or os.getenv(
            "JWT_SECRET_KEY",
            "",
        )
        or os.getenv(
            "SECRET_KEY",
            "",
        )
    )

    if not secret:
        raise RuntimeError(
            "No OTP/application secret configured."
        )

    return secret.encode()


def hash_code(
    email: str,
    code: str,
) -> str:
    return hmac.new(
        verification_secret(),
        f"{email}:{code}".encode(),
        hashlib.sha256,
    ).hexdigest()


def create_code() -> str:
    return (
        f"{secrets.randbelow(1_000_000):06d}"
    )


async def find_conflict(
    db: AsyncSession,
    email: str,
    phone: str,
):
    result = await db.execute(
        text(
            """
            SELECT
                email,
                phone
            FROM users
            WHERE lower(email) = :email
               OR phone = :phone
            LIMIT 1
            """
        ),
        {
            "email": email,
            "phone": phone,
        },
    )

    user = (
        result.mappings().first()
    )

    if user:
        return "user"

    result = await db.execute(
        text(
            """
            SELECT phone
            FROM patients
            WHERE phone = :phone
            LIMIT 1
            """
        ),
        {
            "phone": phone,
        },
    )

    if result.first():
        return "patient"

    return None


@router.post(
    "/start",
    status_code=202,
)
async def start_signup(
    payload: StartSignupRequest,
    db: AsyncSession = Depends(
        get_db
    ),
):
    email = normalize_email(
        str(payload.email)
    )

    phone = normalize_phone(
        payload.phone
    )

    gender = normalize_gender(
        payload.gender
    )

    conflict = await find_conflict(
        db,
        email,
        phone,
    )

    if conflict:
        raise HTTPException(
            status_code=409,
            detail=(
                "An account already exists with this "
                "email or mobile number."
            ),
        )

    now = now_utc()

    # Newest challenge wins.
    await db.execute(
        text(
            """
            UPDATE email_verification_challenges
            SET
                used_at = :now,
                updated_at = :now
            WHERE lower(email) = :email
              AND used_at IS NULL
            """
        ),
        {
            "email": email,
            "now": now,
        },
    )

    code = create_code()

    await db.execute(
        text(
            """
            INSERT INTO email_verification_challenges (
                id,
                email,
                full_name,
                phone,
                gender,
                password_hash,
                profile_image_url,
                code_hash,
                attempt_count,
                expires_at,
                resend_available_at,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :email,
                :full_name,
                :phone,
                :gender,
                :password_hash,
                :profile_image_url,
                :code_hash,
                0,
                :expires_at,
                :resend_available_at,
                :now,
                :now
            )
            """
        ),
        {
            "id": uuid4(),
            "email": email,
            "full_name": (
                payload.full_name.strip()
            ),
            "phone": phone,
            "gender": gender,
            "password_hash": (
                hash_password(
                    payload.password
                )
            ),
            "profile_image_url": (
                payload.profile_image_url
            ),
            "code_hash": hash_code(
                email,
                code,
            ),
            "expires_at": (
                now
                +
                timedelta(
                    seconds=OTP_TTL_SECONDS
                )
            ),
            "resend_available_at": (
                now
                +
                timedelta(
                    seconds=OTP_RESEND_SECONDS
                )
            ),
            "now": now,
        },
    )

    try:
        await send_verification_code(
            email,
            code,
        )

    except EmailDeliveryNotConfigured:
        await db.rollback()

        raise HTTPException(
            status_code=503,
            detail=(
                "Verification email delivery is not "
                "configured."
            ),
        )

    except Exception:
        await db.rollback()

        raise HTTPException(
            status_code=502,
            detail=(
                "The verification email could not be sent."
            ),
        )

    await db.commit()

    return {
        "verification_required":
            True,

        "email":
            email,

        "expires_in_seconds":
            OTP_TTL_SECONDS,

        "resend_after_seconds":
            OTP_RESEND_SECONDS,
    }


@router.post(
    "/verify",
)
async def verify_signup(
    payload: VerifySignupRequest,
    db: AsyncSession = Depends(
        get_db
    ),
):
    email = normalize_email(
        str(payload.email)
    )

    result = await db.execute(
        text(
            """
            SELECT *
            FROM email_verification_challenges
            WHERE lower(email) = :email
              AND used_at IS NULL
            ORDER BY created_at DESC
            LIMIT 1
            FOR UPDATE
            """
        ),
        {
            "email": email,
        },
    )

    challenge = (
        result.mappings().first()
    )

    if not challenge:
        raise HTTPException(
            status_code=404,
            detail=(
                "No pending registration was found."
            ),
        )

    now = now_utc()

    if (
        challenge["attempt_count"]
        >=
        OTP_MAX_ATTEMPTS
    ):
        raise HTTPException(
            status_code=429,
            detail=(
                "Too many incorrect verification attempts. "
                "Request a new code."
            ),
        )

    if (
        challenge["expires_at"]
        <=
        now
    ):
        raise HTTPException(
            status_code=410,
            detail=(
                "This verification code has expired."
            ),
        )

    actual_hash = hash_code(
        email,
        payload.code,
    )

    if not hmac.compare_digest(
        actual_hash,
        challenge["code_hash"],
    ):
        await db.execute(
            text(
                """
                UPDATE email_verification_challenges
                SET
                    attempt_count =
                        attempt_count + 1,
                    updated_at = :now
                WHERE id = :id
                """
            ),
            {
                "id":
                    challenge["id"],

                "now":
                    now,
            },
        )

        await db.commit()

        raise HTTPException(
            status_code=400,
            detail=(
                "The verification code is incorrect."
            ),
        )

    conflict = await find_conflict(
        db,
        email,
        challenge["phone"],
    )

    if conflict:
        raise HTTPException(
            status_code=409,
            detail=(
                "An account already exists with these "
                "identity details."
            ),
        )

    # Preserve MediBook's existing architecture:
    # users.id and patients.id are separate UUIDs.
    # Their shared phone maps account identity to patient.
    user_id = uuid4()
    patient_id = uuid4()

    await db.execute(
        text(
            """
            INSERT INTO users (
                id,
                email,
                password_hash,
                full_name,
                phone,
                role,
                gender,
                profile_image_url,
                email_verified_at,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :email,
                :password_hash,
                :full_name,
                :phone,
                'patient',
                :gender,
                :profile_image_url,
                :now,
                :now,
                :now
            )
            """
        ),
        {
            "id":
                user_id,

            "email":
                email,

            "password_hash":
                challenge[
                    "password_hash"
                ],

            "full_name":
                challenge[
                    "full_name"
                ],

            "phone":
                challenge[
                    "phone"
                ],

            "gender":
                challenge[
                    "gender"
                ],

            "profile_image_url":
                challenge[
                    "profile_image_url"
                ],

            "now":
                now,
        },
    )

    await db.execute(
        text(
            """
            INSERT INTO patients (
                id,
                full_name,
                phone,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :full_name,
                :phone,
                :now,
                :now
            )
            """
        ),
        {
            "id":
                patient_id,

            "full_name":
                challenge[
                    "full_name"
                ],

            "phone":
                challenge[
                    "phone"
                ],

            "now":
                now,
        },
    )

    await db.execute(
        text(
            """
            UPDATE email_verification_challenges
            SET
                used_at = :now,
                updated_at = :now
            WHERE id = :id
            """
        ),
        {
            "id":
                challenge["id"],

            "now":
                now,
        },
    )

    await db.commit()

    return {
        "verified":
            True,

        "account_created":
            True,

        "email":
            email,
    }


@router.post(
    "/resend",
)
async def resend_signup(
    payload: ResendSignupRequest,
    db: AsyncSession = Depends(
        get_db
    ),
):
    email = normalize_email(
        str(payload.email)
    )

    result = await db.execute(
        text(
            """
            SELECT *
            FROM email_verification_challenges
            WHERE lower(email) = :email
              AND used_at IS NULL
            ORDER BY created_at DESC
            LIMIT 1
            FOR UPDATE
            """
        ),
        {
            "email":
                email,
        },
    )

    challenge = (
        result.mappings().first()
    )

    if not challenge:
        raise HTTPException(
            status_code=404,
            detail=(
                "No pending registration was found."
            ),
        )

    now = now_utc()

    if (
        challenge[
            "resend_available_at"
        ]
        >
        now
    ):
        remaining = int(
            (
                challenge[
                    "resend_available_at"
                ]
                -
                now
            ).total_seconds()
        )

        raise HTTPException(
            status_code=429,
            detail=(
                f"Please wait {max(remaining, 1)} seconds "
                "before requesting another code."
            ),
        )

    code = create_code()

    await db.execute(
        text(
            """
            UPDATE email_verification_challenges
            SET
                code_hash = :code_hash,
                attempt_count = 0,
                expires_at = :expires_at,
                resend_available_at =
                    :resend_available_at,
                updated_at = :now
            WHERE id = :id
            """
        ),
        {
            "id":
                challenge["id"],

            "code_hash":
                hash_code(
                    email,
                    code,
                ),

            "expires_at":
                now
                +
                timedelta(
                    seconds=OTP_TTL_SECONDS
                ),

            "resend_available_at":
                now
                +
                timedelta(
                    seconds=OTP_RESEND_SECONDS
                ),

            "now":
                now,
        },
    )

    try:
        await send_verification_code(
            email,
            code,
        )

    except EmailDeliveryNotConfigured:
        await db.rollback()

        raise HTTPException(
            status_code=503,
            detail=(
                "Verification email delivery is not "
                "configured."
            ),
        )

    except Exception:
        await db.rollback()

        raise HTTPException(
            status_code=502,
            detail=(
                "The verification email could not be sent."
            ),
        )

    await db.commit()

    return {
        "sent":
            True,

        "expires_in_seconds":
            OTP_TTL_SECONDS,

        "resend_after_seconds":
            OTP_RESEND_SECONDS,
    }
