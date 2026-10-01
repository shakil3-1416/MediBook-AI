from __future__ import annotations

from typing import Any

from sqlalchemy import event

from app.models.hospital import (
    HospitalIntegration,
)

from app.services.integration_secret_crypto import (
    decrypt_sensitive_config,
    encrypt_sensitive_config,
    redact_sensitive_config,
)


def prepare_integration_config_for_storage(
    config: dict[
        str,
        Any,
    ] | None,
) -> dict[
    str,
    Any,
]:
    """
    Convert integration configuration to its database representation.

    Secret-shaped values are encrypted while non-secret operational
    metadata remains readable.

    The transformation is idempotent, so an already encrypted config
    may safely pass this boundary again.
    """

    return encrypt_sensitive_config(
        dict(
            config
            or {}
        )
    )


def prepare_integration_config_for_runtime(
    config: dict[
        str,
        Any,
    ] | None,
) -> dict[
        str,
        Any,
]:
    """
    Return decrypted configuration for trusted adapter/runtime use.

    This representation must never be returned from a public API,
    serialized to audit payloads, or written to application logs.
    """

    return decrypt_sensitive_config(
        dict(
            config
            or {}
        )
    )


def prepare_integration_config_for_public_response(
    config: dict[
        str,
        Any,
    ] | None,
) -> dict[
        str,
        Any,
]:
    """
    Return an API/log-safe representation.

    Both plaintext secret values and encrypted envelopes are replaced
    with redaction markers.
    """

    return redact_sensitive_config(
        dict(
            config
            or {}
        )
    )


def _encrypt_model_config(
    target: HospitalIntegration,
) -> None:
    target.config = (
        prepare_integration_config_for_storage(
            target.config
        )
    )


@event.listens_for(
    HospitalIntegration,
    "before_insert",
)
def _hospital_integration_before_insert(
    mapper,
    connection,
    target: HospitalIntegration,
) -> None:
    del mapper
    del connection

    _encrypt_model_config(
        target
    )


@event.listens_for(
    HospitalIntegration,
    "before_update",
)
def _hospital_integration_before_update(
    mapper,
    connection,
    target: HospitalIntegration,
) -> None:
    del mapper
    del connection

    _encrypt_model_config(
        target
    )
