import streamlit as st

import db
from auth import login_page
from views import child, explore, home, library, parent, reader

db.init_db()

st.set_page_config(
    page_title="SafeStory",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Auth ──────────────────────────────────────────────────────────────────────

if "user" not in st.session_state:
    login_page()
    st.stop()

user = st.session_state.user

# ── 아이 모드 — 전체화면 ──────────────────────────────────────────────────────

if st.session_state.get("child_auth"):
    child.show(user)
    st.stop()

# ── 모드 라우팅 ───────────────────────────────────────────────────────────────

mode = st.session_state.get("app_mode", "home")

if mode == "home":
    home.show(user)
elif mode == "parent":
    # 부모 모드는 사이드바 사용
    st.markdown("""
    <style>.stApp{background:#f8f9ff}</style>
    """, unsafe_allow_html=True)
    with st.sidebar:
        if st.button("← 홈으로", use_container_width=True):
            st.session_state.app_mode = "home"
            st.rerun()
    parent.show(user)
elif mode == "child":
    child.show(user)
elif mode == "library":
    with st.sidebar:
        if st.button("← 홈으로", use_container_width=True):
            st.session_state.app_mode = "home"
            st.rerun()
    library.show(user)
elif mode == "explore":
    with st.sidebar:
        if st.button("← 홈으로", use_container_width=True):
            st.session_state.app_mode = "home"
            st.rerun()
    explore.show(user)
elif mode == "reader":
    with st.sidebar:
        if st.button("← 홈으로", use_container_width=True):
            st.session_state.app_mode = "home"
            st.rerun()
    reader.show(user)
