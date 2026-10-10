from __future__ import annotations

import streamlit as st

from ui.api_client import APIClient


def _submit(client: APIClient, token: str, request_id: str, thumb: str, reason: str = "") -> None:
    try:
        client.submit_feedback(token, request_id, thumb, reason)
        st.toast(f"Thanks — feedback recorded ({thumb}).", icon="✅")
    except Exception as e:
        st.toast(f"Feedback failed: {type(e).__name__}", icon="⚠️")


def render_feedback(client: APIClient, token: str, request_id: str) -> None:
    if not request_id:
        return

    # session_state keyed by request_id so each turn remembers what the user picked
    up_key = f"fb_up_{request_id}"
    down_key = f"fb_down_{request_id}"

    already = st.session_state.get(up_key) or st.session_state.get(down_key)
    if already:
        st.caption("Feedback recorded. Thank you.")
        return

    col1, col2, _ = st.columns([1, 1, 6])
    with col1:
        if st.button("👍", key=f"up_{request_id}", use_container_width=True):
            _submit(client, token, request_id, "up")
            st.session_state[up_key] = True
            st.rerun()
    with col2:
        if st.button("👎", key=f"down_{request_id}", use_container_width=True):
            # for a down vote, ask for a reason
            with st.expander("Tell us why (optional)", expanded=True):
                reason = st.text_input("Reason", key=f"reason_{request_id}")
                if st.button("Submit", key=f"reason_submit_{request_id}"):
                    _submit(client, token, request_id, "down", reason)
                    st.session_state[down_key] = True
                    st.rerun()