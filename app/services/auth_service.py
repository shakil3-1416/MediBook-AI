from sqlalchemy import (
    or_,
    select,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)

from app.models.user import (
    User,
)

from app.schemas.auth import (
    AuthResponse,
    AuthUserResponse,
    LoginRequest,
    SignupRequest,
)


class EmailAlreadyExistsError(
    Exception
):
    pass


class PhoneAlreadyExistsError(
    Exception
):
    pass


class InvalidCredentialsError(
    Exception
):
    pass


class AuthService:

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:

        self.session = session


    @staticmethod
    def serialize_user(
        user: User,
    ) -> AuthUserResponse:

        return AuthUserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role,
        )


    async def signup(
        self,
        payload: SignupRequest,
    ) -> AuthResponse:

        email = (
            str(payload.email)
            .strip()
            .lower()
        )

        existing = (
            await self.session.scalar(
                select(User)
                .where(
                    or_(
                        User.email
                        == email,

                        User.phone
                        == payload.phone,
                    )
                )
            )
        )

        if existing:

            if (
                existing.email
                == email
            ):
                raise (
                    EmailAlreadyExistsError()
                )

            raise (
                PhoneAlreadyExistsError()
            )

        user = User(
            full_name=(
                payload.full_name
            ),

            email=email,

            phone=(
                payload.phone
            ),

            password_hash=(
                hash_password(
                    payload.password
                )
            ),

            role="patient",
        )

        self.session.add(
            user
        )

        await self.session.commit()

        await self.session.refresh(
            user
        )

        token = (
            create_access_token(
                user_id=user.id,
                role=user.role,
            )
        )

        return AuthResponse(
            access_token=token,

            user=(
                self.serialize_user(
                    user
                )
            ),
        )


    async def login(
        self,
        payload: LoginRequest,
    ) -> AuthResponse:

        email = (
            str(payload.email)
            .strip()
            .lower()
        )

        user = (
            await self.session.scalar(
                select(User)
                .where(
                    User.email
                    == email
                )
            )
        )

        if (
            user is None
            or not verify_password(
                payload.password,
                user.password_hash,
            )
        ):
            raise (
                InvalidCredentialsError()
            )

        token = (
            create_access_token(
                user_id=user.id,
                role=user.role,
            )
        )

        return AuthResponse(
            access_token=token,

            user=(
                self.serialize_user(
                    user
                )
            ),
        )

# MEDIBOOK_IDENTITY_V2_PASSWORD_ADAPTER
def hash_identity_password(
    password: str,
) -> str:
    return hash_password(
        password
    )


IDENTITY_PASSWORD_FIELD = 'password_hash'

