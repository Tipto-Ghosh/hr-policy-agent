from __future__ import annotations
from hr_agent.agent.state import AgentState

__all__ = [
    "route_after_guard",
    "route_after_router",
    "route_after_kb_grade",
    "route_after_web_grade",
]

def route_after_guard(state: AgentState) -> str:
    verdict = state.get("guard_verdict")
    if verdict not in ("ok", "blocked", "sensitive_case"):
        return "blocked"
    return verdict
    
def route_after_router(state: AgentState) -> str:
    route = state.get("route")
    if route not in ("knowledge_base", "direct_answer"):
        return "knowledge_base"
    return route

def route_after_kb_grade(state: AgentState) -> str:
    grade = state.get("retrieved_docs_evidence_grade")
    if grade not in ("good", "weak"):
        return "weak"
    return grade

def route_after_web_grade(state: AgentState) -> str:
    if state.get("web_search_results_evidence_grade") == "good":
        return "good"
    
    if state.get("retry_count") >= 1:
        return "insufficient"
    
    return "retry"