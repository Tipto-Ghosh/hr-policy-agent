from __future__ import annotations

import streamlit as st

from ui.api_client import ChatResult


def render_citations(result: ChatResult) -> None:
    """
    Render a compact 'Sources' expander. Falls back to a plain caption
    when the turn abstained or was refused.
    """
    if result.source_used in ("", "insufficient_evidence", "blocked", "sensitive_case"):
        st.caption("No sources retrieved for this turn.")
        return

    # The API does not currently return the retrieved docs themselves — just
    # the metadata that flowed into generation. For a richer panel, extend
    # ChatResponse with a `citations` list (breadcrumb + page). This stub
    # shows what's available now.
    with st.expander("Sources", expanded=False):
        st.markdown(f"**Source type:** {result.source_used}")
        if result.current_query:
            st.caption(f"Query resolved to: `{result.current_query}`")