from __future__ import annotations
from langchain_core.runnables import Runnable
from hr_agent.agent.state import AgentState

__all__ = [
    "make_retrieve_node",
]

def make_retrieve_node(retriever: Runnable) -> Runnable:
    """Creates a retrieve node that retrieves relevant documents based on the question."""
    def retrieve_documents_node(state: AgentState) -> dict:
        """Retrieves relevant documents based on the question."""
        query = state.get("current_query") or state.get("masked_question") or state["question"]
        retrieved_docs = retriever.invoke(
            query
        )
        return {
            "retrieved_docs": retrieved_docs,
            "source_used": "knowledge_base"
        }
    return retrieve_documents_node