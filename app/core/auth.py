from typing import (
    Annotated,
)

from uuid import UUID

from fastapi import (
    Depends,
    HTTPException,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.core.database import (
    AsyncSessionFactory,
)

from app.core.security import (
    InvalidTokenError,
    decode_access_token,
)

from app.models.user import (
    User,
)


bearer = HTTPBearer(
    auto_error=False
)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials
        | None,
        Depends(bearer),
    ],
) -> User:

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Authentication required."
            ),
        )

    try:
        payload = (
            decode_access_token(
                credentials.credentials
            )
        )

        user_id = UUID(
            payload["sub"]
        )

    except (
        InvalidTokenError,
        ValueError,
        KeyError,
    ) as exc:

        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid or expired session."
            ),
        ) from exc

    async with (
        AsyncSessionFactory()
        as session
    ):

        user = await session.get(
            User,
            user_id,
        )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Account no longer exists."
            ),
        )

    return user


CurrentUser = Annotated[
    User,
    Depends(
        get_current_user
    ),
]
