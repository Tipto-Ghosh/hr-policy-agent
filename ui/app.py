from __future__ import annotations

import os
import httpx

import streamlit as st

from ui.api_client import APIClient


API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")


 
# page config (must be the first Streamlit call)
 
st.set_page_config(
    page_title="HR Policy Agent",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)


 
# singletons in session_state
 
def _get_client() -> APIClient:
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient(API_URL)
    return st.session_state.api_client


def _ensure_chat_id() -> str:
    if "chat_id" not in st.session_state:
        import uuid
        st.session_state.chat_id = f"ui-{uuid.uuid4().hex[:8]}"
    return st.session_state.chat_id


def _logout() -> None:
    for key in ("token", "user_id", "chat_id", "messages"):
        st.session_state.pop(key, None)


 
# sidebar

def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### HR Policy Agent")

        if st.session_state.get("token"):
            st.caption(
                f"Signed in as **{st.session_state.get('user_id', '?')}**"
            )

            page = st.radio(
                "Page",
                ("Chat", "Memory"),
                key="page_selector",
                label_visibility="collapsed",
            )
            st.session_state["page"] = page

            if st.button("Sign out", use_container_width=True):
                _logout()
                st.rerun()
        else:
            st.caption("Not signed in.")

        st.divider()
        st.markdown("**Session**")
        st.caption(
            f"chat_id: `{st.session_state.get('chat_id', '—')}`"
        )

        # Health check
        try:
            ready = _get_client().ready()
            status = ready.get("status", "unknown")
            icon = "🟢" if status == "ready" else "🟡"
            st.caption(f"{icon} API status: {status}")
        except Exception as e:
            st.caption(f"🔴 API unreachable: {type(e).__name__}")
 
# login
 
def _render_login() -> None:
    st.title("HR Policy Agent")
    st.caption("Sign in to continue. Use a demo user — e.g. `tipto / demo`.")

    col1, col2 = st.columns([1, 2])
    with col1:
        with st.form("login_form"):
            username = st.text_input("Username", value="tipto")
            password = st.text_input("Password", value="demo", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)

        if submitted:
            try:
                result = _get_client().login(username, password)
                st.session_state.token = result.access_token
                st.session_state.user_id = result.user_id
                _ensure_chat_id()
                st.rerun()
            except httpx.HTTPStatusError as e:
                st.error(f"Login failed ({e.response.status_code}): {e.response.text}")
            except Exception as e:
                st.error(f"Login error: {type(e).__name__}: {e}")
    
 
# main
def main() -> None:
    _render_sidebar()

    if not st.session_state.get("token"):
        _render_login()
        return

    _ensure_chat_id()

    page = st.session_state.get("page", "Chat")

    if page == "Chat":
        from ui.pages import chat

        chat.render(
            client=_get_client(),
            token=st.session_state.token,
            chat_id=st.session_state.chat_id,
        )

    elif page == "Memory":
        from ui.pages import memory

        memory.render(
            client=_get_client(),
            token=st.session_state.token,
        )


if __name__ == "__main__":
    main()