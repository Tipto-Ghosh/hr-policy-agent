from __future__ import annotations
from langchain_core.runnables import Runnable

from hr_agent.agent.prompts.generation import WEB_GENERATION_PROMPT
from hr_agent.agent.state import AgentState

__all__ = [
    "make_generate_web_node"
]

def  make_generate_web_node(llm: Runnable) -> Runnable:
    def generate_web_node(state: AgentState) -> dict:
        question = state.get("masked_question") or state["question"]
        web_context = state.get("web_search_results" "")
        response = llm.invoke(
            WEB_GENERATION_PROMPT.format(
                web_context=web_context,
                question=question
            )
        )
        return {
            "answer": getattr(response, "content", str(response)),
            "source_used": "web_search_results"
        }
    return generate_web_node