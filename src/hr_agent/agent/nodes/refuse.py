from __future__ import annotations
from hr_agent.agent.state import AgentState

__all__ = [
    "refuse_node"
]

REFUSAL_TEMPLATE = (
    "I'm not able to confidently answer that based on verified sources. "
    "Could you rephrase the question or point me to a more specific document?"
)


def refuse_node(state: AgentState) -> dict:
    return {
        "answer": REFUSAL_TEMPLATE,
        "source_used": "blocked",
        "citation_ok": False,
        "grounded": False,
    }