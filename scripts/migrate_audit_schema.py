import sqlite3
from hr_agent.core.settings import get_settings

db = sqlite3.connect(str(get_settings().audit_db_path))
cur = db.cursor()

try:
    cur.execute("ALTER TABLE query_audit RENAME COLUMN user_id TO user_id_hash")
    cur.execute("ALTER TABLE query_audit RENAME COLUMN guard_virdict TO guard_verdict")
    db.commit()
    print("Renamed columns in place.")
except sqlite3.OperationalError as e:
    print(f"RENAME COLUMN failed: {e}")
    print("Falling back to copy-table migration.")
    cur.execute("""
        CREATE TABLE query_audit_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            request_id TEXT,
            user_id_hash TEXT,
            question TEXT NOT NULL,
            guard_verdict TEXT,
            guard_reason TEXT,
            source_used TEXT NOT NULL,
            trace_json TEXT NOT NULL
        )
    """)
    cur.execute("""
        INSERT INTO query_audit_new
            (id, created_at, request_id, user_id_hash, question,
             guard_verdict, guard_reason, source_used, trace_json)
        SELECT id, created_at, request_id, user_id, question,
               guard_virdict, guard_reason, source_used, trace_json
        FROM query_audit
    """)
    cur.execute("DROP TABLE query_audit")
    cur.execute("ALTER TABLE query_audit_new RENAME TO query_audit")
    db.commit()
    print("Copy-table migration complete.")

db.close()