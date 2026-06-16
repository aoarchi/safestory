import streamlit as st

import db
from auth import login_page
from views import child, explore, parent, reader

# ── Bootstrap ────────────────────────────────────────────────────────────────

db.init_db()

st.set_page_config(
    page_title="SafeStory",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp { background-color: #f8f9ff; }
.block-container { padding-top: 1.8rem; }
</style>
""", unsafe_allow_html=True)

# ── Auth guard ────────────────────────────────────────────────────────────────

if "user" not in st.session_state:
    login_page()
    st.stop()

user = st.session_state.user

# ── Mode routing ──────────────────────────────────────────────────────────────

# Child mode renders its own full-screen UI (no sidebar navigation)
if st.session_state.get("child_auth"):
    child.show(user)
    st.stop()

with st.sidebar:
    st.markdown("## 📚 SafeStory")
    mode = st.radio(
        "mode",
        ["👨‍👩‍👧 부모 모드", "👶 아이 시청 모드", "🌍 큐레이터 둘러보기", "📖 동화 읽기"],
        label_visibility="collapsed",
    )

if mode == "👨‍👩‍👧 부모 모드":
    parent.show(user)
elif mode == "👶 아이 시청 모드":
    child.show(user)
elif mode == "🌍 큐레이터 둘러보기":
    explore.show(user)
elif mode == "📖 동화 읽기":
    reader.show(user)
