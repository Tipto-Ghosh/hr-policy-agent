from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_core.runnables import RunnableWithFallbacks
from pydantic import BaseModel
from hr_agent.agent.schemas import *
from hr_agent.core.settings import RoleConfig, get_models_config
from hr_agent.llm.providers import build_chat_model


__all__ = [
    "build_role_llm", 
    "build_role_llm_with_fallback",
    "build_role_chain",
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

# single role resolver
def build_role_llm(role: str) -> BaseChatModel:
    cfg = get_models_config()
    role_cfg: RoleConfig | None = cfg.roles.get(role)
    
    if role_cfg is None:
       known = ", ".join(sorted(cfg.roles.keys())) or "<none>"
       raise ValueError(
           f"No role '{role}' in configs/models.yaml. Known roles: {known}."
       ) 
    
    provider_defaults = cfg.providers.get(role_cfg.provider)
    return build_chat_model(role, role_cfg, provider_defaults)


# fallback chain
def build_role_llm_with_fallback(role: str) -> Runnable:
    """
    Build `role` and, if it declares `fallback_role`, wrap it in
    `with_fallbacks([<fallback>])`. The fallback role is resolved
    recursively (so a fallback can itself have a fallback), with a
    visited-set guard against config cycles.
    """
    cfg = get_models_config()
    return _build_chain(role, cfg.roles, visited=set())
    

def _build_chain(role: str, roles: dict[str, RoleConfig], visited: set[str]) -> Runnable:
    if role in visited:
       raise ValueError(f"Cycle detected in fallback_role chain at '{role}'.")
    
    visited.add(role)
    
    
    primary = build_role_llm(role)
    role_cfg = roles.get(role)
    
    if role_cfg is None or not role_cfg.fallback_role:
        return primary
    
    fallback = _build_chain(role_cfg.fallback_role, roles, visited)
    return primary.with_fallbacks([fallback])



build_role_chain = build_role_llm_with_fallback
 

def _structured_chain(role: str, schema: type[BaseModel]) -> Runnable:
    cfg = get_models_config()
    return _structured_chain_impl(role, schema, cfg.roles, visited=set())

def _structured_chain_impl(
    role: str,
    schema: type[BaseModel],
    roles: dict[str, RoleConfig],
    visited: set[str],
) -> Runnable:
    if role in visited:
        raise ValueError(f"Cycle detected in fallback_role chain at '{role}'.")
    
    visited.add(role)
    
    primary = build_role_llm(role).with_structured_output(schema, method="json_mode")
    role_cfg = roles.get(role)
    
    if role_cfg is None or not role_cfg.fallback_role:
        return primary
    
    fallback = _structured_chain_impl(role_cfg.fallback_role, schema, roles, visited)
    return primary.with_fallbacks([fallback])



def get_generator_llm() -> BaseChatModel:
    return build_role_llm_with_fallback("generator")

def get_router_llm() -> BaseChatModel:
    return build_role_llm_with_fallback("router")

def get_scope_llm() -> BaseChatModel:
    return build_role_llm_with_fallback("scope")

def get_rewriter_llm() -> BaseChatModel:
    return build_role_llm_with_fallback("rewriter")

def get_summarizer_llm() -> BaseChatModel:
    return build_role_llm_with_fallback("summarizer")

# structured-output LLMs
def get_router_structured_llm() -> Runnable:
    from hr_agent.agent.nodes.route import Route
    return _structured_chain("router", Route)

 
def get_scope_structured_llm() -> Runnable:
    from hr_agent.agent.nodes.guard_input import _ScopeDecision
    return _structured_chain("scope", _ScopeDecision)

def get_kb_grader_llm() -> Runnable:
    from hr_agent.agent.nodes.grade_kb import EvidenceGrade
    return _structured_chain("kb_grader", EvidenceGrade)

def get_web_grader_llm() -> Runnable:
    from hr_agent.agent.nodes.grade_kb import EvidenceGrade
    return _structured_chain("web_grader", EvidenceGrade) 
    
def get_groundedness_llm() -> Runnable:
    from hr_agent.agent.nodes.guard_output import GroundednessResult
    return _structured_chain("groundedness", GroundednessResult)
