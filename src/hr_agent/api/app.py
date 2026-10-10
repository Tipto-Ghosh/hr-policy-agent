# src/hr_agent/api/app.py
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hr_agent.agent.checkpoint import (
    close_async_checkpointer,
    get_async_checkpointer,
)
from hr_agent.agent.graph import compile_graph_async
from hr_agent.api.config import get_api_settings
from hr_agent.api.dependencies import _get_graph_deps
from hr_agent.api.middleware import RequestIDMiddleware
from hr_agent.api.routes.chat import router as chat_router
from hr_agent.api.routes.health import router as health_router
from hr_agent.audit.db import init_db as init_audit_db

from hr_agent.api.routes.auth import router as auth_router
from hr_agent.api.routes.feedback import router as feedback_router
from hr_agent.api.routes.memory import router as memory_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)
# Reduce Hugging Face network chatter at startup.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logger = logging.getLogger("hr_agent.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("lifespan: starting")

    # ---- audit DB ----
    try:
        init_audit_db()
        logger.info("audit db initialised")
    except Exception as e:
        logger.warning("audit db init failed: %s", e)
        raise

    # ---- async graph ----
    try:
        deps = _get_graph_deps()
        checkpointer = await get_async_checkpointer()
        app.state.graph = compile_graph_async(deps, checkpointer=checkpointer)
        logger.info("async graph compiled")
    except Exception as e:
        logger.exception("graph warmup failed")
        raise

    logger.info("lifespan: ready")
    yield

    logger.info("lifespan: shutting down")
    try:
        await close_async_checkpointer()
    except Exception as e:
        logger.warning("checkpointer close failed: %s", e)


def create_app() -> FastAPI:
    api_settings = get_api_settings()
    app = FastAPI(
        title="HR Policy Agent",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(auth_router)
    app.include_router(feedback_router)
    app.include_router(memory_router)
    return app


app = create_app()