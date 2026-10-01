from __future__ import annotations

from typing import Iterable

__all__ = [
    "should_write_memory",
    "dedupe_by_key",
    "MEMORY_MAX_PER_USER",
    "MEMORY_TTL_DAYS",
]

MEMORY_MAX_PER_USER = 50
MEMORY_TTL_DAYS = 180


def should_write_memory(guard_verdict: str, preferences: list[dict]) -> bool:
    """
    Top-level gate: only write when the turn passed the guard and
    at least one preference candidate was extracted.
    """
    if guard_verdict != "ok":
        return False
    
    return bool(preferences)


def dedupe_by_key(existing: Iterable[dict], new: Iterable[dict]) -> list[dict]:
    """
    Key-based dedup. Semantic dedup can be layered on top later; this
    catches the common case where the same preference is extracted twice
    with the same key.
    """
    seen = {item.get("key") for item in existing if item.get("key")}
    return [item for item in new if item.get("key") and item["key"] not in seen]