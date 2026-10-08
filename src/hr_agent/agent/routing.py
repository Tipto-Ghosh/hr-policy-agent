from __future__ import annotations
from hr_agent.agent.state import AgentState

__all__ = [
    "route_after_guard",
    "route_after_router",
    "route_after_kb_grade",
    "route_after_web_grade",
]

def route_after_guard(state: AgentState) -> str:
    return state.get("guard_verdict", "blocked")

def route_after_router(state: AgentState) -> str:
    return state.get("route", "direct_answer")

def route_after_kb_grade(state: AgentState) -> str:
    return state.get("retrieved_docs_evidence_grade", "weak")

def route_after_web_grade(state: AgentState) -> str:
    if state.get("web_search_results_evidence_grade") == "good":
        return "good"
    
    if state.get("retry_count") >= 1:
        return "insufficient"
    
    return "retry"