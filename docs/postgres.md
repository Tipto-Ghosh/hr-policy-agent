# Postgres backend

The agent supports two persistence backends for **short-term memory**
(per-chat history) and **long-term memory** (per-user preferences):

| State | Default (no DSN) | Postgres (DSN set) |
|---|---|---|
| Short-term (checkpointer) | AsyncSqliteSaver | AsyncPostgresSaver |
| Long-term (Store) | InMemoryStore | PostgresStore |

Audit log, feedback, Pinecone, and the LLM layer are **not** affected.
This is intentional — the migration is scoped to memory.

## Quickstart

```bash
# 1. Start Postgres (Docker)
docker compose up -d postgres

# 2. Point the app at it
echo 'POSTGRES_DSN=postgresql://hr_agent:hr_agent_dev@localhost:5432/hr_agent' >> .env

# 3. Provision tables (one time, idempotent)
uv run python scripts/init_postgres.py

# 4. Restart the API
uv run uvicorn hr_agent.api.app:app --reload