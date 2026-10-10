# Docker

The HR Policy Agent supports two deployment styles:

| Style | Postgres | API | Streamlit UI | Ollama |
|---|---|---|---|---|
| **Native dev** | `docker compose up -d postgres` | `uv run python scripts/run_api.py` | `uv run streamlit run ui/app.py` | `ollama serve` on host |
| **Containerized API** | `docker compose up -d postgres` | `docker compose up -d api` | `uv run streamlit run ui/app.py` | `ollama serve` on host |

The same Python code runs in both cases. The container only changes *where* the API process runs.

## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- Ollama running on the host (for local fallbacks)
- `.env` at the repo root with `GROQ_API_KEY`, `PINECONE_API_KEY`, and `JWT_SECRET` set

## Quickstart — containerized API

```bash
# 1. Copy and fill in the env file
cp .env.example .env
# edit .env: set GROQ_API_KEY, PINECONE_API_KEY, JWT_SECRET

# 2. Bring the stack up (Postgres + API)
docker compose up -d

# 3. Wait for both to become healthy
docker compose ps
# hr-agent-postgres   Up (healthy)
# hr-agent-api        Up (healthy)

# 4. Hit the API
curl http://localhost:8000/health
curl http://localhost:8000/ready | python -m json.tool