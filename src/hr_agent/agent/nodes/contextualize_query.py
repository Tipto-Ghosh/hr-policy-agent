from __future__ import annotations

from typing import Iterable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import Runnable

from hr_agent.agent.state import AgentState
from hr_agent.retrieval.query_analysis import ChatTurn, rewrite_query_with_history

__all__ = [
    "contextualize_query_node",
    "to_chat_turns",
]

def to_chat_turns(
    raw_chat_history: Iterable[BaseMessage],
) -> list[ChatTurn]:
    """
    Normalize `state["chat_history"]` into list[ChatTurn]
    Handles:
    - ChatTurn objects 
    - dicts with "question" and "answer" keys
    - (question, answer) tuples/lists
    - LangChain BaseMessage pairs
    """
    items = list(raw_chat_history or [])
    turns: list[ChatTurn] = []
    
    if items and all(isinstance(i, BaseMessage) for i in items):
        pending_question: str | None = None
        for msg in items:
            if isinstance(msg, HumanMessage):
                pending_question = msg.content or ""
            elif isinstance(msg, AIMessage) and pending_question is not None:
                turns.append(
                    ChatTurn(
                       question = pending_question, 
                       answer = msg.content or ""
                    )
                )
                pending_question = None
        return turns
    
    for item in items:
        if isinstance(item, ChatTurn):
            turns.append(item)
        elif isinstance(item, dict):
            turns.append(
                ChatTurn(
                    question = item.get("question", ""),
                    answer = item.get("answer", "")
                )
            )
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            turns.append(ChatTurn(question = item[0], answer = item[1]))
    return turns

def contextualize_query_node(
    state: AgentState,
    rewriter_llm: Runnable,
) -> dict:
    question = state["question"]
    chat_history = to_chat_turns(state.get("chat_history"))
    resolved = rewrite_query_with_history(
        question = question,
        chat_history = chat_history,
        llm = rewriter_llm
    )
    return {
        "current_query": resolved
    }