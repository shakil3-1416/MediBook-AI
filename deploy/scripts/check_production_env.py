from pathlib import Path
import sys


path = Path(".env.production")


if not path.exists():

    print(
        "PRODUCTION ENV: MISSING"
    )

    print(
        "Create .env.production from "
        ".env.production.example"
    )

    sys.exit(0)


values = {}


for raw in path.read_text().splitlines():

    line = raw.strip()

    if (
        not line
        or line.startswith("#")
        or "=" not in line
    ):
        continue


    key, value = line.split(
        "=",
        1,
    )

    values[
        key.strip()
    ] = value.strip()


required = [
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "DATABASE_URL",
    "REDIS_URL",
    "JWT_SECRET",
    "JWT_ALGORITHM",
    "MEDIBOOK_DOMAIN",
    "FRONTEND_ORIGIN",
    "MEDIBOOK_INTEGRATION_MASTER_KEY",
    "MEDIBOOK_OTP_SECRET",
    "MEDIBOOK_VERIFICATION_DELIVERY",
    "MEDIBOOK_SMTP_HOST",
    "MEDIBOOK_SMTP_PORT",
    "MEDIBOOK_SMTP_FROM",
    "MEDIBOOK_PROFILE_STORAGE",
    "MEDIBOOK_ALLOWED_ORIGINS",
]


failures = []


for key in required:

    value = values.get(
        key,
        "",
    )

    if not value:

        failures.append(
            f"{key} missing"
        )

    elif "CHANGE_ME" in value:

        failures.append(
            f"{key} still uses placeholder"
        )


storage = values.get("MEDIBOOK_PROFILE_STORAGE", "").strip().lower()

if storage in {"", "local"}:

    failures.append(
        "MEDIBOOK_PROFILE_STORAGE must be S3-compatible in production "
        "(local files are lost when containers are recreated)"
    )

else:

    for key in (
        "MEDIBOOK_S3_BUCKET",
        "MEDIBOOK_S3_ACCESS_KEY_ID",
        "MEDIBOOK_S3_SECRET_ACCESS_KEY",
    ):

        if not values.get(key, ""):

            failures.append(
                f"{key} missing (required for S3 profile storage)"
            )


delivery = values.get("MEDIBOOK_VERIFICATION_DELIVERY", "smtp").strip().lower()

if delivery not in {"smtp"}:

    failures.append(
        "MEDIBOOK_VERIFICATION_DELIVERY must be smtp in production"
    )


for key, value in sorted(values.items()):

    message = f"{key} still uses placeholder"

    if "CHANGE_ME" in value and message not in failures:

        failures.append(message)


for key in ("FRONTEND_ORIGIN", "MEDIBOOK_ALLOWED_ORIGINS"):

    for origin in values.get(key, "").split(","):

        origin = origin.strip().strip('"').strip("'")

        message = f"{key} must use https:// in production"

        if (
            origin
            and "CHANGE_ME" not in origin
            and not origin.startswith("https://")
            and message not in failures
        ):

            failures.append(message)


jwt = values.get(
    "JWT_SECRET",
    "",
)


if (
    jwt
    and "CHANGE_ME" not in jwt
    and len(jwt) < 64
):

    failures.append(
        "JWT_SECRET should contain at least 64 characters"
    )


if failures:

    print(
        "PRODUCTION ENV: NEEDS ATTENTION"
    )

    for item in failures:

        print(
            " -",
            item,
        )

else:

    print(
        "PRODUCTION ENV: PASS"
    )
