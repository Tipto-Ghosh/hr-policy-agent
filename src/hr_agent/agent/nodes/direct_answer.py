from __future__ import annotations
from langchain_core.runnables import Runnable

from hr_agent.agent.prompts.direct_answer import DIRECT_ANSWER_PROMPT
from hr_agent.agent.state import AgentState

__all__ = [
    "make_direct_answer_node"
]

def make_direct_answer_node(llm: Runnable) -> Runnable:
    def direct_answer_node(state: AgentState) -> dict:
        question = state.get("masked_question") or state["question"]
        response = llm.invoke(
            DIRECT_ANSWER_PROMPT.format(
                question=question
            )
        )
        return {
            "answer": getattr(response, "content", str(response)),
            "source_used": "direct_answer"
        }
    return direct_answer_node