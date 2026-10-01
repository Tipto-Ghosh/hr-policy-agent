from __future__ import annotations

from langchain_core.runnables import Runnable
from hr_agent.agent.state import AgentState
from hr_agent.memory.profile_adapter import get_user_profile
from hr_agent.memory.store import get_store, preference_namespace

__all__ = [
    "make_load_context_node"
]

def make_load_context_node(_unused_llm: Runnable|None = None) -> Runnable:
    
    def load_context_node(state: AgentState) -> dict:
        user_id_hash = state.get("user_id_hash" , "")
        profile = get_user_profile(user_id_hash)
        
        memory_context: dict[str, str] = {}
        if user_id_hash:
            store = get_store()
            namespace = preference_namespace(user_id_hash)
            
            try:
                items = store.search(
                    namespace = namespace,
                    query = "",
                    limit = 25,
                )
                memory_context = {item.key: item.value for item in items}
            except Exception:
                memory_context = {}
        
        return {
            "user_profile": profile,
            "memory_context": memory_context,
        }
    
    return load_context_node