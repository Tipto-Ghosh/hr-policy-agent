from __future__ import annotations
from fastapi import APIRouter

from hr_agent.api.schemas import HealthResponse, ReadyResponse
from hr_agent.core.settings import get_settings
from hr_agent.memory.store import get_store


router = APIRouter(
    tags = ["health"]
)

@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse()

@router.get("/ready", response_model=ReadyResponse)
async def ready() -> ReadyResponse:
    """ 
    Readiness: check each external dependency. Returns 'degraded' when
    any dependency is unreachable, so orchestrators can decide whether to route
    traffic to this instance or not.
    """
    settings = get_settings()
    checks: dict[str, bool] = {}
    details: dict[str, str] = {}
    
    # store check
    try:
        store = get_store()
        store.search(("users", "_probe", "preferences"), query = "", limit = 1)
        checks["store"] = True
    except Exception as e:
        checks["store"] = False
        details["store"] = f"{type(e).__name__}: {e}"
    
    # check pinecone
    try:
        if settings.pinecone_api_key:
            checks["pinecone_config"] = True
        else:
            checks["pinecone_config"] = False
            details["pinecone_config"] = "Pinecone API key is not set."
    except Exception as e:
        checks["pinecone_config"] = False
        details["pinecone_config"] = f"{type(e).__name__}: {e}"
    
    # llm provider check
    checks["groq_config"] = bool(settings.groq_api_key)
    if not settings.groq_api_key:
        details["groq_config"] = "Groq API key is not set."
        
    all_ok = all(checks.values())
    return ReadyResponse(
        status = "ready" if all_ok else "degraded",
        check = checks,
        details = details,
    )