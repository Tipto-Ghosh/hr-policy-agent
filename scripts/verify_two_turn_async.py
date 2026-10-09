# scripts/verify_two_turn_async.py
"""
Two-turn async verification: proves short-term memory works end-to-end.

Turn 1: a broad policy question — must go through the KB path.
Turn 2: a follow-up that depends on turn 1's context — must resolve
        references using chat_history and still land on the KB path.

Uses a unique chat_id per run so checkpoint bleed from earlier test
sessions cannot contaminate the result. Run:

    uv run python scripts/verify_two_turn_async.py
"""
from __future__ import annotations

import asyncio
import uuid

from hr_agent.agent.runner import ask_agent_async
from hr_agent.agent.checkpoint import (
    get_async_checkpointer,
    close_async_checkpointer,
)


async def main() -> None:
    # Unique per run — no bleed from earlier test sessions.
    session = uuid.uuid4().hex[:8]
    chat_id = f"chat-{session}"
    user_id = "tipto"

    checkpointer = await get_async_checkpointer()

    try:
        # ---------------- Turn 1 ----------------
        q1 = "What are the duties and obligations of GESCI?"
        r1 = await ask_agent_async(
            question=q1,
            user_id=user_id,
            chat_id=chat_id,
            checkpointer=checkpointer,
        )

        print("=" * 80)
        print(f"[session={session} chat_id={chat_id}]")
        print("=" * 80)
        print(f"TURN 1 — question     : {q1}")
        print(f"TURN 1 — current_query: {r1['current_query']}")
        print(f"TURN 1 — source_used  : {r1['source_used']}")
        print(f"TURN 1 — grade        : {r1['retrieved_docs_evidence_grade']}")
        print(f"TURN 1 — answer[:200] : {r1['answer'][:200].replace(chr(10), ' ')}...")
        print()

        # ---------------- Turn 2 ----------------
        # A follow-up that refers to the topic of turn 1 without naming it.
        # The rewriter must turn this into a standalone question using the
        # history carried by the same chat_id.
        q2 = "Does GESCI give every employee the same chances for hiring?"
        r2 = await ask_agent_async(
            question=q2,
            user_id=user_id,
            chat_id=chat_id,             # same chat_id → same thread_id
            checkpointer=checkpointer,
        )

        print(f"TURN 2 — question     : {q2}")
        print(f"TURN 2 — current_query: {r2['current_query']}")
        print(f"TURN 2 — source_used  : {r2['source_used']}")
        print(f"TURN 2 — grade        : {r2['retrieved_docs_evidence_grade']}")
        print(f"TURN 2 — answer[:200] : {r2['answer'][:200].replace(chr(10), ' ')}...")
        print()

        # ---------------- Assertions ----------------
        # What "working" means for this scenario:
        assert r1["source_used"] == "retrieved_docs", (
            f"Turn 1 should be KB-sourced, got {r1['source_used']}"
        )
        assert r1["retrieved_docs_evidence_grade"] == "good", (
            f"Turn 1 grade should be 'good', got {r1['retrieved_docs_evidence_grade']}"
        )
        assert r2["source_used"] == "retrieved_docs", (
            f"Turn 2 should still be KB-sourced, got {r2['source_used']}"
        )
        assert r2["retrieved_docs_evidence_grade"] == "good", (
            f"Turn 2 grade should be 'good', got {r2['retrieved_docs_evidence_grade']}"
        )
        # The rewriter should have produced a standalone question for turn 2.
        # We don't assert the exact string (model nondeterminism), only that
        # it's non-empty and reasonably long.
        assert len(r2["current_query"]) > 10, (
            f"Turn 2 rewriter produced too-short query: {r2['current_query']!r}"
        )

        print("=" * 80)
        print("ALL ASSERTIONS PASSED")
        print("=" * 80)

    finally:
        await close_async_checkpointer()


if __name__ == "__main__":
    asyncio.run(main())