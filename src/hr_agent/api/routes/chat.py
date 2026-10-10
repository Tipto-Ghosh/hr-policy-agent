from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from hr_agent.agent.runner import build_initial_state
from hr_agent.api.auth import AuthUser, current_user
from hr_agent.api.dependencies import GraphDep
from hr_agent.api.schemas import ChatRequest, ChatResponse, ErrorResponse
from hr_agent.audit.trace import TraceRecorder
from hr_agent.guardrails.pii import mask_pii
from hr_agent.llm.usage import UsageRecorder

router = APIRouter(prefix="/chat", tags=["chat"])


def _build_state_and_config(
    req: ChatRequest, user_id: str, request_id: str
) -> tuple[dict, dict]:
    initial = build_initial_state(
        question=req.question,
        user_id=user_id,
        chat_id=req.chat_id,
    )
    initial["request_id"] = request_id
    initial["masked_question"] = mask_pii(req.question)

    config = {
        "configurable": {
            "thread_id": f"{user_id}:{req.chat_id}",
            "trace_recorder": TraceRecorder(),
            "usage_recorder": UsageRecorder(),
        }
    }
    return initial, config


@router.post("", response_model=ChatResponse, responses={500: {"model": ErrorResponse}})
async def chat(
    req: ChatRequest,
    graph: GraphDep,
    user: AuthUser = Depends(current_user),
) -> ChatResponse:
    initial, config = _build_state_and_config(req, user.user_id, user.request_id)
    try:
        result = await graph.ainvoke(initial, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

    return ChatResponse(
        request_id=user.request_id,
        chat_id=req.chat_id,
        question=req.question,
        current_query=result.get("current_query", ""),
        answer=result.get("answer", ""),
        source_used=result.get("source_used", ""),
        guard_verdict=result.get("guard_verdict", ""),
        guard_reason=result.get("guard_reason", ""),
        citation_ok=result.get("citation_ok", False),
        grounded=result.get("grounded", False),
        retretrieved_breadcrumbs=[
            d.metadata.get("breadcrumb", "")
            for d in result.get("retrieved_docs", [])
        ],
        evidence_grade=result.get(
            "retrieved_docs_evidence_grade", ""
        ),
    )


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    graph: GraphDep,
    user: AuthUser = Depends(current_user),
):
    initial, config = _build_state_and_config(req, user.user_id, user.request_id)

    async def event_stream():
        started = time.perf_counter()
        try:
            async for chunk in graph.astream(
                initial, config=config, stream_mode="updates"
            ):
                for node_name, update in chunk.items():
                    elapsed = (time.perf_counter() - started) * 1000.0
                    payload = {
                        "node": node_name,
                        "elapsed_ms": round(elapsed, 1),
                        "update_keys": sorted((update or {}).keys()),
                    }
                    yield f"event: node\ndata: {json.dumps(payload)}\n\n"

            final_state = await graph.aget_state(config)
            values = final_state.values if final_state else {}

            final_payload = ChatResponse(
                request_id=user.request_id,
                chat_id=req.chat_id,
                question=req.question,
                current_query=values.get("current_query", ""),
                answer=values.get("answer", ""),
                source_used=values.get("source_used", ""),
                guard_verdict=values.get("guard_verdict", ""),
                guard_reason=values.get("guard_reason", ""),
                citation_ok=values.get("citation_ok", False),
                grounded=values.get("grounded", False),
                retrieved_breadcrumbs=[
                   d.metadata.get("breadcrumb", "")
                   for d in values.get("retrieved_docs", [])
               ],
               evidence_grade=values.get(
                   "retrieved_docs_evidence_grade", ""
               ),
            ).model_dump()
            yield f"event: done\ndata: {json.dumps(final_payload)}\n\n"

        except Exception as e:
            err = {
                "error": type(e).__name__,
                "detail": str(e),
                "request_id": user.request_id,
            }
            yield f"event: error\ndata: {json.dumps(err)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )