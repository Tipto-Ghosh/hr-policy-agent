from __future__ import annotations

import streamlit as st

from ui.api_client import APIClient

def render(client: APIClient, token: str) -> None:
    st.title("Memory")
    st.caption(
        "These are durable preferences the agent has learned about you "
        "(language, verbosity, format, recurring topics). They never "
        "store HR case details. Delete any you don't want kept."
    )

    try:
        payload = client.list_memory(token)
    except Exception as e:
        st.error(f"Could not load memory: {type(e).__name__}: {e}")
        return

    user_id_hash = payload.get("user_id_hash", "")
    items = payload.get("items", [])

    st.caption(f"user_id_hash: `{user_id_hash}`")
    st.divider()

    if not items:
        st.info("No preferences stored yet.")
        return

    for item in items:
        col_a, col_b = st.columns([5, 1])
        with col_a:
            st.markdown(f"**{item['key']}**  \n`{item['value']}`")
        with col_b:
            if st.button("Forget", key=f"del_{item['key']}", use_container_width=True):
                try:
                    client.delete_memory(token, item["key"])
                    st.toast(f"Removed `{item['key']}`", icon="🗑️")
                    st.rerun()
                except Exception as e:
                    st.error(f"Delete failed: {type(e).__name__}: {e}")