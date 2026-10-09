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
    Async counterpart to get_checkpointer().
    """
    global _async_checkpointer
    if _async_checkpointer is None:
        import aiosqlite

        settings = get_settings()
        db_path = Path(settings.memory_db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = await aiosqlite.connect(str(db_path))
        _async_checkpointer = AsyncSqliteSaver(
            conn=conn,
            serde=_build_serde(),
        )
    return _async_checkpointer


async def close_async_checkpointer() -> None:
    """Close the cached async checkpointer (call on FastAPI shutdown)."""
    global _async_checkpointer
    if _async_checkpointer is not None:
        await _async_checkpointer.conn.close()
        _async_checkpointer = None