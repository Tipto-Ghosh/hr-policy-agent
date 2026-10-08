from __future__ import annotations
from dataclasses import dataclass

from langchain_core.runnables import Runnable
from langgraph.graph import START, END, StateGraph
from langgraph.store.base import BaseStore

from hr_agent.agent.nodes import (
    answer_insufficient_node,
    contextualize_query_node,
    make_direct_answer_node,
    make_generate_kb_node,
    make_web_search_node,
    make_generate_web_node,
    make_grade_kb_node,
    make_grade_web_node,
    make_guard_input_node,
    make_guard_output_node,
    make_load_context_node,
    make_persist_node,
    make_retrieve_node,
    make_rewrite_query_node,
    make_router_node,
    make_summarize_history_node,
    refuse_node,
    sensitive_case_node
)
from hr_agent.agent.routing import (
    route_after_guard,
    route_after_kb_grade,
    route_after_router,
    route_after_web_grade
)
from hr_agent.agent.state import AgentState
from hr_agent.agent.checkpoint import get_checkpointer
from hr_agent.memory.store import get_store
from hr_agent.llm.registry import LLMBundle

__all__ = [
    "GraphDeps",
    "build_graph",
    "compile_graph",
    "save_graph_image",
]

@dataclass
class GraphDeps:
    """All injectable dependencies for one graph instance."""
    llms: LLMBundle
    retriever: Runnable
    web_search: Runnable # TavilySearch
    

def build_graph(deps: GraphDeps) -> StateGraph:
    # first get all the llms
    llms = deps.llms
    
    workflow = StateGraph(AgentState)
    
    # guardrail nodes
    workflow.add_node("guard_input", make_guard_input_node(llms.scope_structured))
    workflow.add_node("refuse", refuse_node)
    workflow.add_node("sensitive_case_response", sensitive_case_node)
    workflow.add_node("guard_output", make_guard_output_node(llms.groundedness))
    
    # memory and context nodes
    workflow.add_node("load_context", make_load_context_node())
    workflow.add_node(
        "contextualize_query",
        lambda state: contextualize_query_node(state, llms.contextualize)
    )
    
    # routing / retrieval nodes
    workflow.add_node("route_question", make_router_node(llms.router_structured))
    workflow.add_node("retrieve_kb_docs", make_retrieve_node(deps.retriever))
    workflow.add_node("grade_kb_evidence", make_grade_kb_node(llms.kb_grader))
    workflow.add_node("web_search", make_web_search_node(deps.web_search))
    workflow.add_node("grade_web_evidence", make_grade_web_node(llms.web_grader))
    workflow.add_node("rewrite_query", make_rewrite_query_node(llms.rewriter))
    
    # generation nodes
    workflow.add_node("generate_from_kb", make_generate_kb_node(llms.generator))
    workflow.add_node("generate_from_web_search", make_generate_web_node(llms.generator))
    workflow.add_node("direct_answer", make_direct_answer_node(llms.generator))
    
    workflow.add_node("answer_insufficient", answer_insufficient_node)
    
    # summarization nodes
    workflow.add_node(
        "summarize_history",
        make_summarize_history_node(llms.summarizer)
    )
    workflow.add_node("persist", make_persist_node(llms.memory_extract))
    
    # edges
    workflow.add_edge(START, "guard_input")
    workflow.add_conditional_edges(
        "guard_input",
        route_after_guard,
        {
            "ok": "load_context",
            "blocked": "refuse",
            "sensitive_case": "sensitive_case_response"
        }
    )
    
    # after context load, resolve references before routing
    workflow.add_edge("load_context", "contextualize_query")
    workflow.add_edge("contextualize_query", "route_question")
    
    workflow.add_conditional_edges(
        "route_question",
        route_after_router,
        {
            "knowledge_base": "retrieve_kb_docs",
            "direct_answer": "direct_answer",
        }
    )
    
    workflow.add_edge("retrieve_kb_docs", "grade_kb_evidence")
    
    # grade_kb_evidence => generate_from_kb or web_search
    workflow.add_conditional_edges(
        "grade_kb_evidence",
        route_after_kb_grade,
        {
            "good": "generate_from_kb",
            "weak": "web_search",
        }
    )
    
    workflow.add_edge("web_search", "grade_web_evidence")
    
    workflow.add_conditional_edges(
        "grade_web_evidence",
        route_after_web_grade,
        {
            "good": "generate_from_web_search",
            "retry": "rewrite_query",
            "insufficient": "answer_insufficient"
        }
    )
    
    workflow.add_edge("rewrite_query", "retrieve_kb_docs")
    
    # generation path => guard_output => summarize_history => persist => end
    workflow.add_edge("generate_from_kb", "guard_output")
    workflow.add_edge("generate_from_web_search", "guard_output")
    workflow.add_edge("direct_answer", "guard_output")
    workflow.add_edge("answer_insufficient", "guard_output")
    
    workflow.add_edge("guard_output", "summarize_history")
    workflow.add_edge("summarize_history", "persist")
    workflow.add_edge("persist", END)
    
    # terminal guardrail branches bypassing output guard groundedness checks
    workflow.add_edge("refuse", "persist")
    workflow.add_edge("sensitive_case_response", "persist")
    
    return workflow


def compile_graph(
    deps: GraphDeps,
    checkpointer = None, 
    store: BaseStore | None = None
) -> Runnable:
    """
    Compiles the graph with the given dependencies, checkpointer, and store.
    Checkpointer: short-term memory for the graph
    Store: long-term memory for the graph
    """
    workflow = build_graph(deps)
    return workflow.compile(
        checkpointer = checkpointer if checkpointer is not None else get_checkpointer(),
        store = store if store is not None else get_store() 
    )

def save_graph_image(compiled_graph: Runnable, file_path: str) -> None:
    """
    Generates a Mermaid PNG representation of the compiled graph and saves it.
    Ensure you pass the COMPILED graph to this function, not the StateGraph builder.
    """
    image_bytes = compiled_graph.get_graph().draw_mermaid_png()
    with open(file_path, "wb") as f:
        f.write(image_bytes)