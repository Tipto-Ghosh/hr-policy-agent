from __future__ import annotations
from langchain_core.runnables import Runnable

from hr_agent.agent.prompts.generation import KB_GENERATION_PROMPT
from hr_agent.agent.state import AgentState

__all__ = [
    "make_generate_kb_node",
    "render_history_summary_block",
]

def _format_context(docs) -> str:
    return "\n\n".join(
        f'<retrieved_document source="{doc.metadata}">\n{doc.page_content}\n</retrieved_document>'
        for doc in docs
    )

def render_history_summary_block(history_summary: str | None) -> str:
    if not history_summary:
        return ""
    
    return f"\n[Earlier conversation summary]\n{history_summary.strip()}\n"

def make_generate_kb_node(llm: Runnable) -> Runnable:
    """
    This function creates a node that generates a answer based on the retrieved context and the user's question. 
    """
    def generate_kb_node(state: AgentState) -> dict:
        question = state.get("masked_question") or state["question"]
        context = _format_context(state.get("retrieved_docs", []))
        summary_block = render_history_summary_block(state.get("history_summary"))
        
        response = llm.invoke(
            KB_GENERATION_PROMPT.format(
                context = context,
                question = question,
                history_summary_block = summary_block
            )
        )
        return {
            "answer": getattr(response, "content", str(response)),
            "source_used": "retrieved_docs"
        }
    
    return generate_kb_node