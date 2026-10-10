# Start the Project — Step-by-Step

A complete guide for getting the HR Policy Agent running on a fresh
machine. Follow the steps in order. Every command is copy-paste ready.

### Getting Started

If you are starting fresh, follow these steps to clone the repository and set up your environment:

**Clone the repository:**
   ```bash
   git clone [https://github.com/Tipto-Ghosh/hr-policy-agent.git](https://github.com/Tipto-Ghosh/hr-policy-agent.git)
   ```
**Navigate into the project directory:**
   ```bash
   cd hr-policy-agent
   ```

**What you'll have at the end:**
- The HR Policy Agent API running locally.
- The Streamlit chat UI at `http://localhost:8501`.
- Postgres and the vector store backing it (containers + Pinecone).
- Answers with citations from the HR policy manual.

**Total time:** ~15 minutes on a fresh machine (longer on the very first
run because the embedding model downloads ~100 MB).

---

## Table of contents

- [Prerequisites](#prerequisites)
- [Step 1 — Verify prerequisites](#step-1--verify-prerequisites)
- [Step 2 — Clone and install](#step-2--clone-and-install)
- [Step 3 — Create the `.env` file](#step-3--create-the-env-file)
- [Step 4 — Start Postgres in Docker](#step-4--start-postgres-in-docker)
- [Step 5 — Provision Postgres tables](#step-5--provision-postgres-tables)
- [Step 6 — Ingest the HR policy into Pinecone](#step-6--ingest-the-hr-policy-into-pinecone)
- [Step 7 — Start the API](#step-7--start-the-api)
- [Step 8 — Start the Streamlit UI](#step-8--start-the-streamlit-ui)
- [Step 9 — Log in and ask a question](#step-9--log-in-and-ask-a-question)
- [Daily workflow after setup](#daily-workflow-after-setup)
- [Alternative: run everything in Docker](#alternative-run-everything-in-docker)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

You need **five things** installed before starting:

| # | Tool | Why | Where to get it |
|---|---|---|---|
| 1 | **Python 3.11+** | Runtime | [python.org](https://www.python.org/downloads/) |
| 2 | **uv** | Package manager (fast pip replacement) | [docs.astral.sh/uv](https://docs.astral.sh/uv/) |
| 3 | **Docker Desktop** | Runs Postgres in a container | [docker.com](https://www.docker.com/products/docker-desktop/) |
| 4 | **Groq API key** (free) | Primary LLM provider | [console.groq.com/keys](https://console.groq.com/keys) |
| 5 | **Pinecone API key** (free) | Vector store | [app.pinecone.io](https://app.pinecone.io/) |

**Optional:**
- **Ollama** for local LLM fallbacks — [ollama.com](https://ollama.com/)
- **Git** for cloning the repo — [git-scm.com](https://git-scm.com/)

**You do NOT need:**
- Node.js, npm, or any JavaScript tooling.
- A database server installed natively (Docker provides Postgres).
- GPU. Everything runs on CPU by default.

---

## Step 1 — Verify prerequisites

Open a terminal and run these commands. Each one should print a version.
If any fails, install the corresponding tool from the table above.

```bash
python --version       # expect: Python 3.11.x or higher
uv --version           # expect: uv 0.x.x
docker --version       # expect: Docker version 2x.x.x
docker compose version # expect: Docker Compose version v2.x.x
```

Confirm Docker Desktop is actually running (the icon in the tray should
be green):

```bash
docker info
```

If `docker info` errors with "Cannot connect to the Docker daemon", start
Docker Desktop from your applications menu and wait for it to become ready.

---

## Step 2 — Clone and install

**If you already have the repo cloned**, skip the `git clone` line and
`cd` into the project directory.

```bash
# Clone (or cd into your existing checkout)
git clone <repository-url> hr-policy-agent
cd hr-policy-agent

# Install the package and all dependencies in editable mode.
# The first run may take 2-3 minutes; subsequent runs are instant.
uv pip install -e .
```

**Verify the install:**

```bash
uv run python -c "import hr_agent; print(hr_agent.__file__)"
```

Expected output (path will differ):

```
D:\path\to\hr-policy-agent\src\hr_agent\__init__.py
```

If you see a `ModuleNotFoundError`, the editable install didn't take
effect. Re-run `uv pip install -e .` and check that you're in the repo
root (the folder with `pyproject.toml`).

---

## Step 3 — Create the `.env` file

The app reads all its configuration from a `.env` file at the repo root.
Copy the template and fill in your keys.

```bash
# Copy the template
cp .env.example .env
```

**Edit `.env`** with a text editor and set these three values:

```dotenv
# Required — get from https://console.groq.com/keys
GROQ_API_KEY=gsk_...

# Required — get from https://app.pinecone.io/
PINECONE_API_KEY=pcsk_...

# Any long random string; used to sign login tokens.
# Generate one with:  python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET=replace-me-with-a-random-string
```

Leave the rest as-is. **Leave `POSTGRES_DSN` blank** for now — we'll set
it in the next step.

> **Windows PowerShell** — if the `cp` command doesn't exist, use:
> ```powershell
> Copy-Item .env.example .env
> ```

**Generate a JWT secret** (optional but recommended):

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output into `JWT_SECRET=` in `.env`.

---

## Step 4 — Start Postgres in Docker

Postgres runs in a container. One command starts it, and it stays up
until you stop it.

```bash
docker compose up -d postgres
```

**Verify it's healthy:**

```bash
docker compose ps
```

Wait until the `STATUS` column shows `Up ... (healthy)`:

```
NAME                IMAGE         STATUS                    PORTS
hr-agent-postgres   postgres:16   Up 15 seconds (healthy)   0.0.0.0:5432->5432/tcp
```

If it shows `(health: starting)`, wait 5-10 more seconds and re-run
`docker compose ps`.

**If port 5432 is already in use** (another Postgres running on your
machine), Docker will either fail to bind or you'll connect to the wrong
database. Check:

```bash
# Windows (Git Bash / WSL)
netstat -ano | findstr :5432
```

If you see more than one PID listening on `0.0.0.0:5432`, stop the other
service or remap Docker's port. See
[docs/postgres.md](docs/postgres.md) for the fix.

**Now tell the app to use Postgres.** Edit `.env` and set:

```dotenv
POSTGRES_DSN=postgresql://hr_agent:hr_agent_dev@localhost:5432/hr_agent
```

Save the file. Don't start the API yet — we need to provision tables
first.

---

## Step 5 — Provision Postgres tables

The checkpointer and the long-term memory Store each need their own tables.
This is a one-time setup. The command is idempotent — safe to re-run.

```bash
uv run python scripts/init_postgres.py
```

Expected output:

```
Provisioning Postgres at postgresql://hr_agent:***@localhost:5432/hr_agent
  checkpointer tables: ok
  store tables: ok

Done. Postgres is ready.
```

**If you see `psycopg cannot use ProactorEventLoop`** on Windows, this is
a known issue. It's fixed by the launcher script we use in the next step;
if it appears here, see the [Troubleshooting](#troubleshooting) section.

**Verify the tables exist:**

```bash
docker compose exec postgres psql -U hr_agent -d hr_agent -c "\dt"
```

Expected: at least `checkpoints`, `checkpoint_blobs`, `checkpoint_writes`,
and `store`.

---

## Step 6 — Ingest the HR policy into Pinecone

The agent answers from a Pinecone index that must be populated with the
HR policy content. If the person setting up this project is **you**, the
index is already populated and you can skip this step. If it's a **new
machine** and you have the source PDF, run:

```bash
# Create the data folders
mkdir -p data/raw data/processed

# Place the source PDF (or markdown) into data/
# If you have the PDF:
cp /path/to/GESCI_HRPPM_2018.pdf data/raw/hr_policy.pdf

# If you already have the markdown file:
cp /path/to/hr_policy.md data/processed/hr_policy.md

# Run the ingestion pipeline
uv run python -m hr_agent.ingest
```

Expected output:

```
[pipeline] source_doc_id = hr_policy-a1b2c3d4e5f6
[pipeline] 197 final chunks
[pipeline] validation: total_chunks=197 orphaned_headers=0 too_short=0 too_long=0 missing_breadcrumb=0
[pipeline] source_doc_id=hr_policy-a1b2c3d4e5f6 upserted=197 deleted_stale=0
```

**Verify the index:**

```bash
uv run scripts/pinecone_stats.py
```

Expected:

```
Index         : hr-policy-agent
Dimension     : 384
Total vectors : 197
Namespaces:
  - hr-policy-agent-namespace               197
```

**If the index is already populated** from a previous session (yours or a
teammate's), skip ingestion — you'll connect to the same Pinecone index
via the shared `PINECONE_API_KEY`.

Full ingestion details are in
[`docs/ingestion_guide.md`](docs/ingestion_guide.md).

---

## Step 7 — Start the API

Open a **new terminal** (leave the current one free) and run:

```bash
uv run python scripts/run_api.py
```

Leave this terminal running — it's the API server.

Expected startup log:

```
INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO    hr_agent.api: lifespan: starting
INFO    hr_agent.api: audit db initialised
Loading weights: 100%|...|
INFO    hr_agent.api: async graph compiled
INFO    hr_agent.api: lifespan: ready
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**The first startup takes ~15 seconds** because the embedding model loads
and the graph compiles. Subsequent starts are faster (the model is cached).

**Verify from another terminal:**

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

```bash
curl http://127.0.0.1:8000/ready | python -m json.tool
```

Expected:

```json
{
  "status": "ready",
  "checks": {
    "store": true,
    "pinecone_config": true,
    "groq_config": true
  },
  "details": {}
}
```

If `status` is `degraded`, the `details` field explains which check
failed — usually a missing API key in `.env`.

---

## Step 8 — Start the Streamlit UI

Open a **third terminal** and run:

```bash
uv run streamlit run ui/app.py
```

Expected output:

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Streamlit opens the browser automatically. If it doesn't, open
`http://localhost:8501` manually.

**You now have three terminals running:**
1. **API** — `uv run python scripts/run_api.py` (leave running).
2. **UI** — `uv run streamlit run ui/app.py` (leave running).
3. **Free** — for any commands you want to run.

Postgres runs in the background as a Docker container.

---

## Step 9 — Log in and ask a question

In the Streamlit UI at `http://localhost:8501`:

1. **Log in** with one of the demo users:
   - Username: `tipto` — Password: `demo`
   - Username: `alice` — Password: `demo`
   - Username: `bob` — Password: `demo`

   (Demo credentials are documented in `configs/users.yaml`.)

2. **Ask a question** in the chat box, for example:
   - *"What is the probation period?"*
   - *"Should an employee have a Skype account?"*
   - *"What are the duties and obligations of GESCI?"*

3. **Watch the streaming response.** The sidebar shows per-node progress
   (guard_input → load_context → … → persist). The final answer appears
   with citations from the HR policy manual.

4. **Test memory:**
   - Ask a follow-up: *"What about their reporting timelines?"* — the
     rewriter should resolve "their" using the previous turn.
   - Open a new tab, log in as `alice`, and confirm no chat history leaks
     from `tipto`'s session.

5. **Rate the answer** with the thumbs up/down buttons. The feedback is
   stored in the audit DB and readable via `uv run scripts/feedback_stats.py`.

---

## Daily workflow after setup

Once everything is running, the daily loop is:

```bash
# 1. Start Postgres (if not already running)
docker compose up -d postgres

# 2. Start the API
uv run python scripts/run_api.py

# 3. In another terminal, start the UI
uv run streamlit run ui/app.py
```

**Stop everything:**

```bash
# Ctrl+C in the API and UI terminals
# Then stop Postgres (data is preserved):
docker compose stop postgres
```

**Resume later:**

```bash
docker compose start postgres
uv run python scripts/run_api.py
uv run streamlit run ui/app.py
```

The Postgres volume persists between restarts — chat history and
preferences survive.

---

## Alternative: run everything in Docker

If you'd rather containerize the API too (Postgres and API in Docker,
Streamlit and Ollama on the host):

```bash
# Build and start both containers
docker compose up -d

# Verify
docker compose ps
docker compose logs -f api

# When ready
curl http://localhost:8000/health
```

Then run the UI on the host as before:

```bash
uv run streamlit run ui/app.py
```

`docker-compose.yml` sets `POSTGRES_DSN` to use the `postgres` service
hostname internally, so you don't need to set it in `.env` when running
containerized. See [`docs/docker.md`](docs/docker.md) for the full
container guide.

---

## Troubleshooting

### `uv: command not found`

Install `uv` from [docs.astral.sh/uv](https://docs.astral.sh/uv/).
On Windows PowerShell:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### `ModuleNotFoundError: No module named 'hr_agent'`

You're not in the repo root, or the editable install didn't take effect.

```bash
# Confirm you're in the right place
pwd
ls pyproject.toml

# Reinstall
uv pip install -e .
```

### `docker: command not found` or `Cannot connect to the Docker daemon`

Docker Desktop isn't running. Launch it from your applications menu and
wait for the tray icon to turn green.

### `POSTGRES_DSN is empty` when starting the API

You skipped Step 4. Set `POSTGRES_DSN` in `.env`:

```dotenv
POSTGRES_DSN=postgresql://hr_agent:hr_agent_dev@localhost:5432/hr_agent
```

### `psycopg cannot use the 'ProactorEventLoop'` (Windows only)

This is a Windows-specific issue with `psycopg3`. The launcher script
`scripts/run_api.py` handles it automatically. If you see this error:

- **In `scripts/init_postgres.py`** — you may need to run it through the
  same launcher pattern. See [docs/postgres.md](docs/postgres.md).
- **In the API startup** — you're not using `scripts/run_api.py`. Always
  start the API with `uv run python scripts/run_api.py`, not with
  `uvicorn` directly.

### `password authentication failed for user "hr_agent"`

Two common causes:

1. **A native Windows Postgres is running on port 5432** and intercepting
   your connections. Check:

   ```bash
   netstat -ano | findstr :5432
   ```

   If two different PIDs are listening, stop the native service (see
   `docs/postgres.md`) or remap Docker's port to 5433.

2. **The Postgres volume was initialized with a different password.**
   Wipe it and start fresh:

   ```bash
   docker compose down -v
   docker compose up -d postgres
   # wait for healthy
   uv run python scripts/init_postgres.py
   ```

   The `-v` flag wipes volumes. Only do this if you have no data you care
   about (e.g., on first setup).

### `PoolTimeout: pool initialization incomplete after 10.0 sec`

Usually a downstream symptom of the auth failure above. Fix the auth
issue first.

### `GROQ_API_KEY is not set` at API startup

You didn't set `GROQ_API_KEY` in `.env`. Get a key from
[console.groq.com/keys](https://console.groq.com/keys), add it, and
restart the API.

### `PINECONE_API_KEY is not set` at API startup

Same as above, with a Pinecone key. Free tier at
[app.pinecone.io](https://app.pinecone.io/).

### UI shows "API unreachable"

The sidebar in the Streamlit UI shows a red indicator if it can't reach
the API. Check:

1. Is the API running? Look at its terminal.
2. Does `curl http://127.0.0.1:8000/health` work from another terminal?
3. Is `API_URL` set differently? By default the UI uses
   `http://127.0.0.1:8000`. If your API is elsewhere, set the env var
   before starting Streamlit:
   ```bash
   API_URL=http://192.168.1.10:8000 uv run streamlit run ui/app.py
   ```

### Slow first response

The first question after API startup takes 15-30 seconds because:

1. The embedding model loads (~5s).
2. The graph compiles and connects to Postgres (~5s).
3. The first LLM call warms up the Groq client.

Subsequent questions are 3-8 seconds depending on the number of nodes
visited.

### Chat history doesn't persist across restart

You're likely running with SQLite instead of Postgres. Verify:

```bash
uv run python -c "
from hr_agent.core.settings import get_settings
print('postgres mode:', get_settings().uses_postgres)
print('dsn:', get_settings().postgres_dsn)
"
```

If `postgres mode: False`, `POSTGRES_DSN` isn't set in `.env`.

---

## Quick reference — all commands

For copy-paste convenience, here's the complete setup in one block:

```bash
# 0. prerequisites
python --version && uv --version && docker --version

# 1. clone and install
git clone <repository-url> hr-policy-agent
cd hr-policy-agent
uv pip install -e .

# 2. configure
cp .env.example .env
# edit .env: set GROQ_API_KEY, PINECONE_API_KEY, JWT_SECRET,
#            POSTGRES_DSN=postgresql://hr_agent:hr_agent_dev@localhost:5432/hr_agent

# 3. start Postgres
docker compose up -d postgres

# 4. provision tables
uv run python scripts/init_postgres.py

# 5. ingest (only if the index isn't already populated)
mkdir -p data/raw data/processed
cp /path/to/hr_policy.md data/processed/hr_policy.md
uv run python -m hr_agent.ingest

# 6. start the API (Terminal A — leave running)
uv run python scripts/run_api.py

# 7. start the UI (Terminal B — leave running)
uv run streamlit run ui/app.py

# 8. open http://localhost:8501 and log in with tipto / demo
```

---

## What to do next

Once the stack is running:

- **Explore the docs:** [`docs/`](docs/) has deeper material on
  architecture, ingestion, Postgres, and Docker.
- **Read the evaluation guide:** [README → Evaluation](README.md#evaluation)
  explains how to run the retrieval eval.
- **Try the CLI tools:** `scripts/pinecone_stats.py`,
  `scripts/audit_stats.py`, `scripts/feedback_stats.py`.
- **Check the API:** visit `http://localhost:8000/docs` for the
  interactive OpenAPI spec.

If something doesn't work and the troubleshooting section doesn't cover
it, check the API logs (the terminal where `run_api.py` is running) and
the Docker logs (`docker compose logs postgres`). Those two almost always
contain the answer.