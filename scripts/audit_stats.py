from __future__ import annotations
import argparse
import sqlite3
from pathlib import Path

from hr_agent.core.settings import get_settings

def _row_counts(con: sqlite3.Connection) -> dict:
    total = con.execute("SELECT COUNT(*) FROM query_audit").fetchone()[0]
    blocked = con.execute(
        "SELECT COUNT(*) FROM query_audit "
        "WHERE guard_verdict IS NOT NULL AND guard_verdict != '' "
        "AND guard_verdict != 'allow'"
    ).fetchone()[0]
    sensitive = con.execute(
        "SELECT COUNT(*) FROM query_audit "
        "WHERE guard_reason LIKE '%sensitive%'"
    ).fetchone()[0]
    return {"total": total, "blocked": blocked, "sensitive": sensitive}

def _top_sources(con: sqlite3.Connection, limit: int = 5) -> list[tuple[str, int]]:
    return con.execute(
        """SELECT source_used, COUNT(*) AS n
           FROM query_audit
           GROUP BY source_used
           ORDER BY n DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    
def _recent(con: sqlite3.Connection, limit: int) -> list[tuple]:
    return con.execute(
        """SELECT id, created_at, guard_verdict, guard_reason,
                  source_used, question
           FROM query_audit
           ORDER BY id DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5,
                        help="Number of recent rows to show (default: 5)")
    args = parser.parse_args()

    db_path = Path(get_settings().audit_db_path)
    if not db_path.exists():
        print(f"Audit DB not found at: {db_path}")
        print("Run `uv run python -m hr_agent.ingest` or execute a query first.")
        return

    con = sqlite3.connect(db_path)
    try:
        counts = _row_counts(con)
        print(f"Audit DB : {db_path}")
        print(f"Total: {counts['total']}")
        print(f"Blocked: {counts['blocked']}")
        print(f"Sensitive: {counts['sensitive']}")

        print("\nTop sources:")
        for src, n in _top_sources(con):
            print(f"  {src or '<empty>':<40} {n}")

        print(f"\nRecent {args.limit} rows (newest first):")
        for r in _recent(con, args.limit):
            rid, created, verdict, reason, source, question = r
            verdict = verdict or "-"
            reason = f" ({reason})" if reason else ""
            q = (question[:60] + "...") if len(question) > 60 else question
            print(f"  #{rid} {created} [{verdict}{reason}] src={source} | {q}")
    finally:
        con.close()


if __name__ == "__main__":
    main()