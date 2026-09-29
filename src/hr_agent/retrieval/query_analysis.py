from __future__ import annotations
from dataclasses import dataclass
from hr_agent.core.settings import get_query_analysis_config

__all__ = [
    "ChatTurn",
    "format_chat_history_for_prompt",
    "needs_contextualization",
    "rewrite_query_with_history",
]

@dataclass
class ChatTurn:
    question: str
    answer: str
    
def format_chat_history_for_prompt(
    chat_history: list[ChatTurn], max_turns: int | None = None
) -> str:
    """
    Render the last `max_turns` turns as plain QA text for the prompt.
    `max_turns = None` uses the value from configs/query_analysis.yaml.
    """
    query_analysis_config = get_query_analysis_config()
    if max_turns is None:
        max_turns = query_analysis_config.max_turns
    
    if not chat_history:
        return "(no prior conversation)"
    
    recent = chat_history[-max_turns:]
    lines: list[str] = []
    for turn in recent:
        lines.append(f"User: {turn.question}")
        lines.append(f"Assistant: {turn.answer}")
    return "\n".join(lines)

def needs_contextualization(chat_history: list[ChatTurn]) -> bool:
    """Cheap gate: skip the extra LLM call entirely on a first turn."""
    return bool(chat_history)

def rewrite_query_with_history(
    question: str, 
    chat_history: list[ChatTurn], 
    max_turns: int | None = None,
    llm = None
) -> str:
    """
    Resolve references in `question` against `chat_history`, returning a
    standalone version suitable for the FIRST retrieval attempt.

    Falls back to the original `question` unchanged if:
      - there's no history at all (nothing to resolve against), or
      - the LLM call raises, or
      - the LLM returns an empty/whitespace-only response.
    """
    if not needs_contextualization(chat_history):
        return question
    
    query_analysis_config = get_query_analysis_config()
    if max_turns is None:
        max_turns = query_analysis_config.max_turns
    
    history_text = format_chat_history_for_prompt(
        chat_history, max_turns = max_turns
    )
    prompt = query_analysis_config.prompt.format(
        history = history_text,
        question = question
    )
    
    if llm is None:
        # create the LLM
        from langchain_groq import ChatGroq
        from hr_agent.core.settings import get_settings
        groq_api_key = get_settings().groq_api_key
        llm = ChatGroq(
            api_key = groq_api_key,
            model = query_analysis_config.model_name,
            temperature = 0.0,
        )
    
    try:
        response = llm.invoke(prompt)
        rewritten = getattr(response, "content", str(response).strip())
    except Exception:
        return question
    return rewritten
