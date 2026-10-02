from __future__ import annotations
from langchain_core.runnables import Runnable
from typing import Literal
from pydantic import BaseModel, Field
from hr_agent.agent.state import AgentState
from hr_agent.agent.prompts.grader import KB_EVIDENCE_GRADE_PROMPT

__all__ = [
    "make_grade_kb_node",
    "EvidenceGrade"
]

class EvidenceGrade(BaseModel):
    """A grade for the evidence based on its ability to answer the question."""

    grade: Literal["good", "weak"] = Field(
        description = "good if the evidence can answer the question; weak otherwise."
    )
    
def make_grade_kb_node(grader_llm: Runnable) -> Runnable:
    """Creates a grade_kb node that grades the private knowledge base evidence based on the question."""
    def grade_kb_node(state: AgentState) -> dict:
        """Grades the private knowledge base evidence based on the question."""
        question = state.get("masked_question") or state["question"]
        context = "\m\n".join(
            f"Source: {doc.metadata.get('source')}\n{doc.page_content}"
            for doc in state.get("retrieved_docs", [])
        )
        grade_prompt = KB_EVIDENCE_GRADE_PROMPT.format(
            question = question,
            context = context
        )
        result: EvidenceGrade = grader_llm.invoke(
            grade_prompt
        )
        return {
           "retrieved_docs_evidence_grade": result.grade   
        }
    
    return grade_kb_node