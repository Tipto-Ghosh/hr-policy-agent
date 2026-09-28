from __future__ import annotations
from hr_agent.core.settings import get_models_config


def estimate_llm_cost(
    model_key: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """
    Estimated dollar cost for one LLM call, based on configs/models.yaml.
    Returns 0.0 if the model_key is unknown so a missing pricing entry
    degrades the estimate rather than crashing the run.
    """
    pricing = get_models_config().models.get(model_key)
    if pricing is None:
        return 0.0
    return (
        (input_tokens / 1000.0) * pricing.input_cost_per_1k_usd
        + (output_tokens / 1000.0) * pricing.output_cost_per_1k_usd
    )


def estimate_tool_cost(tool_key: str) -> float:
    """
    Estimated dollar cost for one tool call (flat per-call rate).
    Returns 0.0 if the tool_key is unknown.
    """
    pricing = get_models_config().tools.get(tool_key)
    if pricing is None:
        return 0.0
    return pricing.cost_per_call_usd