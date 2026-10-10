from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, HTTPException, status

from hr_agent.api.auth import current_user, AuthUser
from hr_agent.api.schemas import MemoryItem, MemoryListResponse
from hr_agent.memory.store import get_store, preference_namespace

router = APIRouter(
    prefix="/memory",
    tags=["memory"],
)

def _user_hash(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()


@router.get("", response_model=MemoryListResponse)
async def list_memory(user: AuthUser = Depends(current_user)) -> MemoryListResponse:
    """List the authenticated user's stored preference memories."""
    user_id_hash = _user_hash(user.user_id)
    ns = preference_namespace(user_id_hash)
    store = get_store()
    try:
        items = store.search(ns, query="", limit=200)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"store error: {type(e).__name__}: {e}",
        )
    return MemoryListResponse(
        user_id_hash=user_id_hash,
        items=[MemoryItem(key=it.key, value=str(it.value)) for it in items],
    )
    
    
@router.delete("/{key}")
async def delete_memory(
    key: str,
    user: AuthUser = Depends(current_user),
) -> dict:
    """
    Forget one preference. Idempotent: returns 200 even if the key didn't
    exist, so the UI can call this safely without a prior GET.
    """
    user_id_hash = _user_hash(user.user_id)
    ns = preference_namespace(user_id_hash)
    store = get_store()
    try:
        store.delete(ns, key=key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"store error: {type(e).__name__}: {e}",
        )
    return {"deleted": key}