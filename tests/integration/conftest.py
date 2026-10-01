"""Isolation for the shared async SQLAlchemy engine in integration tests.

pytest-asyncio runs every test in its own event loop, while the app's
engine is a module-level singleton. asyncpg connections pooled under one
test's loop cannot be reused under the next test's loop, so each
integration test starts from an empty pool and closes its own
connections when it finishes.
"""

import sys

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker


def _app_async_engines():
    engines = {}
    for name, module in list(sys.modules.items()):
        if module is None or not (name == "app" or name.startswith("app.")):
            continue
        for value in list(vars(module).values()):
            if isinstance(value, AsyncEngine):
                engines[id(value)] = value
            elif isinstance(value, async_sessionmaker):
                bind = value.kw.get("bind")
                if isinstance(bind, AsyncEngine):
                    engines[id(bind)] = bind
    return list(engines.values())


@pytest.fixture(autouse=True)
async def _fresh_async_engine_pool():
    for engine in _app_async_engines():
        await engine.dispose(close=False)
    yield
    for engine in _app_async_engines():
        await engine.dispose()
