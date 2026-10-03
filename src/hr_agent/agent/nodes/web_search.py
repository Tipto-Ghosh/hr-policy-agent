from __future__ import annotations
from langchain_core.runnables import Runnable
from langchain_tavily import TavilySearch

from hr_agent.agent.state import AgentState


__all__ = [
    "make_web_search_node"
]

web_search = TavilySearch(
    topic = "general",
    include_answer = True,
    include_raw_content = False
)

def make_web_search_node(web_search: Runnable = web_search) -> Runnable:
    """Creates a web search node that retrieves relevant documents based on the question."""
    def web_search_node(state: AgentState) -> dict:
        """Retrieves relevant documents based on the question."""
        query = state.get("current_query") or state.get("masked_question") or state["question"]
        
        web_search_results = web_search.invoke(
            query
        )
        
        return {
            "web_search_results": web_search_results,
            "source_used": "web_search"
        }
    return web_search_node