from __future__ import annotations
from  langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from hr_agent.core.settings import get_settings


__all__ = [
    "get_async_postgres_checkpointer",
    "init_postgres_checkpointer",
    "close_async_postgres_checkpointer",
    "reset_postgres_checkpointer_cache",
]

_pool: AsyncConnectionPool | None = None
_saver: AsyncPostgresSaver | None = None

async def get_async_postgres_checkpointer() -> AsyncPostgresSaver:
    """
    Return the process-wide AsyncPostgresSaver singleton. Creates the
    connection pool on first call. Must be called from within a running
    event loop.
    """
    global _pool, _saver
    if _saver is not None:
        return _saver

    settings = get_settings()
    if not settings.postgres_dsn:
        raise RuntimeError(
            "get_async_postgres_checkpointer() called but POSTGRES_DSN is empty."
        )

    # `open=False` then explicit `await pool.open()` because we are inside
    # an async context. min_size=1 keeps idle connections modest for dev;
    # max_size=10 is plenty for a single-process API.
    _pool = AsyncConnectionPool(
        conninfo=settings.postgres_dsn,
        min_size=1,
        max_size=10,
        open=False,
        kwargs={"autocommit": True, "prepare_threshold": 0},
    )
    await _pool.open(wait=True, timeout=10.0)

    _saver = AsyncPostgresSaver(_pool)
    return _saver


async def init_postgres_checkpointer() -> None:
    """
    Create the checkpoint tables if they don't exist. Idempotent.
    Called by scripts/init_postgres.py, not on every API startup.
    """
    saver = await get_async_postgres_checkpointer()
    await saver.setup()


async def close_async_postgres_checkpointer() -> None:
    """Close the pool cleanly. Called from the FastAPI lifespan shutdown."""
    global _pool, _saver
    if _pool is not None:
        await _pool.close()
    _pool = None
    _saver = None


def reset_postgres_checkpointer_cache() -> None:
    """Testing helper — drop the cached pool/saver so the next call rebuilds."""
    global _pool, _saver
    _pool = None
    _saver = None