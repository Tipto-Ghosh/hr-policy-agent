"""
Windows-safe uvicorn entrypoint.

Must set the asyncio event loop policy BEFORE uvicorn creates its loop,
because psycopg3's async mode refuses ProactorEventLoop on Windows.

Run from the repo root:
    uv run python -m hr_agent.api
"""
from __future__ import annotations

import asyncio
import sys


def main() -> None:
    if sys.platform == "win32":
        # psycopg3 async + ProactorEventLoop = incompatible.
        # Must run before uvicorn creates the loop.
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    import uvicorn

    from hr_agent.api.config import get_api_settings

    settings = get_api_settings()
    uvicorn.run(
        "hr_agent.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )


if __name__ == "__main__":
    main()