from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from hr_agent.core.settings import get_settings


def _counts(con: sqlite3.Connection) -> dict:
    total = con.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    up = con.execute(
        "SELECT COUNT(*) FROM feedback WHERE TRIM(LOWER(thumb)) = 'up'"
    ).fetchone()[0]
    down = con.execute(
        "SELECT COUNT(*) FROM feedback WHERE TRIM(LOWER(thumb)) = 'down'"
    ).fetchone()[0]
    return {"total": total, "up": up, "down": down}


def _recent(con: sqlite3.Connection, limit: int) -> list[tuple]:
    return con.execute(
        """SELECT id, created_at, thumb, request_id, reason
           FROM feedback
           ORDER BY id DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    db_path = Path(get_settings().audit_db_path)
    if not db_path.exists():
        print(f"Audit DB not found: {db_path}")
        return

    con = sqlite3.connect(db_path)
    try:
        c = _counts(con)
        print(f"Audit DB : {db_path}")
        print(f"Total    : {c['total']}")
        print(f"Thumbs up: {c['up']}")
        print(f"Thumbs dn: {c['down']}")
        if c["total"]:
            ratio = (c["up"] / c["total"]) * 100
            print(f"Approval : {ratio:.1f}%")

        print(f"\nRecent {args.limit} rows:")
        for r in _recent(con, args.limit):
            rid, created, thumb, req, reason = r
            thumb = thumb or "-"
            reason = (reason[:60] + "...") if reason and len(reason) > 60 else (reason or "")
            print(f"  #{rid} {created} [{thumb}] req={req[:12]}… {reason}")
    finally:
        con.close()


if __name__ == "__main__":
    main()