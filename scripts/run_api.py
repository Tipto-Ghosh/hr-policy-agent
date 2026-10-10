from __future__ import annotations

import asyncio
import sys

import uvicorn


def main() -> None:
    config = uvicorn.Config(
        "hr_agent.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,        # reload spawns subprocesses; see note below
        loop="asyncio",      # explicit: don't let uvicorn pick uvloop
        log_level="info",
    )
    server = uvicorn.Server(config)

    if sys.platform == "win32":
        # Create a SelectorEventLoop directly. This is what psycopg3 wants.
        # `asyncio.run` with loop_factory (3.12+) is nicer, but we're on 3.11,
        # so do it manually.
        loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(server.serve())
        finally:
            loop.close()
    else:
        asyncio.run(server.serve())


if __name__ == "__main__":
    main()