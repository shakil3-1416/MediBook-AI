from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any

from cryptography.fernet import (
    Fernet,
    InvalidToken,
)


MASTER_KEY_ENV = (
    "MEDIBOOK_INTEGRATION_MASTER_KEY"
)

ENVELOPE_MARKER = (
    "__medibook_encrypted__"
)

ENVELOPE_VERSION = 1


SENSITIVE_KEY_FRAGMENTS = {
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "token",
    "secret",
    "client_secret",
    "password",
    "private_key",
    "signing_key",
    "webhook_secret",
    "authorization",
    "credential",
}


REDACTED_VALUE = "••••••••"


class IntegrationSecretError(
    RuntimeError
):
    pass


class IntegrationMasterKeyMissing(
    IntegrationSecretError
):
    pass


class IntegrationSecretDecryptError(
    IntegrationSecretError
):
    pass


def _normalize_key_name(
    value: str,
) -> str:
    return (
        value
        .strip()
        .lower()
        .replace(
            "-",
            "_",
        )
        .replace(
            " ",
            "_",
        )
    )


def is_sensitive_key(
    key: str,
) -> bool:
    normalized = (
        _normalize_key_name(
            key
        )
    )

    if normalized in (
        SENSITIVE_KEY_FRAGMENTS
    ):
        return True

    return any(
        (
            normalized.endswith(
                f"_{fragment}"
            )
            or normalized.startswith(
                f"{fragment}_"
            )
        )
        for fragment
        in SENSITIVE_KEY_FRAGMENTS
    )


def _fernet_key_from_master(
    master: str,
) -> bytes:
    """
    Accept either:
      1. a native Fernet key, or
      2. an arbitrary high-entropy deployment secret.

    Arbitrary secrets are SHA-256 derived and URL-safe encoded.
    """

    encoded = master.encode(
        "utf-8"
    )

    try:
        Fernet(
            encoded
        )

        return encoded

    except Exception:
        digest = hashlib.sha256(
            encoded
        ).digest()

        return base64.urlsafe_b64encode(
            digest
        )


def _load_fernet() -> Fernet:
    master = (
        os.getenv(
            MASTER_KEY_ENV,
            "",
        )
        .strip()
    )

    if not master:
        raise IntegrationMasterKeyMissing(
            f"{MASTER_KEY_ENV} is not configured."
        )

    return Fernet(
        _fernet_key_from_master(
            master
        )
    )


def is_encrypted_envelope(
    value: Any,
) -> bool:
    return (
        isinstance(
            value,
            dict,
        )
        and value.get(
            ENVELOPE_MARKER
        )
        is True
        and value.get(
            "version"
        )
        == ENVELOPE_VERSION
        and isinstance(
            value.get(
                "ciphertext"
            ),
            str,
        )
    )


def encrypt_value(
    value: Any,
) -> dict[
    str,
    Any,
]:
    if is_encrypted_envelope(
        value
    ):
        return value

    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
        default=str,
    ).encode(
        "utf-8"
    )

    ciphertext = (
        _load_fernet()
        .encrypt(
            payload
        )
        .decode(
            "ascii"
        )
    )

    return {
        ENVELOPE_MARKER:
            True,

        "version":
            ENVELOPE_VERSION,

        "ciphertext":
            ciphertext,
    }


def decrypt_value(
    value: Any,
) -> Any:
    if not is_encrypted_envelope(
        value
    ):
        return value

    try:
        plaintext = (
            _load_fernet()
            .decrypt(
                value[
                    "ciphertext"
                ].encode(
                    "ascii"
                )
            )
        )

        return json.loads(
            plaintext.decode(
                "utf-8"
            )
        )

    except (
        InvalidToken,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise IntegrationSecretDecryptError(
            "Integration secret could not be decrypted."
        ) from exc


def encrypt_sensitive_config(
    value: Any,
) -> Any:
    """
    Recursively encrypt values belonging to sensitive keys.

    Non-secret operational metadata remains readable for indexing,
    health/status rendering and debugging.
    """

    if isinstance(
        value,
        list,
    ):
        return [
            encrypt_sensitive_config(
                item
            )
            for item
            in value
        ]

    if not isinstance(
        value,
        dict,
    ):
        return value

    if is_encrypted_envelope(
        value
    ):
        return value

    output = {}

    for key, item in (
        value.items()
    ):
        if is_sensitive_key(
            str(
                key
            )
        ):
            output[
                key
            ] = encrypt_value(
                item
            )

        else:
            output[
                key
            ] = encrypt_sensitive_config(
                item
            )

    return output


def decrypt_sensitive_config(
    value: Any,
) -> Any:
    if isinstance(
        value,
        list,
    ):
        return [
            decrypt_sensitive_config(
                item
            )
            for item
            in value
        ]

    if not isinstance(
        value,
        dict,
    ):
        return value

    if is_encrypted_envelope(
        value
    ):
        return decrypt_value(
            value
        )

    return {
        key:
            decrypt_sensitive_config(
                item
            )
        for key, item
        in value.items()
    }


def redact_sensitive_config(
    value: Any,
) -> Any:
    """
    Safe representation for APIs, logs and audit payloads.
    """

    if isinstance(
        value,
        list,
    ):
        return [
            redact_sensitive_config(
                item
            )
            for item
            in value
        ]

    if not isinstance(
        value,
        dict,
    ):
        return value

    if is_encrypted_envelope(
        value
    ):
        return REDACTED_VALUE

    output = {}

    for key, item in (
        value.items()
    ):
        if is_sensitive_key(
            str(
                key
            )
        ):
            output[
                key
            ] = REDACTED_VALUE

        else:
            output[
                key
            ] = redact_sensitive_config(
                item
            )

    return output


def contains_plaintext_secret(
    value: Any,
) -> bool:
    """
    Used by tests / migration tooling.

    A sensitive key whose value is not encrypted is plaintext.
    """

    if isinstance(
        value,
        list,
    ):
        return any(
            contains_plaintext_secret(
                item
            )
            for item
            in value
        )

    if not isinstance(
        value,
        dict,
    ):
        return False

    if is_encrypted_envelope(
        value
    ):
        return False

    for key, item in (
        value.items()
    ):
        if is_sensitive_key(
            str(
                key
            )
        ):
            if not is_encrypted_envelope(
                item
            ):
                return True

        elif contains_plaintext_secret(
            item
        ):
            return True

    return False
