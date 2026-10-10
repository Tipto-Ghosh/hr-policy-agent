from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from hr_agent.api.auth import AuthUser, current_user
from hr_agent.api.schemas import FeedbackRequest, FeedbackResponse
from hr_agent.audit.writers import read_feedback, write_feedback

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    req: FeedbackRequest,
    user: AuthUser = Depends(current_user),
) -> FeedbackResponse:
    try:
        fid = write_feedback(
            request_id=req.request_id,
            user_id_hash=_user_hash(user.user_id),
            thumb=req.thumb,
            reason=req.reason,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"feedback write failed: {type(e).__name__}: {e}",
        )
    rows = [r for r in read_feedback(limit=1) if r["id"] == fid]
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="feedback written but not readable back",
        )
    return FeedbackResponse(**rows[0])


def _user_hash(user_id: str) -> str:
    import hashlib
    return hashlib.sha256(user_id.encode()).hexdigest()