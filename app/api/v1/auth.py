from fastapi import (
    APIRouter,
    HTTPException,
)

from app.core.auth import (
    CurrentUser,
)

from app.core.database import (
    AsyncSessionFactory,
)

from app.schemas.auth import (
    AuthResponse,
    AuthUserResponse,
    LoginRequest,
    SignupRequest,
)

from app.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    PhoneAlreadyExistsError,
)


router = APIRouter()


@router.post("/signup")
async def legacy_signup_disabled():
    """
    Legacy direct patient account creation is disabled.

    New patient accounts must complete email verification
    through /auth/signup/start and /auth/signup/verify.
    """
    from fastapi import HTTPException

    raise HTTPException(
        status_code=410,
        detail=(
            "Direct signup has been retired. "
            "Use the verified registration flow."
        ),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
)
async def login(
    payload: LoginRequest,
) -> AuthResponse:

    async with (
        AsyncSessionFactory()
        as session
    ):

        service = AuthService(
            session
        )

        try:
            return await service.login(
                payload
            )

        except (
            InvalidCredentialsError
        ) as exc:

            raise HTTPException(
                status_code=401,
                detail=(
                    "Incorrect email or password."
                ),
            ) from exc


@router.get(
    "/me",
    response_model=AuthUserResponse,
)
async def me(
    user: CurrentUser,
) -> AuthUserResponse:

    return AuthUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
    )
