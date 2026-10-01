from __future__ import annotations
from functools import lru_cache
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore


__all__ = [
    "get_store",
    "preference_namespace"
]

def preference_namespace(user_id_hash: str) -> tuple[str, ...]:
    """Return a tuple representing the namespace for storing user preferences."""
    return ("users", user_id_hash, "preferences")


@lru_cache
def get_store() -> BaseStore:
    return InMemoryStore()