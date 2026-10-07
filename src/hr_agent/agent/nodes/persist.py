"""Terminal node: writes memory, audit row and usage summary"""

from __future__ import annotations
from langchain_core.runnables import Runnable
from langchain_core.messages import AIMessage

from hr_agent.agent.state import AgentState
from hr_agent.audit.writers import write_audit
from hr_agent.memory.extractor import extract_preferences
from hr_agent.memory.policy import dedupe_by_key, should_write_memory
from hr_agent.memory.store import get_store, preference_namespace

__all__ = [
    "make_persist_node"
]

def make_persist_node(memory_extract_llm: Runnable) -> Runnable:
    def persist_node(state: AgentState) -> dict:
        answer = state.get("answer", "")
        question = state.get("masked_question") or state["question"]
        guard_verdict = state.get("guard_verdict", "")
        user_id_hash = state.get("user_id_hash", "")
        request_id = state.get("request_id", "")
        source_used = state.get("source_used", "")
        
        # append assistant turn to the chat history
        history_update = {}
        if answer:
            history_update["chat_history"] = [AIMessage(content = answer)]
            
        # long term preference memory
        if user_id_hash and guard_verdict == "ok" and answer:
            try:
                canditates = extract_preferences(
                    question = question,
                    answer = answer,
                    llm = memory_extract_llm
                )
                if should_write_memory(guard_verdict, canditates):
                    store = get_store()
                    ns = preference_namespace(user_id_hash)
                    existing = [
                        {"key": it.key, "value": it.value}
                        for it in store.search(ns, query = "", limit = 100)
                    ]
                    to_write = dedupe_by_key(
                       existing = existing,
                       new = canditates     
                    )
                    for item in to_write:
                        store.put(
                            namespace = ns,
                            key = item["key"],
                            value = {
                                "value": item["value"],
                            }
                        )
            except Exception:
                pass
        
        # write audit row
        try:
            trace = []
            recorder = state.get("trace_recorder")
            if recorder:
                trace = recorder.as_list()
                
            usage = state.get("usage_recorder")
            if usage is not None:
                summary = usage.summarize()
                trace = trace + [
                    f"usage_calls={summary.call_count}",
                    f"usage_cost_usd={summary.total_cost_usd:.5f}",
                ]
                
            write_audit(
                question = state.get("raw_question", question),
                source_used = source_used,
                trace_steps = trace,
                request_id = request_id,
                user_id_hash = user_id_hash,
                guard_verdict = guard_verdict,
                guard_reason = state.get("guard_reason", ""),
            )
        except Exception:
            pass
        
        return history_update
    
    return persist_node