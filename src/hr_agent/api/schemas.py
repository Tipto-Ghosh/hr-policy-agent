from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "ChatRequest",
    "ChatResponse",
    "MemoryItem",
    "MemoryListResponse",
    "FeedbackRequest",
    "FeedbackResponse",
    "ErrorResponse",
    "HealthResponse",
    "ReadyResponse",
]

# auth
class LoginRequest(BaseModel):
    username: str = Field(min_length = 1, max_length = 64)
    password: str = Field(min_length = 1, max_length = 128)
    
class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int  # seconds until expiry
    user_id: str
    
# Chat 
class ChatRequest(BaseModel):
    question: str = Field(min_length = 1, max_length = 4000)
    chat_id: str = Field(min_length = 1, max_length = 128)
    

class ChatResponse(BaseModel):
    request_id: str
    chat_id: str
    question: str
    current_query: str
    answer: str
    source_used: str
    guard_verdict: str
    guard_reason: str
    citation_ok: bool
    grounded: bool

# Memory
class MemoryItem(BaseModel):
    key: str
    value: str
    
class MemoryListResponse(BaseModel):
    user_id_hash: str
    items: list[MemoryItem] 
    

# Feedback
class FeedbackRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=64)
    thumb: Literal["up", "down"]
    reason: str = Field(default="", max_length=500)


class FeedbackResponse(BaseModel):
    id: int
    created_at: str
    request_id: str
    thumb: str
    reason: str

# Meta    
class ErrorResponse(BaseModel):
    error: str
    detail: str | None = ""
    request_id: str | None = ""
    

class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    
class ReadyResponse(BaseModel):
    status: Literal["ready", "degraded"]
    check: dict[str, bool]
    details: dict[str, str] = Field(default_factory = dict)