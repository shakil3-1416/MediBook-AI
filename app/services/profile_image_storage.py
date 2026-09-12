from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import secrets
import shutil
from uuid import UUID


MAX_PROFILE_IMAGE_BYTES = int(
    os.getenv(
        "MEDIBOOK_PROFILE_MAX_BYTES",
        str(
            5
            * 1024
            * 1024
        ),
    )
)


MEDIA_EXTENSIONS = {
    "image/png":
        ".png",

    "image/jpeg":
        ".jpg",

    "image/webp":
        ".webp",
}


class InvalidProfileImage(
    ValueError
):
    pass


class UnsupportedProfileStorage(
    RuntimeError
):
    pass


def validate_profile_image(
    data: bytes,
    media_type: str,
) -> str:

    media_type = (
        media_type
        .split(
            ";",
            1,
        )[0]
        .strip()
        .lower()
    )

    extension = (
        MEDIA_EXTENSIONS.get(
            media_type
        )
    )

    if extension is None:
        raise InvalidProfileImage(
            "Profile image must be PNG, JPEG, or WebP."
        )

    if not data:
        raise InvalidProfileImage(
            "Profile image is empty."
        )

    if (
        len(
            data
        )
        >
        MAX_PROFILE_IMAGE_BYTES
    ):
        raise InvalidProfileImage(
            "Profile image is too large."
        )

    if media_type == "image/png":
        if not data.startswith(
            b"\x89PNG\r\n\x1a\n"
        ):
            raise InvalidProfileImage(
                "Invalid PNG image."
            )

    elif media_type == "image/jpeg":
        if not data.startswith(
            b"\xff\xd8\xff"
        ):
            raise InvalidProfileImage(
                "Invalid JPEG image."
            )

    elif media_type == "image/webp":
        if not (
            len(
                data
            )
            >= 12
            and
            data[:4]
            ==
            b"RIFF"
            and
            data[8:12]
            ==
            b"WEBP"
        ):
            raise InvalidProfileImage(
                "Invalid WebP image."
            )

    return extension


@dataclass(
    frozen=True
)
class StoredProfileImage:
    filename: str
    media_type: str


class LocalProfileImageStorage:

    def __init__(
        self,
    ) -> None:

        root = os.getenv(
            "MEDIBOOK_PROFILE_STORAGE_ROOT",
            "var/profile-images",
        )

        self.root = (
            Path(
                root
            )
            .expanduser()
            .resolve()
        )

        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

    def store(
        self,
        *,
        user_id: UUID,
        data: bytes,
        media_type: str,
    ) -> StoredProfileImage:

        extension = (
            validate_profile_image(
                data,
                media_type,
            )
        )

        directory = (
            self.root
            /
            str(
                user_id
            )
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        filename = (
            secrets.token_hex(
                20
            )
            +
            extension
        )

        destination = (
            directory
            /
            filename
        )

        temporary = (
            directory
            /
            (
                "."
                +
                filename
                +
                ".tmp"
            )
        )

        temporary.write_bytes(
            data
        )

        temporary.replace(
            destination
        )

        return StoredProfileImage(
            filename=filename,
            media_type=media_type,
        )

    def resolve(
        self,
        *,
        user_id: UUID,
        filename: str,
    ) -> Path:

        if (
            filename
            !=
            Path(
                filename
            ).name
        ):
            raise FileNotFoundError

        if not all(
            character.isalnum()
            or
            character
            in {
                ".",
                "-",
                "_",
            }
            for character
            in filename
        ):
            raise FileNotFoundError

        directory = (
            self.root
            /
            str(
                user_id
            )
        ).resolve()

        candidate = (
            directory
            /
            filename
        ).resolve()

        if (
            candidate.parent
            !=
            directory
        ):
            raise FileNotFoundError

        if not candidate.is_file():
            raise FileNotFoundError

        return candidate

    def remove_user_images(
        self,
        *,
        user_id: UUID,
    ) -> None:

        directory = (
            self.root
            /
            str(
                user_id
            )
        )

        if directory.exists():
            shutil.rmtree(
                directory,
                ignore_errors=True,
            )


def profile_image_storage():
    provider = os.getenv(
        "MEDIBOOK_PROFILE_STORAGE",
        "local",
    ).strip().lower()

    if provider == "local":
        return LocalProfileImageStorage()

    if provider in {
        "s3",
        "aws-s3",
        "aws_s3",
        "r2",
        "minio",
    }:
        from app.services.s3_profile_image_storage import (
            S3ProfileImageStorage,
        )

        return S3ProfileImageStorage()

    raise UnsupportedProfileStorage(
        "Unsupported profile storage provider."
    )
