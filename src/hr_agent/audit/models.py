from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class AuditRow:
    id: int
    created_at: str
    request_id: str | None
    user_id: str | None
    question: str
    guard_virdict: str | None
    guard_reason: str | None
    source_used: str
    trace: list[str] = field(default_factory = list)
    
    def summary(self) -> str:
        """
        Return a summary of the audit row.
        """
        verdict = self.guard_virdict or "N/A"
        reason = f"({self.guard_reason})" if self.guard_reason else ""
        
        return f"#{self.id} {self.created_at} [{verdict}{reason}] source: {self.source_used} trace_steps = {len(self.trace)}"