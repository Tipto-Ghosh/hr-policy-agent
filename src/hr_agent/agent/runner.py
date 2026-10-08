"""High-level entry point for one conversation turn."""

from __future__ import annotations
import hashlib
import uuid

from hr_agent.agent.graph import GraphDeps, compile_graph
from hr_agent.audit.trace import TraceRecorder
from hr_agent.guardrails.pii import mask_pii
from hr_agent.llm.usage import UsageRecorder

__all__ = [
    "build_initial_state",
    "ask_agent",
]

def build_initial_state(question: str, user_id: str, chat_id: str) -> dict:
    user_id_hash = hashlib.sha256(user_id.encode()).hexdigest()
    return {
        "question": question,
        "current_query": question,
        "raw_question": question,
        "masked_question": mask_pii(question),
        "request_id": str(uuid.uuid4()),
        "user_id_hash": user_id_hash,
        "chat_id": chat_id,
        "retry_count": 0,
        "guard_verdict": "",
        "guard_reason": "",
        "citation_ok": False,
        "grounded": False,
        "retrieved_docs": [],
        "web_search_results": "",
        "retrieved_docs_evidence_grade": "",
        "web_search_results_evidence_grade": "",
        "answer": "",
        "source_used": "",
        "trace_recorder": TraceRecorder(),
        "usage_recorder": UsageRecorder(),
    }
    
    
def ask_agent(
    question: str, 
    user_id: str, 
    chat_id: str, 
    deps: GraphDeps, 
    checkpointer = None, 
    store = None, 
    verbose: bool = False
) -> dict:
    
    """Run one turn end-to-end.  `thread_id` is f"{user_id}:{chat_id}" so
    different chats don't share short-term memory even for the same user.
    Long-term preference memory is keyed by `user_id_hash` and shared
    across all of that user's chats.
    """
    
    graph = compile_graph(
        deps = deps,
        checkpointer = checkpointer,
        store = store
    )    
    
    thread_id = f"{user_id}:{chat_id}"
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    
    initial = build_initial_state(question, user_id, chat_id)
    result = graph.invoke(initial, config = config)
    
    if verbose:
        print("=" * 40)
        print("Question:", question)
        print("GUARD VERDICT:", result.get("guard_verdict"))
        print("SOURCE USED:", result.get("source_used"))
        print("\nANSWER:\n", result.get("answer"))
    
    return result