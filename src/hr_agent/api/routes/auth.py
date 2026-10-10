from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from hr_agent.api.auth import authenticate, create_access_token
from hr_agent.api.config import get_api_settings
from hr_agent.api.schemas import LoginRequest, LoginResponse

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest) -> LoginResponse:
    """
    Exchange username/password for a JWT. Returns 401 for both unknown
    user and wrong password — the two cases are indistinguishable to
    the caller by design.
    """
    user = authenticate(req.username, req.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.user_id)
    settings = get_api_settings()
    return LoginResponse(
        access_token=token,
        expires_in=settings.jwt_expiry_minutes * 60,
        user_id=user.user_id,
    )