import streamlit as st
import db


def show(user: dict):
    with st.sidebar:
        st.markdown("### 🌍 큐레이터 둘러보기")
        st.caption("다른 부모님이 골라준 동화 목록을 구경해보세요!")

    st.title("🌍 큐레이터 둘러보기")

    playlists = db.get_public_playlists()
    if not playlists:
        st.info("아직 공개된 플레이리스트가 없어요. 먼저 부모 모드에서 공개 설정을 해보세요!")
        return

    # Age filter
    all_ages = sorted({p["child_age"] for p in playlists if p.get("child_age")})
    ages = ["전체"] + all_ages
    sel_age = st.selectbox("자녀 연령대 필터", ages, label_visibility="visible")

    shown = [p for p in playlists if sel_age == "전체" or p.get("child_age") == sel_age]

    if not shown:
        st.info("해당 연령대의 플레이리스트가 없어요.")
        return

    for pl in shown:
        with st.container(border=True):
            c_info, c_action = st.columns([3, 1])

            with c_info:
                curator = pl.get("display_name") or "익명 큐레이터"
                age_tag = f"  ·  👶 {pl['child_age']}" if pl.get("child_age") else ""
                st.markdown(f"### {pl['name']}")
                st.markdown(f"**{curator}**{age_tag}")

                if pl.get("bio"):
                    st.caption(pl["bio"])
                if pl.get("description"):
                    st.caption(f"📝 {pl['description']}")

                st.caption(
                    f"🎬 영상 **{pl['video_count']}**개  ·  "
                    f"👥 구독 **{pl['subscriber_count']}**명"
                )

                # Thumbnail preview strip
                videos = db.get_playlist_videos(pl["id"])
                if videos:
                    thumb_cols = st.columns(min(len(videos), 4))
                    for j, v in enumerate(videos[:4]):
                        with thumb_cols[j]:
                            st.image(v["thumbnail"], use_container_width=True)
                            title = v["title"] or ""
                            st.caption(title[:18] + "…" if len(title) > 18 else title)

            with c_action:
                st.markdown("<br><br>", unsafe_allow_html=True)
                already = db.is_subscribed(user["id"], pl["id"])
                own = pl.get("user_id") == user["id"] if "user_id" in pl else False

                if own:
                    st.info("내 목록")
                elif already:
                    st.success("✓ 복사됨")
                else:
                    if st.button(
                        "📋 내 목록에\n복사하기",
                        key=f"copy_{pl['id']}",
                        use_container_width=True,
                        type="primary",
                    ):
                        new_name = f"{pl['name']} (복사)"
                        db.copy_playlist(pl["id"], user["id"], new_name)
                        st.success("내 플레이리스트에 추가했어요!")
                        st.rerun()
