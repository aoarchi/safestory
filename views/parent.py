import streamlit as st
import db
import youtube as yt


def show(user: dict):
    with st.sidebar:
        st.markdown(f"### 👋 {user['display_name'] or user['username']}")
        section = st.radio(
            "메뉴",
            ["📋 플레이리스트", "👶 아이 PIN", "👤 프로필"],
            label_visibility="collapsed",
        )
        st.divider()
        if st.button("🚪 로그아웃", use_container_width=True):
            import auth
            auth.logout()

    if section == "📋 플레이리스트":
        _playlists(user)
    elif section == "👶 아이 PIN":
        _pin(user)
    elif section == "👤 프로필":
        _profile(user)


# ── Playlist section ────────────────────────────────────────────────────────

def _playlists(user: dict):
    st.title("📋 플레이리스트 관리")

    with st.expander("➕ 새 플레이리스트 만들기"):
        with st.form("new_pl"):
            name = st.text_input("이름", placeholder="예: 잠자리 동화 모음")
            desc = st.text_area("설명 (선택)", height=68)
            is_pub = st.checkbox("공개 — 다른 부모들도 볼 수 있어요")
            if st.form_submit_button("만들기", use_container_width=True, type="primary"):
                if name.strip():
                    db.create_playlist(user["id"], name.strip(), desc, is_pub)
                    st.success(f"'{name}' 만들었어요!")
                    st.rerun()
                else:
                    st.error("이름을 입력해주세요.")

    playlists = db.get_user_playlists(user["id"])
    if not playlists:
        st.info("아직 플레이리스트가 없어요. 위에서 만들어보세요!")
        return

    labels = [f"{'🌐' if p['is_public'] else '🔒'}  {p['name']}" for p in playlists]
    idx = st.selectbox("플레이리스트 선택", range(len(playlists)), format_func=lambda i: labels[i])
    pl = playlists[idx]

    col_pub, col_del = st.columns([3, 1])
    with col_pub:
        new_pub = st.toggle("공개", value=bool(pl["is_public"]), key=f"pub_{pl['id']}")
        if new_pub != bool(pl["is_public"]):
            db.set_playlist_public(pl["id"], user["id"], new_pub)
            st.rerun()
    with col_del:
        if st.button("🗑️ 삭제", key=f"del_pl_{pl['id']}"):
            st.session_state[f"confirm_{pl['id']}"] = True

    if st.session_state.get(f"confirm_{pl['id']}"):
        st.warning(f"**'{pl['name']}'** 플레이리스트와 영상을 모두 삭제할까요?")
        c1, c2 = st.columns(2)
        if c1.button("네, 삭제", type="primary", use_container_width=True):
            db.delete_playlist(pl["id"], user["id"])
            st.session_state.pop(f"confirm_{pl['id']}", None)
            st.rerun()
        if c2.button("취소", use_container_width=True):
            st.session_state.pop(f"confirm_{pl['id']}", None)
            st.rerun()
        return

    if pl["description"]:
        st.caption(f"📝 {pl['description']}")

    st.divider()
    _add_video(pl)
    st.divider()
    _video_list(pl)


def _add_video(pl: dict):
    st.subheader("🎬 영상 추가")
    with st.form("add_v"):
        url = st.text_input("유튜브 URL", placeholder="https://www.youtube.com/watch?v=...")
        submitted = st.form_submit_button("미리보기", use_container_width=True, type="primary")

    if submitted:
        if not url.strip():
            st.error("URL을 입력해주세요.")
        else:
            vid_id = yt.extract_id(url.strip())
            if not vid_id:
                st.error("올바른 유튜브 URL을 입력해주세요.")
            elif db.video_exists(pl["id"], vid_id):
                st.warning("이미 추가된 영상입니다.")
            else:
                info = yt.get_info(vid_id)
                st.session_state.preview = {
                    "url": url.strip(),
                    "id": vid_id,
                    "title": info["title"],
                    "thumbnail": info["thumbnail"],
                    "pl_id": pl["id"],
                }

    prev = st.session_state.get("preview")
    if prev and prev.get("pl_id") == pl["id"]:
        st.markdown("#### 미리보기")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image(prev["thumbnail"], use_container_width=True)
        with c2:
            st.markdown(f"**{prev['title'] or '(제목 없음)'}**")
            st.caption(prev["url"])

        st.components.v1.html(yt.embed_html(prev["id"], height=340), height=350)

        b1, b2 = st.columns(2)
        if b1.button("✅ 승인 목록에 추가", type="primary", use_container_width=True):
            db.add_video(pl["id"], prev["url"], prev["id"], prev["title"], prev["thumbnail"])
            st.session_state.pop("preview", None)
            st.success("추가했어요!")
            st.rerun()
        if b2.button("❌ 취소", use_container_width=True):
            st.session_state.pop("preview", None)
            st.rerun()


def _video_list(pl: dict):
    videos = db.get_playlist_videos(pl["id"])
    st.subheader(f"📺 승인된 영상 ({len(videos)}개)")

    if not videos:
        st.info("아직 추가된 영상이 없어요.")
        return

    for v in videos:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 1])
            with c1:
                st.image(v["thumbnail"], use_container_width=True)
            with c2:
                st.markdown(f"**{v['title'] or '제목 없음'}**")
                st.caption(v["youtube_url"])
            with c3:
                if st.button("🗑️", key=f"del_v_{v['id']}"):
                    db.delete_video(v["id"], pl["id"])
                    st.rerun()


# ── PIN section ─────────────────────────────────────────────────────────────

def _pin(user: dict):
    st.title("👶 아이 PIN 번호 설정")
    st.info("아이가 시청 모드로 진입할 때 사용하는 4자리 숫자입니다.")

    if user.get("pin"):
        st.success("현재 PIN이 설정되어 있습니다.")
    else:
        st.warning("아직 PIN이 설정되지 않았어요.")

    with st.form("pin_form"):
        p1 = st.text_input("새 PIN (4자리 숫자)", max_chars=4, placeholder="0000")
        p2 = st.text_input("PIN 확인", max_chars=4, placeholder="0000", type="password")
        if st.form_submit_button("저장", use_container_width=True, type="primary"):
            if not p1.isdigit() or len(p1) != 4:
                st.error("숫자 4자리를 입력해주세요.")
            elif p1 != p2:
                st.error("PIN 번호가 일치하지 않습니다.")
            else:
                db.update_pin(user["id"], p1)
                st.session_state.user["pin"] = p1
                st.success("PIN을 저장했어요!")


# ── Profile section ─────────────────────────────────────────────────────────

def _profile(user: dict):
    st.title("👤 프로필 설정")

    ages = ["", "0-2세", "3-5세", "6-8세", "9-12세"]
    cur_age = user.get("child_age", "") or ""

    with st.form("profile"):
        name = st.text_input("닉네임", value=user.get("display_name", ""))
        age = st.selectbox("자녀 연령대", ages, index=ages.index(cur_age) if cur_age in ages else 0)
        bio = st.text_area("큐레이터 소개", value=user.get("bio", ""), height=100)
        if st.form_submit_button("저장", use_container_width=True, type="primary"):
            db.update_profile(user["id"], name, age, bio)
            st.session_state.user.update({"display_name": name, "child_age": age, "bio": bio})
            st.success("프로필을 저장했어요!")
