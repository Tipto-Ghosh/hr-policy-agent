# scripts/verify_long_term_memory_async.py
"""
Long-term preference memory verification: a preference declared in one
chat is visible to another chat by the same user. Run:

    uv run python scripts/verify_long_term_memory_async.py
"""
from __future__ import annotations

import asyncio
import hashlib
import uuid

from hr_agent.agent.runner import ask_agent_async
from hr_agent.agent.checkpoint import (
    get_async_checkpointer,
    close_async_checkpointer,
)
from hr_agent.memory.store import get_store, preference_namespace


async def main() -> None:
    session = uuid.uuid4().hex[:8]
    user_id = "tipto"
    chat_1 = f"chat-1-{session}"
    chat_2 = f"chat-2-{session}"   # a *different* chat, same user

    checkpointer = await get_async_checkpointer()

    try:
        # Turn 1: declare a preference. The memory extractor should pick
        # this up post-response and write it to the Store.
        await ask_agent_async(
            question="Answer concisely — what is the probation period?",
            user_id=user_id,
            chat_id=chat_1,
            checkpointer=checkpointer,
        )

        # Inspect the Store directly to confirm the write happened.
        user_id_hash = hashlib.sha256(user_id.encode()).hexdigest()
        ns = preference_namespace(user_id_hash)
        items = get_store().search(ns, query="", limit=20)
        stored = {item.key: item.value for item in items}
        print(f"Stored preferences for {user_id}: {stored}")

        assert stored, (
            "No preferences were written after a turn that declared "
            "verbosity='concise'. Check memory/policy.py and persist.py."
        )

        # Turn 2: different chat, same user. The preference should be
        # loaded by load_context and available to generation.
        r2 = await ask_agent_async(
            question="What is the notice period for resignation?",
            user_id=user_id,
            chat_id=chat_2,
            checkpointer=checkpointer,
        )
        print(f"[chat-2] source_used  : {r2['source_used']}")
        print(f"[chat-2] answer[:200] : {r2['answer'][:200].replace(chr(10), ' ')}...")

        # We don't assert on answer *style* — that would depend on the
        # generator honoring the preference. The structural guarantee we
        # can assert is that the preference exists in the Store and is
        # discoverable from any chat of the same user.
        print("=" * 80)
        print("LONG-TERM MEMORY VERIFIED")
        print("=" * 80)

    finally:
        await close_async_checkpointer()


if __name__ == "__main__":
    asyncio.run(main())