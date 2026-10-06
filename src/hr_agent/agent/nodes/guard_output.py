from __future__ import annotations
import re 

from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field
from hr_agent.agent.nodes.refuse import REFUSAL_TEMPLATE
from hr_agent.agent.nodes.sensitive_case import DISCLAIMER
from hr_agent.agent.prompts.groundness_check_prompt import GROUNDEDNESS_CHECK_PROMPT
from hr_agent.agent.state import AgentState
from hr_agent.guardrails.pii import mask_pii


__all__ = [
    "make_guard_output_node",
]

class GroundednessResult(BaseModel):
    grounded: bool = Field(..., description="Whether the answer is grounded in the context")

def _citation_ok(answer: str) -> bool:
    return "Knowledge Base" in answer or "Web Search" in answer


def make_guard_output_node(groundedness_llm: Runnable) -> Runnable:
    structured_groundedness_llm = (
        groundedness_llm.with_structured_output(GroundednessResult)
    )

    def guard_output_node(state: AgentState) -> dict:
        answer = state.get("answer", "")
        context_docs = state.get("retrieved_docs", []) or []

        citation_ok = _citation_ok(answer)
        grounded = True

        if context_docs:
            try:
                context = "\n\n".join(
                    doc.page_content for doc in context_docs
                )

                decision = structured_groundedness_llm.invoke(
                    GROUNDEDNESS_CHECK_PROMPT.format(
                        context = context,
                        answer = answer,
                    )
                )

                grounded = decision.grounded

            except Exception:
                print("Groundedness check failed")
                grounded = False

        if context_docs and not grounded:
            answer = REFUSAL_TEMPLATE
            citation_ok = False

        answer = mask_pii(answer)

        if not answer.endswith(DISCLAIMER):
            answer += DISCLAIMER

        return {
            "answer": answer,
            "citation_ok": citation_ok,
            "grounded": grounded,
        }

    return guard_output_node