from __future__ import annotations
from hr_agent.agent.state import AgentState


__all__ = [
    "sensitive_case_node",
]

DISCLAIMER = "\n\n_This is policy information, not legal advice._"

SENSITIVE_CASE_ANSWER = (
    "I can share general policy information, but for your specific case "
    "I'd recommend contacting HR or your supervisor directly, since that "
    "requires review of your individual situation."
)

def sensitive_case_node(state: AgentState) -> dict:
    return {
        "answer": SENSITIVE_CASE_ANSWER + DISCLAIMER,
        "source_used": "senstive_case",
        "citation_ok": False,
        "grounded": False,
    }