from __future__ import annotations
from typing import Literal

from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from hr_agent.agent.prompts.router import ROUTER_PROMPT
from hr_agent.agent.state import AgentState

__all__ = [
    "make_router_node",
    "Route"
]


class Route(BaseModel):
    """A route to a specific node in the agent's workflow."""

    route: Literal["knowledge_base", "direct_answer"] = Field(
        description = "The route to take based on the question."
    )
    
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