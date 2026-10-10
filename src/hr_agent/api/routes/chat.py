from __future__ import annotations
import json
import time
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from hr_agent.api.dependencies import GraphDep
from hr_agent.api.schemas import ChatRequest, ChatResponse, ErrorResponse
from hr_agent.audit.trace import TraceRecorder
from hr_agent.llm.usage import UsageRecorder
from hr_agent.agent.runner import build_initial_state
from hr_agent.guardrails.pii import mask_pii

router = APIRouter(
    prefix = "/chat",
    tags = ["chat"]
)

def _build_state_and_config(request: ChatRequest, request_id: str)->tuple[dict, dict]:
    """ 
    Shared by both endpoints. Builds the initial state and the LangGraph
    config including the per-run trace/usage recorders that travel via
    config["configurable"].
    """
    initial = build_initial_state(
        question = request.question,
        user_id = request.user_id,
        chat_id = request.chat_id,
    )
    
    initial["request_id"] = request_id
    initial["masked_question"] = mask_pii(request.question)
    
    config = {
        "configurable": {
            "thread_id": f"{request.user_id}:{request.chat_id}",
            "trace_recorder": TraceRecorder(),
            "usage_recorder": UsageRecorder(),
        }
    }
    
    return initial, config


@router.post("", response_model = ChatResponse, responses = {500: {"model": ErrorResponse}})
async def chat(req: ChatRequest, request: Request, graph: GraphDep) -> ChatResponse:
    """
    One synchronous turn. Blocks until the graph finishes and returns the
    final state.
    """
    request_id = request.state.request_id
    initial, config = _build_state_and_config(req, request_id)

    try:
        result = await graph.ainvoke(initial, config = config)
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = f"{type(e).__name__}: {e}",
        )

    return ChatResponse(
        request_id = request_id,
        chat_id =  req.chat_id,
        question = req.question,
        current_query=result.get("current_query", ""),
        answer =  result.get("answer", ""),
        source_used = result.get("source_used", ""),
        guard_verdict = result.get("guard_verdict", ""),
        guard_reason = result.get("guard_reason", ""),
        citation_ok = result.get("citation_ok", False),
        grounded = result.get("grounded", False),
    )


@router.post("/stream")
async def chat_stream(req: ChatRequest, request: Request, graph: GraphDep):
    """
    SSE stream. Emits one JSON event per completed node, then a final
    'done' event carrying the assembled ChatResponse.

    Wire format:
        event: node
        data: {"node": "guard_input", "elapsed_ms": 123.4, "update_keys": [...]}

        event: done
        data: { ...ChatResponse fields... }
    """
    request_id = request.state.request_id
    initial, config = _build_state_and_config(req, request_id)

    async def event_stream():
        started = time.perf_counter()
        try:
            async for chunk in graph.astream(
                initial, config=config, stream_mode="updates"
            ):
                # `updates` yields {node_name: partial_state}
                for node_name, update in chunk.items():
                    elapsed = (time.perf_counter() - started) * 1000.0
                    payload = {
                        "node": node_name,
                        "elapsed_ms": round(elapsed, 1),
                        "update_keys": sorted((update or {}).keys()),
                    }
                    yield f"event: node\ndata: {json.dumps(payload)}\n\n"

            # After the stream completes, fetch the final state from the
            # checkpointer (astream does not return the merged state
            # directly — the stream gives per-node updates).
            final_state = await graph.aget_state(config)
            values = final_state.values if final_state else {}

            final_payload = ChatResponse(
                request_id=request_id,
                chat_id=req.chat_id,
                question=req.question,
                current_query=values.get("current_query", ""),
                answer=values.get("answer", ""),
                source_used=values.get("source_used", ""),
                guard_verdict=values.get("guard_verdict", ""),
                guard_reason=values.get("guard_reason", ""),
                citation_ok=values.get("citation_ok", False),
                grounded=values.get("grounded", False),
            ).model_dump()

            yield f"event: done\ndata: {json.dumps(final_payload)}\n\n"

        except Exception as e:
            err = {"error": type(e).__name__, "detail": str(e), "request_id": request_id}
            yield f"event: error\ndata: {json.dumps(err)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering
        },
    )