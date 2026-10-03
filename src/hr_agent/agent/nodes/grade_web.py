from __future__ import annotations
from langchain_core.runnables import Runnable
from hr_agent.agent.state import AgentState
from hr_agent.agent.prompts.grader import WEB_EVIDENCE_GRADE_PROMPT
from hr_agent.agent.nodes.grade_kb import EvidenceGrade

__all__ = [
    "make_grade_web_node"
]


def make_grade_web_node(grader_llm: Runnable) -> Runnable:
    def grade_web_node(state: AgentState) -> dict:
        question = state.get("masked_question") or state["question"]
        context = state.get("web_search_results", "")
        result: EvidenceGrade = grader_llm.invoke(
            WEB_EVIDENCE_GRADE_PROMPT.format(
                question = question,
                context = context
            )
        )
        return {
            "web_search_results_evidence_grade": result.grade
        }
    
    return grade_web_node