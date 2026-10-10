from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

__all__ = [
    
]

class ChatRequest(BaseModel):
    question: str = Field(min_length = 1, max_length = 4000)
    chat_id: str = Field(min_length = 1, max_length = 128)
    user_id: str = Field(min_length = 1, max_length = 128)
    

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