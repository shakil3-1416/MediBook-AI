from __future__ import annotations

import hashlib
import hmac
import time


class WebhookSignatureError(ValueError):
    pass


def _normalize_signature(
    signature: str,
) -> str:
    signature = (
        signature
        .strip()
        .lower()
    )

    if signature.startswith(
        "sha256="
    ):
        signature = signature[
            len("sha256="):
        ]

    if len(signature) != 64:
        raise WebhookSignatureError(
            "Invalid webhook signature format."
        )

    try:
        int(signature, 16)
    except ValueError as exc:
        raise WebhookSignatureError(
            "Invalid webhook signature encoding."
        ) from exc

    return signature


def verify_hmac_sha256_webhook(
    *,
    body: bytes,
    signature: str,
    secret: str,
    timestamp: str | None = None,
    max_age_seconds: int = 300,
    now: int | None = None,
) -> None:
    if not secret:
        raise WebhookSignatureError(
            "Webhook secret is not configured."
        )

    supplied = _normalize_signature(
        signature
    )

    signed_payload = body

    if timestamp is not None:
        try:
            timestamp_value = int(
                timestamp
            )
        except ValueError as exc:
            raise WebhookSignatureError(
                "Invalid webhook timestamp."
            ) from exc

        current_time = (
            int(time.time())
            if now is None
            else int(now)
        )

        if abs(
            current_time
            -
            timestamp_value
        ) > max(
            1,
            int(max_age_seconds),
        ):
            raise WebhookSignatureError(
                "Webhook timestamp is outside "
                "the allowed replay window."
            )

        signed_payload = (
            timestamp.encode("utf-8")
            +
            b"."
            +
            body
        )

    expected = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        supplied,
        expected,
    ):
        raise WebhookSignatureError(
            "Webhook signature verification failed."
        )
