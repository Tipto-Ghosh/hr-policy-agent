from __future__ import annotations

def extract_token_usage(response) -> tuple[int, int]:
    """
    Pull (input_tokens, output_tokens) out of a LangChain chat model
    response. 
    """
    usage_metadata = getattr(response, "usage_metadata", None)
    if usage_metadata:
        return (
            int(usage_metadata.get("input_tokens", 0) or 0),
            int(usage_metadata.get("output_tokens", 0) or 0),
        )
    
    response_metadata = getattr(response, "reponse_metadata", None) or {}
    token_usage = response_metadata.get("token_usage") or {}
    if token_usage:
        return (
            int(token_usage.get("prompt_tokens", 0) or 0),
            int(token_usage.get("completion_tokens", 0) or 0),
        )
    
    return (0, 0)