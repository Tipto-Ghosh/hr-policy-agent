from __future__ import annotations

class TraceRecorder:
    """
    A class to record trace steps for auditing purposes.
    """

    def __init__(self):
        self.trace_steps: list[str] = []

    def record(self, node_name: str, outcome: str = "") -> None:
        entry = f"{node_name}: {outcome}" if outcome else node_name
        self.trace_steps.append(entry)
    
    def as_list(self) -> list[str]:
        return list(self.trace_steps)
    
    def __len__(self) -> int:
        return len(self.trace_steps)
    
    def __repr__(self) -> str:
        return f"TraceRecorder(steps={len(self.trace_steps)})"