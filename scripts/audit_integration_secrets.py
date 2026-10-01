from __future__ import annotations

import asyncio
import inspect

from sqlalchemy import (
    select,
)

import app.core.database as database

from app.models.hospital import (
    HospitalIntegration,
)

from app.services.integration_secret_crypto import (
    contains_plaintext_secret,
)


async def acquire():
    for name in (
        "get_db_session",
        "get_db",
    ):
        fn = getattr(
            database,
            name,
            None,
        )

        if (
            fn
            and inspect.isasyncgenfunction(
                fn
            )
        ):
            gen = fn()

            return (
                await anext(
                    gen
                ),
                gen,
            )

    raise RuntimeError(
        "Database dependency unavailable."
    )


async def main():
    session, gen = await acquire()

    try:
        result = await session.execute(
            select(
                HospitalIntegration
            )
        )

        integrations = (
            result.scalars()
            .all()
        )


        total = len(
            integrations
        )

        plaintext_rows = 0


        for integration in integrations:
            if contains_plaintext_secret(
                integration.config
                or {}
            ):
                plaintext_rows += 1


        print(
            f"integrations_total={total}"
        )

        print(
            f"plaintext_secret_rows={plaintext_rows}"
        )


        # Audit only.
        # Do not fail because existing legacy rows
        # may require controlled migration.
        return plaintext_rows

    finally:
        await gen.aclose()


if __name__ == "__main__":
    asyncio.run(
        main()
    )
