"""
Rolling summary for short-term (chat) history.

When chat_history exceeds a token budget, replace older turns with a single
SystemMessage summary, keeping the last `keep_last` turns verbatim.
"""

from __future__ import annotations
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_core.runnables import Runnable

from hr_agent.agent.prompts.history_summary import HISTORY_SUMMARY_PROMPT

__all__ = [
    "summarize_history",
    "should_summarize",
    "DEFAULT_TOKEN_BUDGET",
]

DEFAULT_TOKEN_BUDGET = 2000
_CHAR_PER_TOKEN = 4 # Approximate number of characters per token

def should_summarize(
    chat_history: list[BaseMessage],
    budget_tokens: int = DEFAULT_TOKEN_BUDGET,
) -> bool:
    """
    Determines if the chat history exceeds the token budget and needs summarization.

    Args:
        chat_history (list[BaseMessage]): The list of chat messages.
        budget_tokens (int): The token budget threshold.

    Returns:
        bool: True if summarization is needed, False otherwise.
    """
    total_chars = sum(len(msg.content) for msg in chat_history)
    total_tokens = total_chars // _CHAR_PER_TOKEN
    return total_tokens > budget_tokens

def _role(message: BaseMessage) -> str:
    """
    Maps a message to its role string.

    Args:
        message (BaseMessage): The chat message.

    Returns:
        str: The role of the message ("User" or "AI").
    """
    if isinstance(message, HumanMessage):
        return "User"
    if isinstance(message, AIMessage):
        return "Assistant"
    
    return "System"


def summarize_history(
    chat_history: list[BaseMessage],
    llm: Runnable,
    keep_last: int = 4,
) -> list[BaseMessage]:
    """
    Summarizes the chat history with the provided LLM.
    If summarization is not needed, returns the original chat history.
    On any LLM error, degrades safely by keeping only the most recent turns.
    Args:
        chat_history (list[BaseMessage]): The list of chat messages.
        llm (Runnable): The language model to use for summarization.
        keep_last (int): The number of most recent messages to keep verbatim.

    Returns:
        list[BaseMessage]: The summarized chat history.
    """
    if not should_summarize(chat_history):
        return chat_history

    older = chat_history[:-keep_last]
    recent = chat_history[-keep_last:]
    
    transcript = "\n".join(f"{_role(msg)}: {msg.content}" for msg in older)
    
    prompt = HISTORY_SUMMARY_PROMPT.format(transcript=transcript)
    try:
        response = llm.invoke(prompt)
        summary = getattr(response, "content", str(response)).strip()
    except Exception:
        return list(recent)  # Degrade gracefully by keeping only the most recent turns
    
    if not summary:
        return list(recent)  # Degrade gracefully by keeping only the most recent turns
    
    summary_message = SystemMessage(
        content = f"[Summary of earlier conversation]\n{summary}"
    )
    return [summary_message , *recent]