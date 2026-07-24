"""
api/deps.py — FastAPI dependency injection.

Provides the database connection and config to route handlers.
The config singleton is loaded once at startup.
"""

from __future__ import annotations

from typing import Annotated, AsyncGenerator

import psycopg
from fastapi import Depends, Request

from engine.config import Config, load_config
from engine.store.repo import Repository

# ─────────────────────────────────────────────────────────────────────────────
# Config singleton
# ─────────────────────────────────────────────────────────────────────────────

_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = load_config()
    return _config


ConfigDep = Annotated[Config, Depends(get_config)]


# ─────────────────────────────────────────────────────────────────────────────
# Database connection pool (attached to app lifespan)
# ─────────────────────────────────────────────────────────────────────────────


async def get_repo(request: Request) -> AsyncGenerator[Repository, None]:
    """Yield a Repository backed by a connection from the pool."""
    pool: psycopg.AsyncConnectionPool = request.app.state.db_pool
    async with pool.connection() as conn:
        yield Repository(conn)


RepoDep = Annotated[Repository, Depends(get_repo)]
