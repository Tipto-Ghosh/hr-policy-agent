from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from hr_agent.core.settings import get_settings

SCHEMA_VERSION = 2

@contextmanager
def connect():
    """
    Open a connection to the audit DB, ensuring:
      1. the parent directory exists
      2. the schema is present
    
    Yields the connection and always closes it on exit.
    """
    settings = get_settings()
    db_path = Path(settings.audit_db_path)
    db_path.parent.mkdir(parents = True, exist_ok = True)
    conn = sqlite3.connect(db_path)
    try:
        yield conn 
    finally:
        conn.close()

def init_db() -> None:
    with connect() as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS query_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                request_id TEXT,
                user_id_hash TEXT,
                question TEXT NOT NULL,
                guard_verdict TEXT,
                guard_reason TEXT,
                source_used TEXT NOT NULL,
                trace_json TEXT NOT NULL
            )"""
        )
        con.execute(
            """CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                request_id TEXT NOT NULL,
                user_id_hash TEXT,
                thumb TEXT NOT NULL,
                reason TEXT
            )"""
        )
        con.execute(
            """CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )"""
        )
        con.execute(
            "INSERT OR REPLACE INTO schema_meta (key, value) VALUES ('version', ?)",
            (str(SCHEMA_VERSION),),
        )
        con.commit()