from __future__ import annotations
import uuid
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from hr_agent.agent.prompts.scope import SCOPE_PROMPT
from hr_agent.agent.state import AgentState
from hr_agent.guardrails.pii import mask_pii

__all__ = ["make_guard_input_node"]

INJECTION_MARKERS = [
    "ignore previous", "ignore the above", "disregard the above",
    "you are now", "system prompt", "reveal your instructions",
    "print your prompt", "repeat the words above", "what were you told",
]
SENSITIVE_CASE_MARKERS = [
    "my case", "my complaint", "my grievance", "my disciplinary",
    "my termination", "my specific situation", "investigate me",
]

class _ScopeDecision(BaseModel):
    in_scope: bool = Field(
        description = "True if the question is HR/organizational in scope."
    )

def _heuristic_injection(text: str) -> bool:
    lowered = text.lower()
    return any(m in lowered for m in INJECTION_MARKERS)

def _sensitive_case(text: str) -> bool:
    lowered = text.lower()
    return any(m in lowered for m in SENSITIVE_CASE_MARKERS)

def make_guard_input_node(
    scope_llm: Runnable,
) -> Runnable:
    """
    Returns a node callable. `scope_llm` is the structured-output LLM that
    produces a `_ScopeDecision`.

    On any terminal verdict (blocked / sensitive_case), the HumanMessage is
    NOT appended to chat_history — poisoned or off-topic turns must not
    become part of the thread the next turn resolves against.
    """
    def guard_input_node(state: AgentState) -> dict:
        question = state["question"]
        request_id = state.get("request_id", str(uuid.uuid4()))
        raw = question
        
        if _heuristic_injection(question):
            return {
                "request_id": request_id,
                "raw_question": raw,
                "guard_verdict": "blocked",
                "guard_reason": "heuristic injection detected",
            }
        
        decision: _ScopeDecision = scope_llm.invoke(
            input = SCOPE_PROMPT.format(question)
        )
        if not decision.in_scope:
            return {
                "request_id": request_id,
                "raw_question": raw,
                "guard_verdict": "blocked",
                "guard_reason": "out of scope question",
            }
        
        masked_question = mask_pii(question)
        if _sensitive_case(question):
            return {
                "request_id": request_id,
                "raw_question": raw,
                "guard_verdict": "sensitive_case",
                "guard_reason": "active case",
                "masked_question": masked_question,
            }
        
        return {
            "request_id": request_id,
            "raw_question": raw,
            "masked_question": masked_question,
            "current_query": masked_question,
            "guard_verdict": "ok",
            "chat_history": [HumanMessage(content = masked_question)],
        }
    
    return guard_input_node