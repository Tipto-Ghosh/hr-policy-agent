from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_groq import ChatGroq
from pydantic import BaseModel
from hr_agent.agent.schemas import *
from hr_agent.agent.prompts.scope import SCOPE_PROMPT
from hr_agent.core.settings import get_settings


__all__ = [
    "get_generator_llm",
    "get_router_llm",
    "get_scope_llm",
    "get_rewriter_llm",
    "get_summarizer_llm",
    "get_router_structured_llm",
    "get_scope_structured_llm",
    "get_kb_grader_llm",
    "get_web_grader_llm",
    "get_groundedness_llm",
]

def _build_chat_model(temperature: float = 0.0) -> BaseChatModel:
    """
    One place where a ChatGroq model is built.
    """
    settings = get_settings()
    return ChatGroq(
        model = settings.groq_model_name,
        temperature = temperature,
        api_key = settings.groq_api_key,
    )
    

def get_generator_llm() -> BaseChatModel:
    return _build_chat_model(temperature = 0.7)

def get_router_llm() -> BaseChatModel:
    return _build_chat_model(temperature = 0.0)

def get_scope_llm() -> BaseChatModel:
    return _build_chat_model(temperature = 0.0)

def get_rewriter_llm() -> BaseChatModel:
    return _build_chat_model(temperature = 0.0)

def get_summarizer_llm() -> BaseChatModel:
    return _build_chat_model(temperature = 0.0)

def _with_structured(llm: BaseChatModel, output_schema: type[BaseModel]) -> Runnable:
    """
    Wraps a chat model with structured output.
    """
    return llm.with_structured_output(
        schema = output_schema,
        method = "json_mode"
    )
    
def get_router_structured_llm() -> Runnable:
    return _with_structured(get_router_llm(), Route)

def get_scope_structured_llm() -> Runnable:
    return _with_structured(get_scope_llm(), _ScopeDecision)

def get_kb_grader_llm() -> Runnable:
    return _with_structured(get_scope_llm(), EvidenceGrade)

def get_web_grader_llm() -> Runnable:
    return _with_structured(get_scope_llm(), EvidenceGrade)

def get_groundedness_llm() -> Runnable:
    return _with_structured(get_scope_llm(), GroundednessResult)