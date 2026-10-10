from __future__ import annotations

import asyncio
import sys

import uvicorn
from hr_agent.api.config import get_api_settings

def main() -> None:
    api_settings = get_api_settings()
    config = uvicorn.Config(
        "hr_agent.api.app:app",
        host = api_settings.api_host,
        port = api_settings.api_port,
        reload = api_settings.api_reload, 
        loop="asyncio",     
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