import re
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)


PHONE_RE = re.compile(
    r"^01[3-9]\d{8}$"
)


def normalize_phone(
    value: str,
) -> str:

    value = (
        value
        .replace(" ", "")
        .replace("-", "")
        .strip()
    )

    if value.startswith("+88"):
        value = value[3:]

    elif (
        value.startswith("88")
        and len(value) == 13
    ):
        value = value[2:]

    return value


class SignupRequest(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=200,
    )

    email: EmailStr

    phone: str

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("full_name")
    @classmethod
    def clean_name(
        cls,
        value: str,
    ) -> str:

        value = " ".join(
            value.split()
        )

        if len(value) < 2:
            raise ValueError(
                "Full name is required."
            )

        return value


    @field_validator("phone")
    @classmethod
    def validate_phone(
        cls,
        value: str,
    ) -> str:

        value = normalize_phone(
            value
        )

        if not PHONE_RE.fullmatch(
            value
        ):
            raise ValueError(
                "Use a valid Bangladesh mobile number."
            )

        return value


class LoginRequest(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=1,
        max_length=128,
    )


class AuthUserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    phone: str
    role: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse
