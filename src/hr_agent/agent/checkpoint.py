"""
Checkpoint for short-term(per-thread) memory.
SqliteServer for now, PostgresServer when FastAPI lands.
"""
# TODO: For now we are using sqlite for short-term memory, but we should switch to Postgres when FastAPI is implemented.

from __future__ import annotations
import sqlite3
from functools import lru_cache
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver

from hr_agent.core.settings import get_settings

__all__ = ["get_checkpointer"]


# Cached so we dont open a new connection per graph invocation
@lru_cache()
def get_checkpointer() -> SqliteSaver:
    settings = get_settings()
    db_path = Path(settings.memory_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(
        str(db_path),
        check_same_thread = False
    )
    return SqliteSaver(conn = conn)