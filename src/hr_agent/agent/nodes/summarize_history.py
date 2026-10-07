from __future__ import annotations
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable

from hr_agent.agent.state import AgentState
from hr_agent.memory.summarizer import should_summarize, summarize_history
from hr_agent.agent.prompts.history_summary import HISTORY_SUMMARY_PROMPT
from hr_agent.core.settings import get_chat_history_config

chat_history_config = get_chat_history_config()

__all__ = [
    "make_summarize_history_node",
    "DEFAULT_TOKEN_BUDGET",
    "CHAR_PER_TOKEN",
    "KEEP_LAST_N_TURNS",
]

DEFAULT_TOKEN_BUDGET = chat_history_config["DEFAULT_TOKEN_BUDGET"]
CHAR_PER_TOKEN = chat_history_config["CHAR_PER_TOKEN"]
KEEP_LAST_N_TURNS = chat_history_config["KEEP_LAST_N_TURNS"]


def _role(message: BaseMessage) -> str:
    if isinstance(message, HumanMessage):
        return "User"
    elif isinstance(message, AIMessage):
        return "Assistant"
    else:
        return "System"
    
def _total_tokens_estimate(messages: list[BaseMessage]) -> int:
    total_chars = sum(len(message.content) for message in messages)
    return total_chars // CHAR_PER_TOKEN


def make_summarize_history_node(llm: Runnable) -> Runnable:
    def summarize_history_node(state: AgentState) -> dict:
        history: list[BaseMessage] = state.get("chat_history", []) or []
        
        if _total_tokens_estimate(history) <= KEEP_LAST_N_TURNS:
            return {}
        
        older = history[:-KEEP_LAST_N_TURNS]
        transcript = "\n".join(f"{_role(message)}: {message.content}" for message in older)
        
        try:
            response = llm.invoke(
               HISTORY_SUMMARY_PROMPT.format(transcript = transcript)   
            )
            summary_text = getattr(response, "content", str(response)).strip()
        except Exception:
            return {}
        
        if not summary_text:
            return {}
        
        return {
            "history_summary": summary_text
        }
    
    return summarize_history_node