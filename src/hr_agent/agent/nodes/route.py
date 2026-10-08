from __future__ import annotations
from langchain_core.runnables import Runnable
from hr_agent.agent.prompts.router import ROUTER_PROMPT
from hr_agent.agent.state import AgentState
from hr_agent.agent.schemas import Route

__all__ = [
    "make_router_node",
]

    
def make_router_node(router_llm: Runnable) -> Runnable:
    """Creates a router node that determines the appropriate route based on the question."""
    def route_question_node(state: AgentState) -> dict:
        """Routes the question to the appropriate node based on the question."""
        question = state.get("masked_question") or state["question"]
        router_prompt = ROUTER_PROMPT.format(
            question = question
        )
        decision: Route = router_llm.invoke(
           router_prompt 
        )
        return {
            "route": decision.route,
            "source_used": decision.route
        }
    
    return route_question_node