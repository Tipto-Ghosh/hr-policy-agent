# scripts/verify_two_turn_isolation_async.py
"""
Chat-isolation verification: proves that two chat_ids for the same user
do not share short-term memory. Run:

    uv run python scripts/verify_two_turn_isolation_async.py
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
    session = uuid.uuid4().hex[:8]
    chat_a = f"chat-A-{session}"
    chat_b = f"chat-B-{session}"
    user_id = "tipto"

    checkpointer = await get_async_checkpointer()

    try:
        # Chat A: turn 1 establishes a context.
        ra1 = await ask_agent_async(
            question="What are the duties and obligations of GESCI?",
            user_id=user_id,
            chat_id=chat_a,
            checkpointer=checkpointer,
        )
        print(f"[chat-A] turn 1 current_query: {ra1['current_query']}")

        # Chat B: a follow-up that WOULD resolve against chat A's context
        # if memory leaked. Since chat B has no history, the rewriter
        # should leave the query essentially unchanged (the pronoun "their"
        # has nothing to resolve against).
        rb1 = await ask_agent_async(
            question="What about their reporting timelines?",
            user_id=user_id,
            chat_id=chat_b,               # different chat, same user
            checkpointer=checkpointer,
        )
        print(f"[chat-B] turn 1 current_query: {rb1['current_query']}")

        # Assertion: chat B's rewriter had no history to resolve against,
        # so the query should still be the raw follow-up (possibly
        # whitespace-normalized). If it got rewritten into something
        # containing "GESCI" or "duties", memory leaked across chats.
        leaked_terms = ("gesci", "duties", "obligations")
        rq = rb1["current_query"].lower()
        leaked = [t for t in leaked_terms if t in rq]
        assert not leaked, (
            f"Chat isolation broken — chat-B query picked up terms from "
            f"chat-A's history: {rb1['current_query']!r} (leaked: {leaked})"
        )

        print("=" * 80)
        print("CHAT ISOLATION VERIFIED")
        print("=" * 80)

    finally:
        await close_async_checkpointer()


if __name__ == "__main__":
    asyncio.run(main())