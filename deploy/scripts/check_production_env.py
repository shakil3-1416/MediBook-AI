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
