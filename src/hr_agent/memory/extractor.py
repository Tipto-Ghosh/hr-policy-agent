from __future__ import annotations
import json
from langchain_core.runnables import Runnable

from hr_agent.agent.prompts.memory_extract import MEMORY_EXTRACT_PROMPT

__all__ = [
    "extract_preferences",
    "ALLOWED_MEMORY_KEYS",
]

ALLOWED_MEMORY_KEYS = {
    "language",  # "en", "bn"
    "verbosity", # "concise", "detailed"
    "format",  # "bullets", "prose", "table"
    "recurring_topic",  # "leave", "travel", "discipline"
}

def extract_preferences(question: str, answer: str, llm: Runnable) -> list[dict]:
    """
    Extracts user preferences from a question and answer pair using the provided LLM.

    Args:
        question (str): The user's question.
        answer (str): The LLM's response to the question.
        llm (Runnable): The language model to use for extraction.

    Returns:
        list[dict]: A list of dictionaries containing the extracted preferences.
    """
    prompt = MEMORY_EXTRACT_PROMPT.format(question=question, answer=answer)
    try:
        response = llm.invoke(prompt)
        raw = getattr(response, "content", str(response))
        parsed = json.loads(raw)
    except Exception:
        return []
    
    out = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        key = item.get("key")
        value = item.get("value")
        if key in ALLOWED_MEMORY_KEYS and value:
            out.append({"key": key, "value": value})
    return out