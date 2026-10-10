"""
JWT-based auth for the HR Policy Agent API.

For this iteration, credentials live in configs/users.yaml and passwords
are plain-text (clearly marked demo-only). When this project moves to a
real user store, only `_load_users()` and `_verify_credentials()` change
the token, dependency, and route plumbing stay identical.

Two public entry points:
  - create_access_token(user_id) -> str (called by /auth/login)
  - current_user (dependency)  -> AuthUser (called by every protected route)
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import jwt
import yaml
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from hr_agent.api.config import get_api_settings

__all__ = [
    "AuthUser",
    "create_access_token",
    "current_user",
    "authenticate",
]

# user loading
@dataclass(frozen = True)
class _DemoUser:
    username: str
    password: str
    user_id: str 
    

@lru_cache()
def _load_users() -> dict[str, _DemoUser]:
    """Load users from configs/users.yaml (demo-only)."""
    
    cfg = get_api_settings()
    path = cfg.users_config_path
    
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
        
    users: dict[str, _DemoUser] = {}
    for entry in raw.get("users", []):
        user = _DemoUser(
            username = entry["username"],
            password = entry["password"],
            user_id = entry["user_id"],
        )
        users[user.username] = user
    return users


def authenticate(username: str, password: str) -> _DemoUser | None:
    """Check credentials against the demo user store."""
    user = _load_users().get(username)
    if user is None:
        return None
    
    if user.password != password:
        return None
    
    return user


# JWT
def create_access_token(user_id: str) -> str:
    settings = get_api_settings()
    now = datetime.now(tz = timezone.utc)
    payload: dict[str, Any] = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expiry_minutes)).timestamp()),
    }  
    
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def _decode_token(token: str) -> dict[str, Any]:
    settings = get_api_settings()
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# FastAPI dependency 
_bearer = HTTPBearer(auto_error=False)

@dataclass(frozen=True)
class AuthUser:
    user_id: str
    request_id: str
    
    
def current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser:
    """
    FastAPI dependency. Reads Authorization: Bearer <token>, verifies it,
    returns the authenticated user. Raises 401 if missing or invalid.
    """
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = _decode_token(creds.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    request_id = getattr(request.state, "request_id", "")
    return AuthUser(user_id=user_id, request_id=request_id)