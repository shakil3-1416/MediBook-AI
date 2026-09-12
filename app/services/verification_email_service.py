from __future__ import annotations

import asyncio
from email.message import EmailMessage
import json
import os
from pathlib import Path
import smtplib
import ssl


class EmailDeliveryNotConfigured(
    RuntimeError
):
    pass


def _subject_and_body(
    code: str,
    purpose: str,
) -> tuple[str, str]:

    if purpose == "password_reset":
        return (
            "Reset your MediBook password",
            (
                "Reset your MediBook password\n\n"
                "Your verification code is:\n\n"
                f"{code}\n\n"
                "This code expires in 10 minutes.\n\n"
                "If you did not request a password reset, "
                "you can ignore this email."
            ),
        )

    if purpose == "email_change":
        return (
            "Verify your new MediBook email",
            (
                "Verify your new MediBook email address\n\n"
                "Your verification code is:\n\n"
                f"{code}\n\n"
                "This code expires in 10 minutes.\n\n"
                "Your MediBook email will not change "
                "until this code is verified."
            ),
        )

    return (
        "Your MediBook verification code",
        (
            "Verify your MediBook account\n\n"
            "Your verification code is:\n\n"
            f"{code}\n\n"
            "This code expires in 10 minutes.\n\n"
            "If you did not try to create a "
            "MediBook account, you can ignore this email."
        ),
    )


def _smtp_send(
    recipient: str,
    code: str,
    purpose: str,
) -> None:

    host = os.getenv(
        "MEDIBOOK_SMTP_HOST",
        "",
    ).strip()

    sender = os.getenv(
        "MEDIBOOK_SMTP_FROM",
        "",
    ).strip()

    username = os.getenv(
        "MEDIBOOK_SMTP_USERNAME",
        "",
    ).strip()

    password = os.getenv(
        "MEDIBOOK_SMTP_PASSWORD",
        "",
    )

    port = int(
        os.getenv(
            "MEDIBOOK_SMTP_PORT",
            "587",
        )
    )

    tls = (
        os.getenv(
            "MEDIBOOK_SMTP_TLS",
            "true",
        ).lower()
        in {
            "1",
            "true",
            "yes",
        }
    )

    if (
        not host
        or
        not sender
    ):
        raise EmailDeliveryNotConfigured(
            "Verification email delivery "
            "is not configured."
        )

    subject, body = (
        _subject_and_body(
            code,
            purpose,
        )
    )

    message = EmailMessage()

    message[
        "Subject"
    ] = subject

    message[
        "From"
    ] = sender

    message[
        "To"
    ] = recipient

    message.set_content(
        body
    )

    with smtplib.SMTP(
        host,
        port,
        timeout=15,
    ) as smtp:

        if tls:
            smtp.starttls(
                context=(
                    ssl.create_default_context()
                ),
            )

        if username:
            smtp.login(
                username,
                password,
            )

        smtp.send_message(
            message
        )


def _development_sink(
    recipient: str,
    code: str,
) -> None:
    """
    Local E2E testing only.

    This mode is never automatically selected.
    Production must use SMTP/provider delivery.
    """

    destination = os.getenv(
        "MEDIBOOK_VERIFICATION_DEV_FILE",
        "",
    ).strip()

    if not destination:
        raise EmailDeliveryNotConfigured(
            "Development verification sink "
            "has no destination."
        )

    Path(
        destination
    ).write_text(
        json.dumps(
            {
                "email":
                    recipient,

                "code":
                    code,
            }
        )
    )


def _send(
    recipient: str,
    code: str,
    purpose: str,
) -> None:

    mode = os.getenv(
        "MEDIBOOK_VERIFICATION_DELIVERY",
        "smtp",
    ).strip().lower()

    if mode == "development_file":
        _development_sink(
            recipient,
            code,
        )

        return

    if mode != "smtp":
        raise EmailDeliveryNotConfigured(
            "Unknown verification "
            "delivery mode."
        )

    _smtp_send(
        recipient,
        code,
        purpose,
    )


async def send_verification_code(
    recipient: str,
    code: str,
    purpose: str = "account_verification",
) -> None:

    await asyncio.to_thread(
        _send,
        recipient,
        code,
        purpose,
    )
