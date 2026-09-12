from __future__ import annotations

from datetime import (
    timedelta,
)
import hmac
from pathlib import Path
import re
from typing import Any
from uuid import (
    UUID,
    uuid4,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)

from fastapi.responses import (
    FileResponse,
)

from pydantic import (
    BaseModel,
)

from sqlalchemy import (
    select,
    text,
)

from app.core.database import (
    AsyncSessionFactory,
)

from app.models import (
    Patient,
    User,
)

from app.api.v1.auth_verification import (
    create_code,
    hash_code,
    normalize_email,
    normalize_gender,
    normalize_phone,
    now_utc,
)

from app.services.auth_service import (
    IDENTITY_PASSWORD_FIELD,
    hash_identity_password,
)

from app.services.profile_image_storage import (
    InvalidProfileImage,
    profile_image_storage,
)

from app.services.verification_email_service import (
    EmailDeliveryNotConfigured,
    send_verification_code,
)

from app.core.auth import get_current_user


router = APIRouter(
    prefix="/identity",
    tags=["identity"],
)


CHALLENGE_SECONDS = 600
RESEND_SECONDS = 60
MAX_ATTEMPTS = 5

# MEDIBOOK_IDENTITY_HASH_ADAPTER
def _identity_hash_code(
    email: str,
    code: str,
) -> str:
    return hash_code(
        email,
        code,
    )



class ProfileUpdateRequest(
    BaseModel
):
    full_name: str | None = None
    phone: str | None = None
    gender: str | None = None


class PasswordResetStartRequest(
    BaseModel
):
    email: str


class PasswordResetVerifyRequest(
    BaseModel
):
    email: str
    code: str
    new_password: str


class PasswordResetResendRequest(
    BaseModel
):
    email: str


class EmailChangeStartRequest(
    BaseModel
):
    new_email: str


class EmailChangeVerifyRequest(
    BaseModel
):
    new_email: str
    code: str


class EmailChangeResendRequest(
    BaseModel
):
    new_email: str


def _user_id(
    current_user: Any,
) -> UUID:

    value = getattr(
        current_user,
        "id",
        None,
    )

    if value is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    try:
        return UUID(
            str(
                value
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid authenticated user.",
        ) from exc


def _role_value(
    value: Any,
) -> str:

    if hasattr(
        value,
        "value",
    ):
        return str(
            value.value
        )

    return str(
        value
    )


def _serialize_user(
    user: User,
) -> dict[str, Any]:

    return {
        "id":
            str(
                user.id
            ),

        "email":
            user.email,

        "full_name":
            user.full_name,

        "phone":
            user.phone,

        "role":
            _role_value(
                user.role
            ),

        "gender":
            getattr(
                user,
                "gender",
                None,
            ),

        "profile_image_url":
            getattr(
                user,
                "profile_image_url",
                None,
            ),

        "email_verified_at":
            (
                user.email_verified_at.isoformat()
                if getattr(
                    user,
                    "email_verified_at",
                    None,
                )
                else None
            ),
    }


def _validate_password(
    password: str,
) -> str:

    if (
        len(
            password
        )
        <
        8
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Password must contain "
                "at least 8 characters."
            ),
        )

    if (
        len(
            password
        )
        >
        128
    ):
        raise HTTPException(
            status_code=400,
            detail="Password is too long.",
        )

    return password


def _validate_code(
    code: str,
) -> str:

    code = code.strip()

    if not re.fullmatch(
        r"\d{6}",
        code,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Verification code must "
                "contain six digits."
            ),
        )

    return code


async def _load_user(
    session,
    current_user: Any,
) -> User:

    user = await session.get(
        User,
        _user_id(
            current_user
        ),
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user not found.",
        )

    identity_profile = await session.execute(
        text(
            """
            SELECT
                gender,
                profile_image_url,
                email_verified_at
            FROM users
            WHERE id = :user_id
            """
        ),
        {
            "user_id":
                user.id,
        },
    )

    identity_row = (
        identity_profile
        .mappings()
        .first()
    )

    if identity_row is not None:
        setattr(
            user,
            "gender",
            identity_row[
                "gender"
            ],
        )

        setattr(
            user,
            "profile_image_url",
            identity_row[
                "profile_image_url"
            ],
        )

        setattr(
            user,
            "email_verified_at",
            identity_row[
                "email_verified_at"
            ],
        )

    return user


async def _find_active_challenge(
    session,
    *,
    purpose: str,
    user_id: UUID,
    email: str,
    lock: bool = False,
):

    lock_sql = (
        " FOR UPDATE"
        if lock
        else
        ""
    )

    result = await session.execute(
        text(
            """
            SELECT
                id,
                purpose,
                user_id,
                email,
                code_hash,
                attempt_count,
                expires_at,
                resend_available_at,
                consumed_at
            FROM identity_verification_challenges
            WHERE
                purpose = :purpose
                AND user_id = :user_id
                AND email = :email
                AND consumed_at IS NULL
            ORDER BY created_at DESC
            LIMIT 1
            """
            +
            lock_sql
        ),
        {
            "purpose":
                purpose,

            "user_id":
                user_id,

            "email":
                email,
        },
    )

    return (
        result
        .mappings()
        .first()
    )


async def _issue_challenge(
    session,
    *,
    purpose: str,
    user_id: UUID,
    email: str,
) -> None:

    challenge_id = (
        uuid4()
    )

    code = (
        create_code()
    )

    now = now_utc()

    await session.execute(
        text(
            """
            DELETE FROM identity_verification_challenges
            WHERE
                purpose = :purpose
                AND user_id = :user_id
                AND consumed_at IS NULL
            """
        ),
        {
            "purpose":
                purpose,

            "user_id":
                user_id,
        },
    )

    await session.execute(
        text(
            """
            INSERT INTO identity_verification_challenges (
                id,
                purpose,
                user_id,
                email,
                code_hash,
                attempt_count,
                expires_at,
                resend_available_at,
                created_at,
                consumed_at
            )
            VALUES (
                :id,
                :purpose,
                :user_id,
                :email,
                :code_hash,
                0,
                :expires_at,
                :resend_available_at,
                :created_at,
                NULL
            )
            """
        ),
        {
            "id":
                challenge_id,

            "purpose":
                purpose,

            "user_id":
                user_id,

            "email":
                email,

            "code_hash":
                _identity_hash_code(
                    email,
                    code,
                ),

            "expires_at":
                (
                    now
                    +
                    timedelta(
                        seconds=(
                            CHALLENGE_SECONDS
                        )
                    )
                ),

            "resend_available_at":
                (
                    now
                    +
                    timedelta(
                        seconds=(
                            RESEND_SECONDS
                        )
                    )
                ),

            "created_at":
                now,
        },
    )

    await session.commit()

    try:
        await send_verification_code(
            email,
            code,
            purpose=purpose,
        )

    except EmailDeliveryNotConfigured as exc:

        await session.execute(
            text(
                """
                DELETE FROM identity_verification_challenges
                WHERE id = :id
                """
            ),
            {
                "id":
                    challenge_id,
            },
        )

        await session.commit()

        raise HTTPException(
            status_code=503,
            detail=(
                "Verification email "
                "could not be sent."
            ),
        ) from exc


async def _verify_challenge(
    session,
    *,
    purpose: str,
    user_id: UUID,
    email: str,
    code: str,
):

    code = _validate_code(
        code
    )

    challenge = (
        await _find_active_challenge(
            session,
            purpose=purpose,
            user_id=user_id,
            email=email,
            lock=True,
        )
    )

    if challenge is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Verification challenge "
                "was not found."
            ),
        )

    now = now_utc()

    if (
        challenge[
            "attempt_count"
        ]
        >=
        MAX_ATTEMPTS
    ):
        raise HTTPException(
            status_code=429,
            detail=(
                "Too many incorrect "
                "verification attempts."
            ),
        )

    if (
        challenge[
            "expires_at"
        ]
        <=
        now
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "This verification "
                "code has expired."
            ),
        )

    valid = hmac.compare_digest(
        challenge[
            "code_hash"
        ],
        _identity_hash_code(
                    email,
                    code,
                ),
    )

    if not valid:

        await session.execute(
            text(
                """
                UPDATE identity_verification_challenges
                SET attempt_count =
                    attempt_count + 1
                WHERE id = :id
                """
            ),
            {
                "id":
                    challenge[
                        "id"
                    ],
            },
        )

        await session.commit()

        raise HTTPException(
            status_code=400,
            detail=(
                "The verification code "
                "is incorrect."
            ),
        )

    return challenge


async def _consume_challenge(
    session,
    challenge_id: UUID,
) -> None:

    await session.execute(
        text(
            """
            UPDATE identity_verification_challenges
            SET consumed_at = :consumed_at
            WHERE id = :id
            """
        ),
        {
            "id":
                challenge_id,

            "consumed_at":
                now_utc(),
        },
    )


async def _cooldown_active(
    session,
    *,
    purpose: str,
    user_id: UUID,
    email: str,
) -> bool:

    challenge = (
        await _find_active_challenge(
            session,
            purpose=purpose,
            user_id=user_id,
            email=email,
        )
    )

    if challenge is None:
        return False

    return (
        challenge[
            "resend_available_at"
        ]
        >
        now_utc()
    )


@router.get(
    "/profile"
)
async def get_profile(
    current_user=Depends(
        get_current_user
    ),
):

    async with AsyncSessionFactory() as session:

        user = await _load_user(
            session,
            current_user,
        )

        return _serialize_user(
            user
        )


@router.patch(
    "/profile"
)
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user=Depends(
        get_current_user
    ),
):

    async with AsyncSessionFactory() as session:

        user = await _load_user(
            session,
            current_user,
        )

        old_phone = (
            user.phone
        )

        patient = await session.scalar(
            select(
                Patient
            ).where(
                Patient.phone
                ==
                old_phone
            )
        )

        if (
            payload.full_name
            is not None
        ):
            full_name = (
                payload.full_name
                .strip()
            )

            if (
                len(
                    full_name
                )
                <
                2
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Full name is invalid."
                    ),
                )

            user.full_name = (
                full_name
            )

            if patient is not None:
                patient.full_name = (
                    full_name
                )

        if (
            payload.phone
            is not None
        ):
            phone = normalize_phone(
                payload.phone
            )

            existing_user = await session.scalar(
                select(
                    User
                ).where(
                    User.phone
                    ==
                    phone,

                    User.id
                    !=
                    user.id,
                )
            )

            if existing_user is not None:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Phone number is "
                        "already in use."
                    ),
                )

            if patient is not None:
                existing_patient = (
                    await session.scalar(
                        select(
                            Patient
                        ).where(
                            Patient.phone
                            ==
                            phone,

                            Patient.id
                            !=
                            patient.id,
                        )
                    )
                )

                if (
                    existing_patient
                    is not None
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Phone number is "
                            "already in use."
                        ),
                    )

            user.phone = (
                phone
            )

            if patient is not None:
                patient.phone = (
                    phone
                )

        if (
            payload.gender
            is not None
        ):
            gender = normalize_gender(
                payload.gender
            )

            await session.execute(
                text(
                    """
                    UPDATE users
                    SET gender = :gender
                    WHERE id = :user_id
                    """
                ),
                {
                    "gender":
                        gender,

                    "user_id":
                        user.id,
                },
            )

            setattr(
                user,
                "gender",
                gender,
            )

        await session.commit()

        await session.refresh(
            user
        )

        refreshed_profile = await session.execute(
            text(
                """
                SELECT
                    gender,
                    profile_image_url,
                    email_verified_at
                FROM users
                WHERE id = :user_id
                """
            ),
            {
                "user_id":
                    user.id,
            },
        )

        refreshed_row = (
            refreshed_profile
            .mappings()
            .first()
        )

        if refreshed_row is not None:
            setattr(
                user,
                "gender",
                refreshed_row[
                    "gender"
                ],
            )

            setattr(
                user,
                "profile_image_url",
                refreshed_row[
                    "profile_image_url"
                ],
            )

            setattr(
                user,
                "email_verified_at",
                refreshed_row[
                    "email_verified_at"
                ],
            )

        return _serialize_user(
            user
        )


@router.post(
    "/profile/image"
)
async def upload_profile_image(
    request: Request,
    current_user=Depends(
        get_current_user
    ),
):

    content_length = (
        request.headers.get(
            "content-length"
        )
    )

    if content_length:
        try:
            if (
                int(
                    content_length
                )
                >
                (
                    5
                    * 1024
                    * 1024
                )
            ):
                raise HTTPException(
                    status_code=413,
                    detail=(
                        "Profile image "
                        "is too large."
                    ),
                )
        except ValueError:
            pass

    data = await request.body()

    media_type = (
        request.headers.get(
            "content-type",
            "",
        )
    )

    async with AsyncSessionFactory() as session:

        user = await _load_user(
            session,
            current_user,
        )

        storage = (
            profile_image_storage()
        )

        try:
            stored = storage.store(
                user_id=user.id,
                data=data,
                media_type=media_type,
            )

        except InvalidProfileImage as exc:
            raise HTTPException(
                status_code=400,
                detail=str(
                    exc
                ),
            ) from exc

        url = (
            "/api/auth/profile-image/"
            +
            str(
                user.id
            )
            +
            "/"
            +
            stored.filename
        )

        setattr(
            user,
            "profile_image_url",
            url,
        )

        await session.execute(
            text(
                """
                UPDATE users
                SET profile_image_url = :url
                WHERE id = :user_id
                """
            ),
            {
                "url":
                    url,

                "user_id":
                    user.id,
            },
        )

        await session.commit()

        return {
            "profile_image_url":
                url,
        }


@router.get(
    "/profile/image/{user_id}/{filename}"
)
async def read_profile_image(
    user_id: UUID,
    filename: str,
    current_user=Depends(
        get_current_user
    ),
):

    authenticated_id = (
        _user_id(
            current_user
        )
    )

    if (
        authenticated_id
        !=
        user_id
    ):
        raise HTTPException(
            status_code=404,
            detail="Image not found.",
        )

    storage = (
        profile_image_storage()
    )

    try:
        path = storage.resolve(
            user_id=user_id,
            filename=filename,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Image not found.",
        ) from exc

    suffix = (
        path.suffix.lower()
    )

    media_type = {
        ".png":
            "image/png",

        ".jpg":
            "image/jpeg",

        ".jpeg":
            "image/jpeg",

        ".webp":
            "image/webp",
    }.get(
        suffix,
        "application/octet-stream",
    )

    return FileResponse(
        path,
        media_type=media_type,
        headers={
            "Cache-Control":
                "private, max-age=3600",
        },
    )


async def _start_password_reset(
    email: str,
) -> None:

    email = normalize_email(
        email
    )

    async with AsyncSessionFactory() as session:

        user = await session.scalar(
            select(
                User
            ).where(
                User.email
                ==
                email
            )
        )

        # Deliberately do not disclose
        # whether the account exists.
        if user is None:
            return

        verified_at = await session.scalar(
            text(
                """
                SELECT email_verified_at
                FROM users
                WHERE id = :user_id
                """
            ),
            {
                "user_id":
                    user.id,
            },
        )

        if verified_at is None:
            return

        if await _cooldown_active(
            session,
            purpose="password_reset",
            user_id=user.id,
            email=email,
        ):
            return

        await _issue_challenge(
            session,
            purpose="password_reset",
            user_id=user.id,
            email=email,
        )


@router.post(
    "/password/reset/start",
    status_code=status.HTTP_202_ACCEPTED,
)
async def password_reset_start(
    payload: PasswordResetStartRequest,
):

    await _start_password_reset(
        payload.email
    )

    return {
        "accepted":
            True,

        "expires_in_seconds":
            CHALLENGE_SECONDS,

        "resend_after_seconds":
            RESEND_SECONDS,
    }


@router.post(
    "/password/reset/resend",
    status_code=status.HTTP_202_ACCEPTED,
)
async def password_reset_resend(
    payload: PasswordResetResendRequest,
):

    await _start_password_reset(
        payload.email
    )

    return {
        "accepted":
            True,

        "expires_in_seconds":
            CHALLENGE_SECONDS,

        "resend_after_seconds":
            RESEND_SECONDS,
    }


@router.post(
    "/password/reset/verify"
)
async def password_reset_verify(
    payload: PasswordResetVerifyRequest,
):

    email = normalize_email(
        payload.email
    )

    password = _validate_password(
        payload.new_password
    )

    async with AsyncSessionFactory() as session:

        user = await session.scalar(
            select(
                User
            ).where(
                User.email
                ==
                email
            )
        )

        if user is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Verification challenge "
                    "was not found."
                ),
            )

        challenge = (
            await _verify_challenge(
                session,
                purpose="password_reset",
                user_id=user.id,
                email=email,
                code=payload.code,
            )
        )

        setattr(
            user,
            IDENTITY_PASSWORD_FIELD,
            hash_identity_password(
                password
            ),
        )

        await _consume_challenge(
            session,
            challenge[
                "id"
            ],
        )

        await session.commit()

        return {
            "password_reset":
                True,
        }


async def _assert_email_available(
    session,
    *,
    email: str,
    user_id: UUID,
) -> None:

    conflict = await session.scalar(
        select(
            User
        ).where(
            User.email
            ==
            email,

            User.id
            !=
            user_id,
        )
    )

    if conflict is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Email address is "
                "already in use."
            ),
        )


@router.post(
    "/email/change/start",
    status_code=status.HTTP_202_ACCEPTED,
)
async def email_change_start(
    payload: EmailChangeStartRequest,
    current_user=Depends(
        get_current_user
    ),
):

    new_email = normalize_email(
        payload.new_email
    )

    async with AsyncSessionFactory() as session:

        user = await _load_user(
            session,
            current_user,
        )

        if (
            new_email
            ==
            user.email
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "This is already your "
                    "current email address."
                ),
            )

        await _assert_email_available(
            session,
            email=new_email,
            user_id=user.id,
        )

        if await _cooldown_active(
            session,
            purpose="email_change",
            user_id=user.id,
            email=new_email,
        ):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Please wait before "
                    "requesting another code."
                ),
            )

        await _issue_challenge(
            session,
            purpose="email_change",
            user_id=user.id,
            email=new_email,
        )

        return {
            "verification_required":
                True,

            "email":
                new_email,

            "expires_in_seconds":
                CHALLENGE_SECONDS,

            "resend_after_seconds":
                RESEND_SECONDS,
        }


@router.post(
    "/email/change/resend",
    status_code=status.HTTP_202_ACCEPTED,
)
async def email_change_resend(
    payload: EmailChangeResendRequest,
    current_user=Depends(
        get_current_user
    ),
):

    new_email = normalize_email(
        payload.new_email
    )

    async with AsyncSessionFactory() as session:

        user = await _load_user(
            session,
            current_user,
        )

        await _assert_email_available(
            session,
            email=new_email,
            user_id=user.id,
        )

        if await _cooldown_active(
            session,
            purpose="email_change",
            user_id=user.id,
            email=new_email,
        ):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Please wait before "
                    "requesting another code."
                ),
            )

        await _issue_challenge(
            session,
            purpose="email_change",
            user_id=user.id,
            email=new_email,
        )

        return {
            "verification_required":
                True,

            "email":
                new_email,

            "expires_in_seconds":
                CHALLENGE_SECONDS,

            "resend_after_seconds":
                RESEND_SECONDS,
        }


@router.post(
    "/email/change/verify"
)
async def email_change_verify(
    payload: EmailChangeVerifyRequest,
    current_user=Depends(
        get_current_user
    ),
):

    new_email = normalize_email(
        payload.new_email
    )

    async with AsyncSessionFactory() as session:

        user = await _load_user(
            session,
            current_user,
        )

        await _assert_email_available(
            session,
            email=new_email,
            user_id=user.id,
        )

        challenge = (
            await _verify_challenge(
                session,
                purpose="email_change",
                user_id=user.id,
                email=new_email,
                code=payload.code,
            )
        )

        user.email = (
            new_email
        )

        verified_at = (
            now_utc()
        )

        setattr(
            user,
            "email_verified_at",
            verified_at,
        )

        await session.execute(
            text(
                """
                UPDATE users
                SET
                    email = :email,
                    email_verified_at = :verified_at
                WHERE id = :user_id
                """
            ),
            {
                "email":
                    new_email,

                "verified_at":
                    verified_at,

                "user_id":
                    user.id,
            },
        )

        await _consume_challenge(
            session,
            challenge[
                "id"
            ],
        )

        await session.commit()

        await session.refresh(
            user
        )

        setattr(
            user,
            "email_verified_at",
            verified_at,
        )

        return {
            "verified":
                True,

            "user":
                _serialize_user(
                    user
                ),
        }
