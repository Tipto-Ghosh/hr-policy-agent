from __future__ import annotations

import streamlit as st

from ui.api_client import APIClient, ChatResult
from ui.components.citations import render_citations
from ui.components.feedback import render_feedback


def _ensure_messages() -> list[dict]:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    return st.session_state.messages


def _render_history() -> None:
    for msg in _ensure_messages():
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def _stream_turn(
    client: APIClient,
    token: str,
    chat_id: str,
    question: str,
) -> ChatResult | None:
    """
    Stream one turn. Shows node events as a status line, and the final
    answer as a chat message. Returns the assembled ChatResult (or None
    on error).
    """
    node_placeholder = st.empty()
    answer_placeholder = st.empty()
    final: ChatResult | None = None

    nodes_seen: list[str] = []
    for event in client.chat_stream(token=token, question=question, chat_id=chat_id):
        if event.kind == "node":
            node = event.data.get("node", "?")
            elapsed = event.data.get("elapsed_ms", 0)
            nodes_seen.append(node)
            node_placeholder.caption(
                f"⚙️ {node}  ·  {elapsed:,.0f} ms  ·  "
                f"({len(nodes_seen)} node{'s' if len(nodes_seen) != 1 else ''})"
            )
        elif event.kind == "done":
            # assemble a ChatResult from the payload
            d = event.data
            final = ChatResult(
                request_id=d.get("request_id", ""),
                chat_id=d.get("chat_id", chat_id),
                question=d.get("question", question),
                current_query=d.get("current_query", ""),
                answer=d.get("answer", ""),
                source_used=d.get("source_used", ""),
                guard_verdict=d.get("guard_verdict", ""),
                guard_reason=d.get("guard_reason", ""),
                citation_ok=bool(d.get("citation_ok", False)),
                grounded=bool(d.get("grounded", False)),
                retrieved_breadcrumbs=d.get("retrieved_breadcrumbs", []),
                evidence_grade=d.get("evidence_grade", ""),
            )
            answer_placeholder.markdown(final.answer)
        elif event.kind == "error":
            node_placeholder.empty()
            st.error(f"{event.data.get('error')}: {event.data.get('detail')}")
            return None

    node_placeholder.empty()
    return final


def render(client: APIClient, token: str, chat_id: str) -> None:
    st.title("Chat")
    st.caption(
        "Ask about GESCI HR policies. Answers cite the section they came "
        "from. Use the memory page to manage learned preferences."
    )

    _render_history()

    question = st.chat_input("Ask a question about the HR manual…")
    if not question:
        return

    # Append user turn immediately
    _ensure_messages().append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Assistant turn
    with st.chat_message("assistant"):
        result = _stream_turn(client, token, chat_id, question)
        if result is None:
            return

        _ensure_messages().append(
            {"role": "assistant", "content": result.answer}
        )

        # Citations + metadata
        st.divider()
        col_a, col_b = st.columns([2, 1])

        with col_a:
            render_citations(result)

        with col_b:
            st.caption(f"Source: `{result.source_used}`")
            st.caption(f"Guard: `{result.guard_verdict or '—'}`")

            if result.grounded:
                st.caption("✅ Grounded")
            else:
                st.caption("⚠️ Not grounded")

        # Evidence diagnostics
        with st.expander("🔎 Evidence Diagnostics", expanded=False):
            st.write(
                "**Evidence grade:**",
                result.evidence_grade or "—",
            )

            st.write("**Retrieved document breadcrumbs:**")

            if result.retrieved_breadcrumbs:
                for breadcrumb in result.retrieved_breadcrumbs:
                    st.markdown(
                        f"- {breadcrumb or '(No breadcrumb available)'}"
                    )
            else:
                st.caption(
                    "No retrieved document breadcrumbs returned."
                )

        # User feedback
        render_feedback(client, token, result.request_id)