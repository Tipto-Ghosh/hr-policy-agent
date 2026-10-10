"""
Provision the Postgres tables used by the checkpointer and the long-term
Store. Idempotent — safe to run more than once.

Usage:
    uv run python scripts/init_postgres.py

Requires POSTGRES_DSN to be set in .env, and the database to be reachable
(e.g., `docker compose up -d postgres`).
"""
from __future__ import annotations

import asyncio
import sys

from hr_agent.core.settings import get_settings


async def _init_checkpointer() -> None:
    from hr_agent.agent.checkpoint_postgres import init_postgres_checkpointer
    await init_postgres_checkpointer()
    print("  checkpointer tables: ok")


def _init_store() -> None:
    from hr_agent.memory.store_postgres import init_postgres_store
    init_postgres_store()
    print("  store tables: ok")


async def main() -> None:
    settings = get_settings()

    if not settings.postgres_dsn:
        print(
            "POSTGRES_DSN is empty. Set it in .env before running this script.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Print the DSN with the password masked, so the log is safe to share.
    safe_dsn = settings.postgres_dsn
    if "@" in safe_dsn and "://" in safe_dsn:
        scheme, rest = safe_dsn.split("://", 1)
        creds, host = rest.split("@", 1)
        if ":" in creds:
            user, _ = creds.split(":", 1)
            safe_dsn = f"{scheme}://{user}:***@{host}"

    print(f"Provisioning Postgres at {safe_dsn}")

    await _init_checkpointer()
    _init_store()

    print("\nDone. Postgres is ready.")


def _run() -> None:
    if sys.platform == "win32":
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())


if __name__ == "__main__":
    _run()