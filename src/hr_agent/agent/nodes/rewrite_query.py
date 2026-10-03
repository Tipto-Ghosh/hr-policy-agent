from __future__ import annotations
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field
from hr_agent.agent.state import AgentState
from hr_agent.agent.prompts.query_rewrite_prompt import QUERY_REWRITE_PROMPT

__all__ = [
    "make_rewrite_query_node"
]

class RewriteQuery(BaseModel):
    rewritten_query: str = Field(
        ...,
        description = "Rewritten query for better retrieval.Return only the rewritten query, do not answer the question."
    )
    
def make_rewrite_query_node(llm: Runnable) -> Runnable:
    structured_llm = llm.with_structured_output(RewriteQuery)
    
    def rewrite_query(state: AgentState) -> RewriteQuery:
        base_query = state.get("masked_question") or state["question"]
        prompt = QUERY_REWRITE_PROMPT.format(question=base_query)
        
        rewritten_query = structured_llm.invoke(prompt)
        return {
            "current_query": rewritten_query.rewritten_query,
            "retry_count": state.get("retry_count", 0) + 1
        }
    
    return rewrite_query