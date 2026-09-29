# scripts/query_rewrite_check.py
"""Compare retrieval BEFORE vs AFTER history-aware query rewriting.

Reproduces the exact two-turn example from notebook 03:
    Turn 1: "What are the duties and obligations of GESCI?"
    Turn 2: "What about their reporting timelines?"

and prints the RETRIEVED CHUNKS for turn 2 with and without contextualization,
so you can see whether the rewrite changed the retrieval set.

Usage:
    uv run scripts/query_rewrite_check.py
"""
from __future__ import annotations

from langchain_groq import ChatGroq

from hr_agent.core.settings import get_settings
from hr_agent.retrieval.query_analysis import ChatTurn, rewrite_query_with_history
from hr_agent.retrieval.retrieve import get_retriever


TURN1_QUESTION = "What are the duties and obligations of GESCI?"
TURN1_ANSWER = (
    "<the real turn-1 answer from your graph — paste it here for a faithful "
    "reproduction, or leave as-is to sanity-check the plumbing>"
)
TURN2_QUESTION = "What about their reporting timelines?"


def _print_breadcrumbs(label: str, query: str, docs) -> None:
    print(f"\n=== {label} ===")
    print(f"query used: {query}")
    for doc in docs:
        print("-", doc.metadata.get("breadcrumb", "(no breadcrumb)"))


def main() -> None:
    settings = get_settings()

    llm = ChatGroq(
        model=settings.groq_model_name,
        api_key=settings.groq_api_key,
        temperature=0,
    )
    retriever = get_retriever()

    chat_history = [
        ChatTurn(question=TURN1_QUESTION, answer=TURN1_ANSWER)
    ]

    # BEFORE: raw follow-up straight into the retriever
    retrieved_before = retriever.invoke(TURN2_QUESTION)
    _print_breadcrumbs("BEFORE (raw follow-up query)", TURN2_QUESTION, retrieved_before)

    # AFTER: history-resolved query into the retriever
    resolved_query = rewrite_query_with_history(TURN2_QUESTION, chat_history, max_turns = 4, llm = llm)
    retrieved_after = retriever.invoke(resolved_query)
    _print_breadcrumbs("AFTER (history-resolved query)", resolved_query, retrieved_after)

    print(
        "\nManual check: the AFTER breadcrumbs should point at reporting / "
        "timeline-related sections. BEFORE likely re-retrieves duties/"
        "obligations content (or something unrelated) because 'their' was "
        "never resolved."
    )


if __name__ == "__main__":
    main()