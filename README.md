# HR Policy Agent

A version-aware, self-reflective retrieval-augmented generation (RAG) system
for HR policy documents, built on LangGraph, Pinecone, and Groq/Ollama.

The agent answers questions about an organization's HR policy manual with
clause-level citations, resolves conversational follow-ups using chat history,
persists short-term and long-term memory across restarts, and falls back to
abstention when the policy is silent — rather than hallucinating.

---

## Table of contents

- [What this project does](#what-this-project-does)
- [Architecture](#architecture)
- [Repository structure](#repository-structure)
- [Quickstart](#quickstart)
- [Running the stack](#running-the-stack)
  - [Native development](#native-development)
  - [Containerized backend](#containerized-backend)
- [Configuration](#configuration)
- [Ingestion](#ingestion)
- [Evaluation](#evaluation)
- [Testing](#testing)
- [Observability](#observability)
- [Deployment modes](#deployment-modes)
- [Design decisions](#design-decisions)
- [Roadmap](#roadmap)
- [Documentation index](#documentation-index)
- [License](#license)

---

## What this project does

Given a question about an HR policy manual, the agent:

1. **Guards the input** — detects prompt injection, checks scope, masks
   Bangladesh-specific PII (email, phone, NID), and identifies sensitive
   cases ("my grievance", "my termination").
2. **Resolves conversational references** — a follow-up like "What about
   their reporting timelines?" is rewritten to a standalone question using
   the chat history before the first retrieval attempt.
3. **Retrieves evidence** — Pinecone hybrid search over chunked policy text
   with breadcrumb metadata (Section > SubSection > SubSubSection).
4. **Grades the evidence** — an LLM grader classifies the retrieved context
   as `good` or `weak` before generation.
5. **Generates an answer** — with `[Source: Section X.Y.Z]` citations, a
   version note when multiple versions match, and a "policy information,
   not legal advice" disclaimer.
6. **Guards the output** — deterministic checks (citation presence) plus an
   LLM groundedness check; falls back to a refusal template when the answer
   is not supported.
7. **Persists memory** — short-term chat history via LangGraph's checkpointer
   (SQLite or Postgres), long-term preferences via LangGraph's Store
   (InMemory or Postgres).
8. **Writes an audit row** — request id, hashed user id, guard verdict,
   source used, and node-by-node trace, queryable via a CLI tool.

The project is deliberately **closed-domain**: when the policy does not
answer the question, the agent abstains instead of reaching for the open web.

---

## Architecture

```
                        ┌──────────────────────┐
                        │   Streamlit UI       │
                        │   (native, :8501)    │
                        └───────────┬──────────┘
                                    │ HTTP / SSE
                                    ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI service (:8000)                    │
│   /auth/login   /chat   /chat/stream   /memory   /feedback    │
│   /health       /ready                                        │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
        ┌───────────────────────────────────────┐
        │         LangGraph agent               │
        │                                       │
        │  guard_input                          │
        │     ├─► load_context  (memory read)   │
        │     ├─► contextualize_query           │
        │     ├─► route_question                │
        │     │       ├─► retrieve_kb_docs      │
        │     │       │       └─► grade_kb      │
        │     │       │              ├─ good ►  │
        │     │       │              └─ weak ►  │
        │     │       │                   abstain│
        │     │       └─► direct_answer         │
        │     └─► refuse / sensitive_case       │
        │                                       │
        │  generate_from_kb                     │
        │     └─► summarize_history             │
        │            └─► guard_output           │
        │                    └─► persist        │
        │                          (memory write,│
        │                           audit row,   │
        │                           usage log)   │
        └───────┬───────────────────┬───────────┘
                │                   │
     ┌──────────┴───────┐     ┌─────┴──────┐
     │  Checkpointer    │     │   Store    │
     │  (short-term)    │     │(long-term) │
     │  SQLite │ Postgres│    │InMem│PG    │
     └──────────────────┘     └────────────┘

              ┌─────────────────────────┐
              │   External services     │
              │   Pinecone (vectors)    │
              │   Groq (LLMs, primary)  │
              │   Ollama (LLMs, fallback)│
              └─────────────────────────┘
```

**Retrieval pipeline (offline, at ingestion):**

```
PDF ─► Markdown ─► header-aware chunking ─► validation
    ─► metadata enrichment (breadcrumb, source_doc_id)
    ─► HuggingFace embeddings (all-MiniLM-L6-v2, 384-dim)
    ─► Pinecone upsert with content-addressed IDs
```

**LLM layer:** every role (generator, router, scope, graders, rewriter,
memory extractor, summarizer) is configured in `configs/models.yaml` with
a primary provider and a fallback. Switching a role's provider is a YAML
edit — no code change.

---

## Repository structure

```
hr-policy-agent/
├── configs/
│   ├── chunking.yaml            # chunk sizes, thresholds, header regexes
│   ├── guardrails.yaml          # injection markers, PII config
│   ├── models.yaml              # role → provider+model, with fallbacks
│   └── users.yaml               # demo users (swap for real auth later)
├── data/
│   ├── raw/                     # original PDFs (git-ignored)
│   ├── processed/               # extracted markdown
│   ├── eval/                    # golden question sets
│   └── audit/                   # SQLite audit + feedback DB
├── docs/
│   ├── architecture.md
│   ├── ingestion_guide.md
│   ├── postgres.md
│   ├── docker.md
│   └── results.md               # evaluation output
├── notebooks/                   # exploratory notebooks (00–04)
├── scripts/
│   ├── run_api.py               # Windows-safe API launcher
│   ├── init_postgres.py         # one-time schema provisioning
│   ├── pinecone_stats.py        # index inspection
│   ├── audit_stats.py           # audit log summary
│   ├── feedback_stats.py        # thumbs up/down summary
│   ├── run_eval.py              # retrieval recall@k
│   └── show_llm_roles.py        # print resolved role→provider mapping
├── src/hr_agent/
│   ├── agent/                   # graph, state, nodes, prompts
│   ├── api/                     # FastAPI app, routes, auth, schemas
│   ├── audit/                   # SQLite audit + feedback writers
│   ├── core/                    # settings, config loaders
│   ├── evaluation/              # recall@k, golden-set loader
│   ├── guardrails/              # PII masking
│   ├── ingest/                  # chunking, embedding, indexing
│   ├── llm/                     # factory, registry, usage tracking
│   ├── memory/                  # profile adapter, Store, policy
│   ├── retrieval/               # retriever, query analysis
│   └── utils/                   # markdown helpers
├── tests/
│   ├── api/                     # auth, memory, feedback endpoints
│   └── integration/             # Postgres backend (skips without DSN)
├── ui/                          # Streamlit app
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── pyproject.toml
└── README.md
```

---

> **New to this project?** Start with
> [`START_THE_PROJECT.md`](docs/START_THE_PROJECT.md) — a step-by-step guide
> for running everything on a fresh machine.

## Quickstart

**Prerequisites:**

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker Desktop (for Postgres) — optional; SQLite works out of the box
- Groq API key
- Pinecone API key
- Ollama (optional, for local fallback)

**Five-minute happy path (SQLite, no Docker):**

```bash
# 1. install
uv pip install -e .

# 2. configure
cp .env.example .env
# edit .env: set GROQ_API_KEY, PINECONE_API_KEY, JWT_SECRET

# 3. ingest the HR policy (see docs/ingestion_guide.md for details)
mkdir -p data/raw data/processed
cp /path/to/hr_policy.md data/processed/hr_policy.md
uv run python -m hr_agent.ingest

# 4. start the API (SQLite-backed, no Postgres required)
uv run python scripts/run_api.py

# 5. (separate terminal) start the UI
uv run streamlit run ui/app.py
```

Open `http://localhost:8501`, log in with `tipto / demo`, and ask a question.

---

## Running the stack

### Native development

Fastest loop. No containers except Postgres (optional).

```bash
# Terminal 1 — Postgres in Docker (optional; SQLite works without it)
docker compose up -d postgres

# Terminal 2 — API on the host
uv run python scripts/run_api.py

# Terminal 3 — UI on the host
uv run streamlit run ui/app.py

# Terminal 4 — Ollama for local fallbacks (optional)
ollama serve
```

With `POSTGRES_DSN` set in `.env` (see [Configuration](#configuration)),
the API uses Postgres for both short-term and long-term memory. Leave it
empty to use SQLite + InMemory.

### Containerized backend

Postgres and the API in Docker; Streamlit and Ollama stay native.

```bash
# 1. build and start
docker compose up -d

# 2. watch it come up
docker compose ps
docker compose logs -f api

# 3. verify
curl http://localhost:8000/health
curl http://localhost:8000/ready | python -m json.tool

# 4. UI on the host, unchanged
uv run streamlit run ui/app.py
```

See [`docs/docker.md`](docs/docker.md) for the full container guide:
rebuild workflow, log viewing, volume reset, and switching between the
native and containerized backends.

### API endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/auth/login` | Exchange username/password for a JWT |
| `POST` | `/chat` | One turn, synchronous JSON |
| `POST` | `/chat/stream` | One turn, SSE, one event per node |
| `GET` | `/memory` | List current user's preference memories |
| `DELETE` | `/memory/{key}` | Forget a preference |
| `POST` | `/feedback` | Thumbs up/down, correlated to the audit row |
| `GET` | `/health` | Liveness |
| `GET` | `/ready` | Readiness with per-dependency checks |

Interactive docs at `http://localhost:8000/docs` when the API is running.

---

## Configuration

All runtime configuration is in `.env` (copy from `.env.example`). The
important keys:

| Variable | Purpose | Default |
|---|---|---|
| `GROQ_API_KEY` | Primary LLM provider | — |
| `PINECONE_API_KEY` | Vector store | — |
| `JWT_SECRET` | Signs API tokens | `dev-only-change-me` |
| `POSTGRES_DSN` | Empty → SQLite. Set → Postgres for both memory layers | empty |
| `API_HOST` / `API_PORT` | API bind address | `127.0.0.1` / `8000` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:8501` |
| `TAVILY_API_KEY` | Optional; web fallback is off by default | — |

**Two forms of `POSTGRES_DSN`:**

- Native (`API` on the host, Postgres in Docker):
  `postgresql://hr_agent:hr_agent_dev@localhost:5432/hr_agent`
- Compose (`API` and Postgres both in Docker):
  `postgresql://hr_agent:hr_agent_dev@postgres:5432/hr_agent`

`docker-compose.yml` sets the compose form automatically, so leave
`POSTGRES_DSN` blank in `.env` when running `docker compose up`.

**Chunking, guardrails, and models** are YAML-configured and live in
`configs/`. See [Ingestion](#ingestion) for chunking details, and
`configs/models.yaml` for the role→provider mapping.

---

## Ingestion

The full ingestion guide lives in
[`docs/ingestion_guide.md`](docs/ingestion_guide.md). Quick reference:

```bash
# 1. place the source markdown
mkdir -p data/raw data/processed
cp /path/to/hr_policy.md data/processed/hr_policy.md

# 2. run the pipeline
uv run python -m hr_agent.ingest

# 3. verify
uv run scripts/pinecone_stats.py
uv run python -m hr_agent.retrieval.retrieve
```

Expected output from the pipeline:

```
[pipeline] source_doc_id = hr_policy-a1b2c3d4e5f6
[pipeline] 197 final chunks
[pipeline] validation: total_chunks=197 orphaned_headers=0 too_short=0 too_long=0 missing_breadcrumb=0
[pipeline] source_doc_id=hr_policy-a1b2c3d4e5f6 upserted=197 deleted_stale=0
```

The ingestion is **idempotent and diff-aware**: re-running with the same
input overwrites the same vectors; editing the source replaces changed
chunks and deletes stale ones. You never need to manually delete the
namespace or recreate the index.

---

## Evaluation

Evaluation is a first-class part of the project, not an afterthought.
Every change to chunking, retrieval, prompting, or model choice should be
measurable against a frozen golden set.

### Datasets

| File | Purpose | Count |
|---|---|---|
| `data/eval/golden_dev.jsonl` | Iteration set; changes between experiments | ~40 (growing to ~130) |
| `data/eval/golden_test.jsonl` | Frozen; only run at milestones | TBD |
| `data/eval/seed_questions.jsonl` | Hand-written seed set from initial PDF audit | ~11 |

Each line is a JSON object:

```json
{"question": "...", "expected_breadcrumb_contains": "..."}
```

A question counts as a **hit** if any of the top-k retrieved chunks has a
`breadcrumb` metadata field containing `expected_breadcrumb_contains`
(case-insensitive substring match). Deliberately loose — exact string
matching would be brittle to minor heading-text differences.

### Retrieval evaluation

```bash
uv run scripts/run_eval.py --k 5
uv run scripts/run_eval.py --k 5 --dataset data/eval/golden_dev.jsonl
```

Expected output:

```
[HIT ] What step on the salary scale does a new employee normally start at?
       expected_contains: '4.2.1 Salary policy'
       retrieved: ['4 REMUNERATION AND BENEFITS > 4.2 Salary structure > 4.2.1 Salary policy on appointment and promotion', ...]
...
--------------------------------------------------------------------------------
recall@5 = 81.82% (9/11)
```

To compare configurations, vary `--k`:

```bash
for k in 3 5 10; do
  uv run scripts/run_eval.py --k $k | tail -1
done
```

### Evaluation strategy

The full evaluation plan (from the project spec) covers:

| Category | Count (target) | Purpose |
|---|---|---|
| Single-clause lookup | 30 | Basic retrieval + citation |
| Table lookup (grade × item) | 20 | Deterministic tool correctness |
| Multi-clause synthesis | 15 | Reasoning across sections |
| Calculations (per diem, PF) | 10 | Arithmetic correctness |
| Temporal / versioning | 15 | `as_of` correctness |
| Multi-turn / follow-up | 10 | History-aware rewriting |
| Unanswerable / out-of-scope | 15 | Abstention precision |
| Adversarial / injection | 15 | Guardrail effectiveness |
| Bangla / Banglish | 20 | Multilingual robustness |

**Metrics reported:**

- **Retrieval**: Recall@k, MRR, context precision vs. gold clause ids.
- **Generation**: answer correctness (exact match for numbers, LLM judge
  for prose), faithfulness (claim-level), citation precision/recall.
- **Behavior**: abstention precision/recall, escalation accuracy.
- **System**: latency p50/p95, LLM calls per query, tokens.
- **Safety**: attack success rate, false-positive rate on benign inputs.

**Rigor:**

- **Judge validation** against 30–40 hand-labeled answers before trusting
  any LLM-judged metric.
- **Ablations**: sparse-only / dense-only / hybrid; ± reranker; chunking
  variants; ± CRAG grading; ± reflection; guardrails on/off.
- **Bootstrap confidence intervals** on all headline numbers.
- **Results frozen** to `docs/results.md` with model, prompt, and config
  hashes for reproducibility.

### Running the full evaluation (when the harness is complete)

```bash
uv run python -m hr_agent.evaluation.runner \
  --dataset data/eval/golden_test.jsonl \
  --k 5 \
  --output docs/results.md
```

Not yet implemented; tracked in the roadmap.

---

## Testing

```bash
# All tests
uv run pytest tests/ -v

# API tests only
uv run pytest tests/api/ -v

# Postgres integration (skips automatically if POSTGRES_DSN is unset)
uv run pytest tests/integration/ -v
```

The API test suite (11 tests) covers:

- Login success, bad password, unknown user.
- Protected routes: missing token, expired token, valid token.
- Memory CRUD: list, delete, per-user isolation.
- Feedback: submit, requires auth, rejects invalid thumb.

Postgres integration tests use the real backend when `POSTGRES_DSN` is
set; otherwise they're skipped, so SQLite-only runs are unaffected.

---

## Observability

Three CLI tools give you a window into what the system is doing:

**Pinecone index state:**

```bash
uv run scripts/pinecone_stats.py
```

Prints total vector count, per-namespace counts, and per-`source_doc_id`
counts (useful for detecting stale vectors after re-ingestion).

**Audit log:**

```bash
uv run scripts/audit_stats.py
```

Prints total queries, blocked count, sensitive-case count, top sources,
and the most recent rows with verdict and source.

**Feedback summary:**

```bash
uv run scripts/feedback_stats.py
```

Prints thumbs-up/down totals, approval ratio, and recent feedback rows
with the correlated `request_id`.

**LLM role mapping:**

```bash
uv run scripts/show_llm_roles.py
```

Prints each role's resolved provider, model, timeout, and fallback target.
Use this after editing `configs/models.yaml` to confirm the change took
effect.

Every `/chat` response also carries `retrieved_breadcrumbs` and
`evidence_grade`, so a single JSON blob tells you what was retrieved, what
the grader said, and whether the output guard accepted the answer.

---

## Deployment modes

| Layer | Native dev | Containerized backend |
|---|---|---|
| Postgres | `docker compose up -d postgres` | same |
| API | `uv run python scripts/run_api.py` | `docker compose up -d api` |
| Streamlit UI | `uv run streamlit run ui/app.py` | same (native) |
| Ollama | `ollama serve` | same (native) |
| Memory backend | SQLite or Postgres (DSN) | Postgres (DSN set by compose) |
| Config files | `configs/*.yaml` on host | mounted read-only from host |
| Embedding cache | `~/.cache/huggingface` | `hf_cache` volume |

Both modes use the same Python code. Switching is a command change, not a
code change. See [`docs/docker.md`](docs/docker.md) and
[`docs/postgres.md`](docs/postgres.md).

---

## Design decisions

**Closed-domain by default.** The web fallback is off. When the policy is
silent, the agent abstains rather than reaching for the open web. This is
the correct behavior for a compliance-adjacent HR tool where "confidently
wrong" is worse than "I don't know".

**Additive infrastructure changes.** Postgres, Docker, and the multi-provider
LLM layer were all added without rewriting existing code. Each has a default
(SQLite, native processes, Groq) and an alternative (Postgres, containers,
Ollama) selected by config. Nothing that worked at the start of a session
stops working at the end.

**Config over code.** Chunking thresholds, guardrail patterns, model
choices, and prompt text are in `configs/*.yaml`. Editing them takes effect
without touching Python. Where a runtime cache is unavoidable (models,
chunking), a `cache_clear()` hook lets long-lived processes pick up edits.

**One file per concern.** Nodes, prompts, LLM construction, memory writes,
and audit writes each live in their own module. `routes/chat.py` builds
responses; `nodes/persist.py` writes memory and audit; `llm/factory.py`
resolves roles. If a change touches two concerns, that's a signal the
abstraction is wrong.

**Determinism where it matters.** Chunk IDs are content-addressed (same
content → same ID → upsert overwrites). Postgres and SQLite are
interchangeable. Audit rows use hashed user ids, not raw identifiers.

**Testability by injection.** Every node that needs an LLM or a retriever
receives it as an argument. Tests pass mocks. The graph can be built in
isolation.

---

## Roadmap

Beyond the current state, the following are planned:

| # | Feature | Phase |
|---|---|---|
| 1 | Answer-guard fix for false citation rejections | 9 |
| 2 | Table lookup + calculator tools | 8 |
| 3 | `as_of` version resolution + document registry + canonical keys | 3, 6 |
| 4 | Injection classifier + retrieval-side framing + red-team suite | 10 |
| 5 | Golden set expansion to ~130 questions with frozen test split | 7, 12 |
| 6 | Full evaluation runner with ablations and CIs | 12 |
| 7 | Bangla + English multilingual support | 14 |
| 8 | Real password auth (swap demo users for bcrypt + users table) | 13 |
| 9 | Production deployment (Linux host, GPU passthrough for Ollama) | 13 |

---

## Documentation index

- [`docs/ingestion_guide.md`](docs/ingestion_guide.md) — full ingestion walkthrough
- [`docs/postgres.md`](docs/postgres.md) — Postgres setup, switching backends, troubleshooting
- [`docs/docker.md`](docs/docker.md) — container build, run, and reset
- [`docs/architecture.md`](docs/architecture.md) — deeper architecture notes
- [`docs/results.md`](docs/results.md) — evaluation output (populated by eval runs)

---

## License

See `LICENSE` at the repository root.