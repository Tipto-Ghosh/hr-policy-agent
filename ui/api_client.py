from __future__ import annotations

import json
import httpx
from dataclasses import dataclass, field
from typing import Iterator
from pydantic import BaseModel, Field


DEFAULT_TIMEOUT = 120.0

@dataclass
class LoginResult:
    access_token: str
    token_type: str
    expires_in: int
    user_id: str
    
@dataclass
class ChatResult:
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
    retrieved_breadcrumbs: list[str] = field(default_factory=list)
    evidence_grade: str = ""


@dataclass
class MemoryItem:
    key: str
    value: str

@dataclass
class StreamEvent:
    """One SSE event from /chat/stream."""
    kind: str  # "node" | "done" | "error"
    data: dict = field(default_factory=dict)


# client
class APIClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=DEFAULT_TIMEOUT)

    # ---------- auth ----------
    def login(self, username: str, password: str) -> LoginResult:
        r = self._client.post(
            "/auth/login",
            json={"username": username, "password": password},
        )
        r.raise_for_status()
        return LoginResult(**r.json())

    # ---------- chat (sync) ----------
    def chat(self, token: str, question: str, chat_id: str) -> ChatResult:
        r = self._client.post(
            "/chat",
            json={"question": question, "chat_id": chat_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        r.raise_for_status()
        return ChatResult(**r.json())

    # ---------- chat (streaming) ----------
    def chat_stream(
        self, token: str, question: str, chat_id: str
    ) -> Iterator[StreamEvent]:
        """
        Yield SSE events as they arrive. Uses httpx.stream so each line is
        delivered the moment the server flushes it.
        """
        with self._client.stream(
            "POST",
            "/chat/stream",
            json={"question": question, "chat_id": chat_id},
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            response.raise_for_status()
            current_event: str | None = None
            for line in response.iter_lines():
                if not line:
                    continue
                if line.startswith("event:"):
                    current_event = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    payload = line.split(":", 1)[1].strip()
                    try:
                        data = json.loads(payload)
                    except json.JSONDecodeError:
                        data = {"raw": payload}
                    yield StreamEvent(kind=current_event or "message", data=data)
                    current_event = None

    # ---------- memory ----------
    def list_memory(self, token: str) -> dict:
        r = self._client.get(
            "/memory",
            headers={"Authorization": f"Bearer {token}"},
        )
        r.raise_for_status()
        return r.json()

    def delete_memory(self, token: str, key: str) -> dict:
        r = self._client.delete(
            f"/memory/{key}",
            headers={"Authorization": f"Bearer {token}"},
        )
        r.raise_for_status()
        return r.json()

    # ---------- feedback ----------
    def submit_feedback(
        self, token: str, request_id: str, thumb: str, reason: str = ""
    ) -> dict:
        r = self._client.post(
            "/feedback",
            json={"request_id": request_id, "thumb": thumb, "reason": reason},
            headers={"Authorization": f"Bearer {token}"},
        )
        r.raise_for_status()
        return r.json()

    # ---------- health ----------
    def ready(self) -> dict:
        r = self._client.get("/ready")
        r.raise_for_status()
        return r.json()