import os

from pathlib import Path
from dotenv import load_dotenv

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from uuid import UUID

import jwt

from pwdlib import PasswordHash


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

load_dotenv(
    PROJECT_ROOT / ".env"
)


password_hash = (
    PasswordHash.recommended()
)


class InvalidTokenError(
    Exception
):
    pass


def _jwt_secret() -> str:

    value = os.getenv(
        "JWT_SECRET",
    )

    if not value:
        raise RuntimeError(
            "JWT_SECRET is not configured."
        )

    return value


def _jwt_algorithm() -> str:

    return os.getenv(
        "JWT_ALGORITHM",
        "HS256",
    )


def _jwt_minutes() -> int:

    return int(
        os.getenv(
            "JWT_ACCESS_MINUTES",
            "480",
        )
    )


def hash_password(
    password: str,
) -> str:

    return password_hash.hash(
        password
    )


def verify_password(
    password: str,
    hashed: str,
) -> bool:

    try:
        return (
            password_hash.verify(
                password,
                hashed,
            )
        )

    except Exception:
        return False


def create_access_token(
    *,
    user_id: UUID,
    role: str,
) -> str:

    now = datetime.now(
        timezone.utc
    )

    expires = (
        now
        + timedelta(
            minutes=_jwt_minutes()
        )
    )

    return jwt.encode(
        {
            "sub":
                str(user_id),

            "role":
                role,

            "type":
                "access",

            "iat":
                now,

            "exp":
                expires,
        },
        _jwt_secret(),
        algorithm=_jwt_algorithm(),
    )


def decode_access_token(
    token: str,
) -> dict:

    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=[
                _jwt_algorithm()
            ],
        )

    except jwt.PyJWTError as exc:

        raise InvalidTokenError(
            "Invalid or expired token."
        ) from exc

    if (
        payload.get("type")
        != "access"
    ):
        raise InvalidTokenError(
            "Invalid token type."
        )

    if not payload.get(
        "sub"
    ):
        raise InvalidTokenError(
            "Missing token subject."
        )

    return payload
