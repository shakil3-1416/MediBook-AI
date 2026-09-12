from __future__ import annotations

import os
import secrets
import shutil
from pathlib import Path
from typing import Any
from uuid import UUID

from app.services.profile_image_storage import (
    StoredProfileImage,
    UnsupportedProfileStorage,
    validate_profile_image,
)


class S3ProfileImageStorage:
    def __init__(self, client: Any | None = None) -> None:
        self.bucket = os.getenv("MEDIBOOK_S3_BUCKET", "").strip()

        if not self.bucket:
            raise UnsupportedProfileStorage(
                "MEDIBOOK_S3_BUCKET is required."
            )

        self.prefix = os.getenv(
            "MEDIBOOK_S3_PREFIX",
            "profile-images",
        ).strip("/")

        self.cache_root = Path(
            os.getenv(
                "MEDIBOOK_PROFILE_STORAGE_ROOT",
                "var/profile-images",
            )
        ).expanduser().resolve()

        self.cache_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        if client is not None:
            self.client = client
            return

        try:
            import boto3
        except ImportError as exc:
            raise UnsupportedProfileStorage(
                "S3 profile storage requires boto3."
            ) from exc

        kwargs: dict[str, Any] = {}

        region = os.getenv(
            "MEDIBOOK_S3_REGION",
            "",
        ).strip()

        endpoint = os.getenv(
            "MEDIBOOK_S3_ENDPOINT_URL",
            "",
        ).strip()

        access_key = os.getenv(
            "MEDIBOOK_S3_ACCESS_KEY_ID",
            "",
        ).strip()

        secret_key = os.getenv(
            "MEDIBOOK_S3_SECRET_ACCESS_KEY",
            "",
        ).strip()

        session_token = os.getenv(
            "MEDIBOOK_S3_SESSION_TOKEN",
            "",
        ).strip()

        if region:
            kwargs["region_name"] = region

        if endpoint:
            kwargs["endpoint_url"] = endpoint

        if access_key:
            kwargs["aws_access_key_id"] = access_key

        if secret_key:
            kwargs["aws_secret_access_key"] = secret_key

        if session_token:
            kwargs["aws_session_token"] = session_token

        self.client = boto3.client(
            "s3",
            **kwargs,
        )

    def _key(
        self,
        *,
        user_id: UUID,
        filename: str,
    ) -> str:
        relative = f"{user_id}/{filename}"

        if self.prefix:
            return f"{self.prefix}/{relative}"

        return relative

    def _cache_path(
        self,
        *,
        user_id: UUID,
        filename: str,
    ) -> Path:
        if filename != Path(filename).name:
            raise FileNotFoundError

        if not all(
            character.isalnum()
            or character in {".", "-", "_"}
            for character in filename
        ):
            raise FileNotFoundError

        directory = (
            self.cache_root
            / str(user_id)
        ).resolve()

        candidate = (
            directory
            / filename
        ).resolve()

        if candidate.parent != directory:
            raise FileNotFoundError

        return candidate

    def store(
        self,
        *,
        user_id: UUID,
        data: bytes,
        media_type: str,
    ) -> StoredProfileImage:
        extension = validate_profile_image(
            data,
            media_type,
        )

        filename = (
            secrets.token_hex(20)
            + extension
        )

        self.client.put_object(
            Bucket=self.bucket,
            Key=self._key(
                user_id=user_id,
                filename=filename,
            ),
            Body=data,
            ContentType=media_type,
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
        destination = self._cache_path(
            user_id=user_id,
            filename=filename,
        )

        if destination.is_file():
            return destination

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = destination.with_name(
            f".{destination.name}.tmp"
        )

        try:
            self.client.download_file(
                self.bucket,
                self._key(
                    user_id=user_id,
                    filename=filename,
                ),
                str(temporary),
            )

            temporary.replace(
                destination
            )

        except Exception as exc:
            temporary.unlink(
                missing_ok=True
            )

            raise FileNotFoundError from exc

        return destination

    def remove_user_images(
        self,
        *,
        user_id: UUID,
    ) -> None:
        prefix = self._key(
            user_id=user_id,
            filename="",
        )

        continuation: str | None = None

        while True:
            kwargs: dict[str, Any] = {
                "Bucket": self.bucket,
                "Prefix": prefix,
            }

            if continuation:
                kwargs[
                    "ContinuationToken"
                ] = continuation

            response = (
                self.client.list_objects_v2(
                    **kwargs
                )
            )

            objects = response.get(
                "Contents",
                [],
            )

            if objects:
                self.client.delete_objects(
                    Bucket=self.bucket,
                    Delete={
                        "Objects": [
                            {
                                "Key":
                                    item["Key"]
                            }
                            for item
                            in objects
                        ]
                    },
                )

            if not response.get(
                "IsTruncated"
            ):
                break

            continuation = response.get(
                "NextContinuationToken"
            )

            if not continuation:
                break

        cache_directory = (
            self.cache_root
            / str(user_id)
        )

        if cache_directory.exists():
            shutil.rmtree(
                cache_directory,
                ignore_errors=True,
            )
