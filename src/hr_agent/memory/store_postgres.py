from __future__ import annotations

from langgraph.store.base import BaseStore
from langgraph.store.postgres import PostgresStore
from psycopg_pool import ConnectionPool

from hr_agent.core.settings import get_settings

__all__ = [
    "get_postgres_store",
    "init_postgres_store",
    "close_postgres_store",
    "reset_postgres_store_cache",
]

_pool: ConnectionPool | None = None
_store: PostgresStore | None = None

def get_postgres_store() -> BaseStore:
    """
    Return the process-wide PostgresStore singleton. Creates the sync
    connection pool on first call.

    The Store is a sync API by design (LangGraph's base store is sync);
    the checkpointer is async. Both backends share the same Postgres
    database but use independent pools.
    """
    global _pool, _store
    if _store is not None:
        return _store

    settings = get_settings()
    if not settings.postgres_dsn:
        raise RuntimeError("get_postgres_store() called but POSTGRES_DSN is empty.")

    _pool = ConnectionPool(
        conninfo=settings.postgres_dsn,
        min_size=1,
        max_size=10,
        open=True,                                # sync pool, can open here
        kwargs={"autocommit": True, "prepare_threshold": 0},
    )
    _store = PostgresStore(_pool)
    return _store

def init_postgres_store() -> None:
    """
    Create the Store tables if they don't exist. Idempotent.
    Called by scripts/init_postgres.py.
    """
    store = get_postgres_store()
    store.setup()

def close_postgres_store() -> None:
    """Close the pool cleanly."""
    global _pool, _store
    if _pool is not None:
        _pool.close()
    _pool = None
    _store = None


def reset_postgres_store_cache() -> None:
    """Testing helper."""
    global _pool, _store
    _pool = None
    _store = None