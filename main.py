import asyncio

from hr_agent.agent.runner import ask_agent_async
from hr_agent.agent.checkpoint import (
    get_async_checkpointer,
    close_async_checkpointer,
)


async def main() -> None:
    checkpointer = await get_async_checkpointer()
    try:
        # Same chat (chat-A): short-term memory should carry across turns,
        # so turn 2's current_query should be a rewritten standalone question.
        r1 = await ask_agent_async(
            "Tell me about Provision of a Mobile Phone",
            user_id="tipto",
            chat_id="chat-A",
            checkpointer=checkpointer,
        )
        r2 = await ask_agent_async(
            "What happens when the employee leaves?",
            user_id="tipto",
            chat_id="chat-A",
            checkpointer=checkpointer,
        )

        print("turn1 answer       :", r1["answer"][:200], "...")
        print("turn2 current_query:", r2["current_query"])
        print("turn2 source_used  :", r2["source_used"])
        print("turn1 answer       :", r1["answer"], "...")

        # Optional: prove chat isolation. Same user, different chat → no memory.
        r3 = await ask_agent_async(
            "What about their reporting timelines?",
            user_id="tipto",
            chat_id="chat-B",
            checkpointer=checkpointer,
        )
        print("chat-B current_query:", r3["current_query"])  
    finally:
        await close_async_checkpointer()


if __name__ == "__main__":
    asyncio.run(main())