from __future__ import annotations
from typing import Annotated, List, Any
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from hr_agent.audit.trace import TraceRecorder
from hr_agent.llm.usage import UsageRecorder
from hr_agent.memory.profile_adapter import UserProfile



class AgentState(TypedDict):
    # identity
    user_id_hash: str
    chat_id: str
    request_id: str
    
    # query
    question: str
    current_query: str
    raw_question: str
    masked_question: str
    
    # memory
    user_profile: UserProfile
    memory_context: dict[str, Any]
    chat_history: Annotated[List[BaseMessage], add_messages]
    
    # retrieval
    retrieved_docs: List[Document]
    web_search_results: str 
    retrieved_docs_evidence_grade: str 
    web_search_results_evidence_grade: str
    
    route: str # "knowledge_base" or "direct_answer"
    
    # answer
    answer: str 
    source_used: str # knowledge base / web_search
    retry_count: int 
    citation_ok: bool 
    grounded: bool 
    
    # guardrail
    guard_verdict: str # "ok" | "blocked" | "sensitive_case"
    guard_reason: str
    
    # observability
    trace_recorder: TraceRecorder
    ussage_recorder: UsageRecorder