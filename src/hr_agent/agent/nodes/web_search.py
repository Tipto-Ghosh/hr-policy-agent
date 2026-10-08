from __future__ import annotations
from langchain_core.runnables import Runnable
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
from hr_agent.agent.state import AgentState

load_dotenv()

__all__ = [
    "make_web_search_node"
]

def make_web_search_node(web_search: Runnable| None = None) -> Runnable:
    """Creates a web search node that retrieves relevant documents based on the question."""
    
    search_tool = web_search or TavilySearch(
        topic = "general",
        include_answers = True,
        include_raw_content = False,
    )
    
    def web_search_node(state: AgentState) -> dict:
        """Retrieves relevant documents based on the question."""
        query = state.get("current_query") or state.get("masked_question") or state["question"]
        
        web_search_results = search_tool.invoke(
            query
        )
        
        return {
            "web_search_results": web_search_results,
            "source_used": "web_search"
        }
    return web_search_node