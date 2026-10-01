"""Database bootstrap for deployments (run by the production migrate service).

An EMPTY database is created from migrations/baseline/schema.sql, a schema-only
snapshot of a database migrated to BASELINE_REVISION, and stamped at that
revision. The historical migration chain upgrades existing databases but cannot
build an empty one. Every run then applies `alembic upgrade head`.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import asyncpg
from sqlalchemy.engine import make_url

from app.core.config import settings

BASELINE_REVISION = "m6b2queue20260930"
BASELINE_SQL = (
    Path(__file__).resolve().parent.parent / "migrations" / "baseline" / "schema.sql"
)


def _dsn() -> str:
    url = make_url(settings.database_url).set(drivername="postgresql")
    return url.render_as_string(hide_password=False)


async def _bootstrap_if_empty() -> str:
    conn = await asyncpg.connect(_dsn())
    try:
        tables = await conn.fetchval(
            "select count(*) from information_schema.tables "
            "where table_schema = 'public'"
        )
        if tables:
            return "existing"
        schema_sql = BASELINE_SQL.read_text(encoding="utf-8")
        async with conn.transaction():
            await conn.execute(schema_sql)
            await conn.execute(
                "insert into public.alembic_version (version_num) values ($1)",
                BASELINE_REVISION,
            )
        return "bootstrapped"
    finally:
        await conn.close()


def main() -> int:
    state = asyncio.run(_bootstrap_if_empty())
    print(f"database: {state}", flush=True)
    return subprocess.call([sys.executable, "-m", "alembic", "upgrade", "head"])


if __name__ == "__main__":
    raise SystemExit(main())
