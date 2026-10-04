from __future__ import annotations
from langchain_core.runnables import Runnable

from hr_agent.agent.prompts.generation import KB_GENERATION_PROMPT
from hr_agent.agent.state import AgentState

__all__ = [
    "make_generate_kb_node"
]

def _format_context(docs) -> str:
    return "\n\n".join(
        f'<retrieved_document source="{doc.metadata}">\n{doc.page_content}\n</retrieved_document>'
        for doc in docs
    )

def make_generate_kb_node(llm: Runnable) -> Runnable:
    """
    This function creates a node that generates a answer based on the retrieved context and the user's question. 
    """
    def generate_kb_node(state: AgentState) -> dict:
        question = state.get("masked_question") or state["question"]
        context = _format_context(state.get("retrieved_docs", []))
        response = llm.invoke(
            KB_GENERATION_PROMPT.format(
                context=context,
                question=question
            )
        )
        return {
            "answer": getattr(response, "content", str(response)),
            "source_used": "retrieved_docs"
        }
    
    return generate_kb_node