from __future__ import annotations
import json
from datetime import datetime, timezone

from hr_agent.audit.db import connect
from hr_agent.audit.models import AuditRow

def write_audit(
    question: str, 
    source_used: str, 
    trace_steps: list[str], 
    request_id: str = "", 
    user_id_hash: str = "",
    guard_verdict: str = "",
    guard_reason: str = "" 
) -> int:
    """
    Insert one audit row into the database and return the new row's ID.
    """
    with connect() as con:
        cursor = con.execute(
            """INSERT INTO query_audit
               (created_at, request_id, user_id_hash, question,
                guard_verdict, guard_reason, source_used, trace_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                request_id,
                user_id_hash,
                question,
                guard_verdict,
                guard_reason,
                source_used,
                json.dumps(trace_steps),
            ),
        )
        con.commit()
        return cursor.lastrowid
    

def read_recent(limit: int = 20) -> list[AuditRow]:
    """
    Read the most recent `limit` audit rows, newest first.
    Mainly for notebook verification and admin tooling — not on any hot path.
    """
    with connect() as con:
        cursor = con.execute(
            """SELECT id, created_at, request_id, user_id_hash, question,
               guard_verdict, guard_reason, source_used, trace_json
               FROM query_audit
               ORDER BY id DESC
               LIMIT ?""",
            (limit,),
        )
        rows = cursor.fetchall()

    return [
        AuditRow(
            id = r[0],
            created_at = r[1],
            request_id = r[2],
            user_id_hash = r[3],
            question = r[4],
            guard_verdict = r[5],
            guard_reason = r[6],
            source_used = r[7],
            trace = json.loads(r[8]),
        )
        for r in rows
    ]
    
def write_feedback(
    request_id: str,
    user_id_hash: str,
    thumb: str,
    reason: str = "",
) -> int:
    """
    Insert one feedback row. Returns the new row id. `thumb` should be
    'up' or 'down'; the API schema enforces this, but the writer accepts
    any string so it stays usable from scripts.
    """
    with connect() as con:
        cursor = con.execute(
            """INSERT INTO feedback
               (created_at, request_id, user_id_hash, thumb, reason)
               VALUES (?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                request_id,
                user_id_hash,
                thumb,
                reason,
            ),
        )
        con.commit()
        return cursor.lastrowid

def read_feedback(limit: int = 50) -> list[dict]:
    """Read the most recent feedback rows, newest first."""
    with connect() as con:
        rows = con.execute(
            """SELECT id, created_at, request_id, user_id_hash, thumb, reason
               FROM feedback
               ORDER BY id DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
    return [
        {
            "id": r[0],
            "created_at": r[1],
            "request_id": r[2],
            "user_id_hash": r[3],
            "thumb": r[4],
            "reason": r[5] or "",
        }
        for r in rows
    ]