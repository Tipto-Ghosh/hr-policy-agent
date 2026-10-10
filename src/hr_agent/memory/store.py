from __future__ import annotations
from functools import lru_cache
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore

from hr_agent.core.settings import get_settings

__all__ = [
    "get_store",
    "preference_namespace"
]

def preference_namespace(user_id_hash: str) -> tuple[str, ...]:
    """Return a tuple representing the namespace for storing user preferences."""
    return ("users", user_id_hash, "preferences")


def get_store() -> BaseStore:
    """
    Return the long-term preference Store.

    Backend is selected by `settings.postgres_dsn`:
      - non-empty -> PostgresStore 
      - empty -> InMemoryStore
    """
    settings = get_settings()

    # Postgres branch
    if settings.uses_postgres:
        from hr_agent.memory.store_postgres import get_postgres_store
        return get_postgres_store()

    return _get_inmemory_store()

def _get_inmemory_store() -> BaseStore:
    return InMemoryStore()