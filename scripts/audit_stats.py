from __future__ import annotations
import argparse
import sqlite3
from pathlib import Path

from hr_agent.core.settings import get_settings

def _row_counts(con: sqlite3.Connection) -> dict:
    """
    Count audit rows by verdict. Uses Python-side classification rather
    than SQL string comparison so the logic is transparent and can't
    drift from the writer's values.
    """
    rows = con.execute("SELECT guard_verdict FROM query_audit").fetchall()

    def bucket(v):
        # v may be None, '', or any string the writer produced.
        if v is None:
            return "unknown"
        v_norm = v.strip().lower()
        if v_norm == "":
            return "unknown"
        if v_norm == "ok":
            return "ok"
        if v_norm == "sensitive_case":
            return "sensitive"
        return "blocked"

    counts = {"ok": 0, "blocked": 0, "sensitive": 0, "unknown": 0}
    for (v,) in rows:
        counts[bucket(v)] += 1

    return {
        "total": len(rows),
        "blocked": counts["blocked"],
        "sensitive": counts["sensitive"],
        # kept out of the report for now, but visible if you want it
        "unknown": counts["unknown"],
        "ok": counts["ok"],
    }
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