from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from hr_agent.core.settings import ProviderDefaults, RoleConfig, get_settings

__all__ = [
    "build_chat_model"
]


def _build_groq(role: str, cfg: RoleConfig, provider_defaults: ProviderDefaults) -> BaseChatModel:
    """Build a Groq chat model."""
    settings = get_settings()
    
    if not settings.groq_api_key:
        raise RuntimeError(
            f"Role '{role}' is configured to use Groq, but the GROQ_API_KEY is not set in settings."
        )
    
    return ChatGroq(
        model = cfg.model,
        api_key = settings.groq_api_key,
        temperature = cfg.temperature,
        timeout = cfg.timeout_s,
        max_retries = cfg.max_retries,
    )
    
def _build_ollama(role: str, cfg: RoleConfig, provider_defaults: ProviderDefaults) -> BaseChatModel:
    kwargs = dict(
        model = cfg.model,
        temperature = cfg.temperature,
        client_kwargs = {"timeout": cfg.timeout_s},
    )
    if provider_defaults.base_url:
        kwargs["base_url"] = provider_defaults.base_url
    
    return ChatOllama(**kwargs)


_PROVIDER_BUILDERS = {
    "groq": _build_groq,
    "ollama": _build_ollama,
}

def build_chat_model(
    role: str,
    cfg: RoleConfig,
    provider_defaults: ProviderDefaults | None = None,
) -> BaseChatModel:
    
    builder = _PROVIDER_BUILDERS.get(cfg.provider)
    if builder is None:
        known = ", ".join(sorted(_PROVIDER_BUILDERS))
        raise ValueError(
            f"Unknown provider '{cfg.provider}' for role '{role}'. "
            f"Known providers: {known}."
        )
    return builder(role, cfg, provider_defaults or ProviderDefaults())