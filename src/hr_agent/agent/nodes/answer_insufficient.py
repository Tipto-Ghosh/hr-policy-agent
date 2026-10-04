from __future__ import annotations
from hr_agent.agent.state import AgentState

__all__ = [
    "answer_insufficient_node"
]

INSUFFICIENT_TEMPLATE = (
    "I could not find enough reliable evidence in the private knowledge base "
    "or the web search results to answer this confidently. "
    "Please provide more specific documents or rephrase the question."
)

def answer_insufficient_node(state: AgentState) -> dict:
    """
    This function creates a node that returns a message indicating insufficient information to answer the question.
    """
    return {
        "answer": INSUFFICIENT_TEMPLATE,
        "source_used": "insufficient_information",
        "citation_ok": False,
        "grounded": False,
    }