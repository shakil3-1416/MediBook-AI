from __future__ import annotations

import os
from collections.abc import Iterable


class ProductionConfigurationError(RuntimeError):
    pass


def environment_name() -> str:
    return (
        os.getenv("MEDIBOOK_ENV")
        or os.getenv("APP_ENV")
        or os.getenv("ENVIRONMENT")
        or "development"
    ).strip().lower()


def is_production() -> bool:
    return environment_name() in {
        "production",
        "prod",
    }


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise ProductionConfigurationError(
            f"{name} must be configured in production."
        )

    return value


def _secret(name: str) -> str:
    value = _required(name)

    if len(value) < 32:
        raise ProductionConfigurationError(
            f"{name} must contain at least 32 characters "
            "in production."
        )

    return value


def production_cors_origins(
    development_origins: Iterable[str],
) -> list[str]:
    defaults = list(development_origins)

    if not is_production():
        return defaults

    raw = _required(
        "MEDIBOOK_ALLOWED_ORIGINS"
    )

    origins = [
        value.strip()
        for value in raw.split(",")
        if value.strip()
    ]

    if not origins:
        raise ProductionConfigurationError(
            "No production CORS origins configured."
        )

    if "*" in origins:
        raise ProductionConfigurationError(
            "Wildcard CORS is forbidden in production."
        )

    return origins


def validate_production_environment(
    *,
    app_debug: bool,
) -> None:
    if not is_production():
        return

    if app_debug:
        raise ProductionConfigurationError(
            "Debug mode must be disabled in production."
        )

    _secret("JWT_SECRET")
    _secret("MEDIBOOK_OTP_SECRET")

    _required("MEDIBOOK_SMTP_HOST")
    _required("MEDIBOOK_SMTP_FROM")

    username = os.getenv(
        "MEDIBOOK_SMTP_USERNAME",
        "",
    ).strip()

    password = os.getenv(
        "MEDIBOOK_SMTP_PASSWORD",
        "",
    ).strip()

    if bool(username) != bool(password):
        raise ProductionConfigurationError(
            "SMTP username and password must be "
            "configured together."
        )

    storage = _required(
        "MEDIBOOK_PROFILE_STORAGE"
    ).lower()

    if storage not in {
        "s3",
        "aws-s3",
        "aws_s3",
        "r2",
        "minio",
    }:
        raise ProductionConfigurationError(
            "Production profile storage must use "
            "an S3-compatible provider."
        )

    _required("MEDIBOOK_S3_BUCKET")

    production_cors_origins([])
