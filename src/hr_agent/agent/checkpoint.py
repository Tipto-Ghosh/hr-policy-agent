from __future__ import annotations

import sqlite3
from functools import lru_cache
from pathlib import Path

from aiosqlite import connect as aiosqlite_connect
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from hr_agent.core.settings import get_settings

__all__ = ["get_checkpointer"]

def _build_serde() -> JsonPlusSerializer:
    """
    Build a JsonPlusSerializer with our custom state types registered.
    
    Types that flow through AgentState channels and need checkpointing
    must be listed here, or LangGraph logs a warning and (in future
    versions) will block deserialization.
    """
    return JsonPlusSerializer(
        allowed_msgpack_modules=[
            ("hr_agent.memory.profile_adapter", "UserProfile"),
        ],
    )
    
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
    return SqliteSaver(conn = conn, serde = _build_serde())



_async_checkpointer: AsyncSqliteSaver | None = None

async def get_async_checkpointer() -> AsyncSqliteSaver:
    """
    Return the async checkpointer.
    
    Backend is selected by `settings.postgres_dsn`:
     - non-empty -> AsyncPostgresSaver (see checkpoint_postgres.py)
      - empty -> AsyncSqliteSaver
    """
    
    settings = get_settings()
    # postgres branch
    if settings.uses_postgres:
        from hr_agent.agent.checkpoint_postgres import (
            get_async_postgres_checkpointer
        )
        return await get_async_postgres_checkpointer()
    
    # sqlite branch
    global _async_checkpointer
    if _async_checkpointer is not None:
        return _async_checkpointer
    
    db_path = Path(settings.memory_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite_connect(str(db_path))
    _async_cp = AsyncSqliteSaver(conn)
    return _async_cp
    

async def close_async_checkpointer() -> None:
    """Close the cached async checkpointer (call on FastAPI shutdown)."""
    settings = get_settings()
    if settings.uses_postgres:
        from hr_agent.agent.checkpoint_postgres import (
            close_async_postgres_checkpointer
        )
        await close_async_postgres_checkpointer()
        return
    
    global _async_checkpointer
    if _async_checkpointer is not None:
        await _async_checkpointer.conn.close()
        _async_checkpointer = None