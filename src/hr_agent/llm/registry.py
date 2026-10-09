from __future__ import annotations
from dataclasses import dataclass
from langchain_core.runnables import Runnable

from hr_agent.llm import factory


__all__ = [
    "LLMBundle",
    "build_default_llm_bundle",
    "build_mock_llm_bundle",   
]

@dataclass(frozen = True)
class LLMBundle:
    """ 
    All LLM roles the agent needs, in one object.
    """
    generator: Runnable
    router: Runnable
    scope: Runnable
    rewriter: Runnable
    summarizer: Runnable
    
    # structured-output LLMs
    router_structured: Runnable
    scope_structured: Runnable
    kb_grader: Runnable
    web_grader: Runnable
    groundedness: Runnable
    
    # history-aware rewriter
    contextualize: Runnable
    # memory extractor
    memory_extract: Runnable
    

def build_default_llm_bundle() -> LLMBundle:
    """
    Builds a bundle of LLMs for the agent to use.
    """
    return LLMBundle(
        generator = factory.get_generator_llm(),
        router = factory.get_router_llm(),
        scope = factory.get_scope_llm(),
        rewriter = factory.get_rewriter_llm(),
        summarizer = factory.get_summarizer_llm(),
        router_structured = factory.get_router_structured_llm(),
        scope_structured = factory.get_scope_structured_llm(),
        kb_grader = factory.get_kb_grader_llm(),
        web_grader = factory.get_web_grader_llm(),
        groundedness = factory.get_groundedness_llm(),
        contextualize = factory.get_rewriter_llm(), # same model, different prompt
        memory_extract = factory.get_summarizer_llm(), # same model, different prompt
    )
    
def build_mock_llm_bundle(mock: Runnable) -> LLMBundle:
    """ 
    Every role points at the same mock. Useful for in unit
    tests.
    """
    return LLMBundle(
        generator = mock,
        router = mock,
        scope = mock,
        rewriter = mock,
        summarizer = mock,
        router_structured = mock,
        scope_structured = mock,
        kb_grader = mock,
        web_grader = mock,
        groundedness = mock,
        contextualize = mock,
        memory_extract = mock,
    )