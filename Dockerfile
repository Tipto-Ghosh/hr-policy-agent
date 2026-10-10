# Dockerfile
#
# Multi-stage build for the HR Policy Agent API.
#
# Stage 1 (builder): resolve and install dependencies into a venv using uv.
# Stage 2 (runtime): copy the venv and src/ into a slim base image.
#
# The container runs `scripts/run_api.py` — the same launcher used natively.
# `configs/` is mounted at runtime (see docker-compose.yml), so tuning YAML
# does not require an image rebuild.
#
# Build:
#     docker compose build api
#     # or
#     docker build -t hr-policy-agent-api .
#
# Run (compose is preferred):
#     docker compose up -d api

# ---------- stage 1: builder ----------
FROM python:3.11-slim AS builder

# uv is the package manager used by the project. Install it once.
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Copy lock + pyproject first so a code change does not invalidate the
# dependency layer.
COPY pyproject.toml uv.lock ./

# Install dependencies into a project-local venv. --frozen pins to uv.lock.
# --no-install-project installs only deps, not the package itself, so the
# layer is cached even when src/ changes.
RUN uv sync --frozen --no-install-project --no-dev

# Now copy the source and install the package itself (editable not needed
# in the image; a non-editable install is smaller and reproducible).
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY ui/ ./ui/
RUN uv sync --frozen --no-dev

# ---------- stage 2: runtime ----------
FROM python:3.11-slim AS runtime

# Non-root user for the runtime. Matches the style of most base images.
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --shell /bin/bash --create-home app

# Minimal runtime deps: libpq is required by psycopg (binary wheel bundles
# most of it, but libpq5 makes the runtime self-contained for edge cases).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the venv and the code from the builder.
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/src /app/src
COPY --from=builder --chown=app:app /app/scripts /app/scripts
COPY --from=builder --chown=app:app /app/ui /app/ui
COPY --from=builder --chown=app:app /app/pyproject.toml /app/uv.lock ./

# Activate the venv.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Cache locations. The embedding model lands in /app/.cache/huggingface;
# a named volume in compose keeps it across restarts.
ENV HF_HOME=/app/.cache/huggingface
RUN mkdir -p /app/.cache/huggingface && chown -R app:app /app/.cache

USER app

# The API listens on this port. The value of API_HOST (set by compose to
# 0.0.0.0) determines the bind address; this EXPOSE is informational.
EXPOSE 8000

# scripts/run_api.py reads API_HOST/API_PORT/API_RELOAD from settings and
# creates the SelectorEventLoop on Windows (no-op on Linux, where the
# default loop is already compatible with psycopg3).
CMD ["python", "scripts/run_api.py"]