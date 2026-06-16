import streamlit as st
import db
import youtube as yt

_CHILD_CSS = """
<style>
/* 사이드바 및 헤더 숨기기 */
section[data-testid="stSidebar"]  { display: none !important; }
header[data-testid="stHeader"]    { display: none !important; }
#MainMenu                          { display: none !important; }
footer                             { display: none !important; }

/* 배경 */
.stApp { background: linear-gradient(135deg, #fff8f0 0%, #f0f4ff 100%); }
.block-container { padding: 1.5rem 2rem !important; }

/* 카드 */
.vid-card {
    background: white;
    border-radius: 18px;
    box-shadow: 0 4px 16px rgba(0,0,0,.08);
    overflow: hidden;
    transition: transform .18s;
}
.vid-card:hover { transform: translateY(-4px); }
</style>
"""


def show(user: dict):
    st.markdown(_CHILD_CSS, unsafe_allow_html=True)

    if not st.session_state.get("child_auth"):
        _pin_screen(user)
        return

    if st.session_state.get("cur_video"):
        _player_screen()
    else:
        _list_screen(user)


# ── PIN screen ───────────────────────────────────────────────────────────────

def _pin_screen(user: dict):
    if not user.get("pin"):
        st.warning("부모님이 아직 PIN을 설정하지 않았어요. 부모 모드에서 PIN을 먼저 설정해주세요.")
        return

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;padding:3rem 0 1.5rem;">
            <div style="font-size:4rem;">🌟</div>
            <h1 style="margin:0.4rem 0 0.2rem;">SafeStory</h1>
            <p style="color:#888;font-size:1rem;">PIN 번호 4자리를 입력해주세요</p>
        </div>
        """, unsafe_allow_html=True)

        pin = st.text_input(
            "", max_chars=4, type="password",
            placeholder="• • • •",
            label_visibility="collapsed",
            key="pin_input",
        )
        st.markdown(
            "<style>input[type='password']{"
            "font-size:2rem!important;text-align:center!important;"
            "letter-spacing:0.6rem!important;border-radius:12px!important;}</style>",
            unsafe_allow_html=True,
        )

        if len(pin) == 4:
            if db.verify_pin(user["id"], pin):
                st.session_state.child_auth = True
                st.rerun()
            else:
                st.error("PIN 번호가 틀렸어요 😢 다시 입력해주세요.")


# ── Video list screen ────────────────────────────────────────────────────────

def _list_screen(user: dict):
    st.markdown("""
    <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:1rem;">
        <span style="font-size:2rem;">📚</span>
        <h2 style="margin:0;">오늘의 동화</h2>
    </div>
    """, unsafe_allow_html=True)

    playlists = db.get_user_playlists(user["id"])
    if not playlists:
        st.info("아직 동화가 없어요. 부모님께 부탁해보세요! 🌸")
        _exit_button()
        return

    # Playlist selector
    if len(playlists) > 1:
        opts = ["✨ 전체 보기"] + [p["name"] for p in playlists]
        chosen = st.selectbox("", opts, label_visibility="collapsed")
    else:
        chosen = "✨ 전체 보기"

    videos = (
        db.get_all_user_videos(user["id"])
        if chosen == "✨ 전체 보기"
        else db.get_playlist_videos(next(p["id"] for p in playlists if p["name"] == chosen))
    )

    if not videos:
        st.info("이 목록에 동화가 없어요 🌱")
        _exit_button()
        return

    # 3-column card grid
    cols = st.columns(3, gap="medium")
    for i, v in enumerate(videos):
        with cols[i % 3]:
            title = v["title"] or "동화"
            short = title[:22] + "…" if len(title) > 22 else title

            st.markdown('<div class="vid-card">', unsafe_allow_html=True)
            st.image(v["thumbnail"], use_container_width=True)
            if st.button(
                f"▶  {short}",
                key=f"play_{v['id']}",
                use_container_width=True,
                type="primary",
            ):
                st.session_state.cur_video = v
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _exit_button()


# ── Player screen ────────────────────────────────────────────────────────────

def _player_screen():
    v = st.session_state.cur_video

    if st.button("← 목록으로", type="secondary"):
        st.session_state.pop("cur_video", None)
        st.rerun()

    st.markdown(f"## {v['title'] or '동화'}")
    st.components.v1.html(yt.embed_html(v["youtube_id"], height=520), height=534)


# ── Helper ───────────────────────────────────────────────────────────────────

def _exit_button():
    if st.button("🔒 나가기 (부모 모드)"):
        st.session_state.pop("child_auth", None)
        st.session_state.pop("cur_video", None)
        st.rerun()
