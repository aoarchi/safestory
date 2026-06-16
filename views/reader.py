import streamlit as st
import gutenberg as gb
import tts_engine as tts


def show(user: dict):
    with st.sidebar:
        st.markdown("### 📖 동화 읽기")
        st.caption("Project Gutenberg 원문을\n한국어로 번역해서 들어보세요")

    st.title("📖 동화 읽기")
    st.caption("Hans Christian Andersen · Project Gutenberg 공개 도메인")

    # ── API 키 확인 ──────────────────────────────────────────────────────────
    try:
        _ = st.secrets["OPENAI_API_KEY"]
    except Exception:
        st.error("OpenAI API 키가 설정되지 않았습니다. `.streamlit/secrets.toml`에 키를 추가해주세요.")
        st.code('OPENAI_API_KEY = "sk-..."', language="toml")
        return

    # ── 동화 목록 로드 ────────────────────────────────────────────────────────
    with st.spinner("동화 목록 불러오는 중..."):
        stories = gb.fetch_stories()

    if not stories:
        st.error("Gutenberg 서버에 연결할 수 없어요. 잠시 후 다시 시도해주세요.")
        if st.button("🔄 다시 시도"):
            gb.fetch_stories.clear()
            st.rerun()
        return

    available = {k: gb.STORIES_META[k] for k in gb.STORIES_META if k in stories}
    if not available:
        st.error("동화를 파싱할 수 없어요.")
        return

    # ── 동화 선택 ─────────────────────────────────────────────────────────────
    keys   = list(available.keys())
    labels = [f"{available[k][1]}  {available[k][0]}  ({available[k][2]})" for k in keys]

    sel_idx = st.selectbox("동화 선택", range(len(keys)), format_func=lambda i: labels[i])
    sel_key         = keys[sel_idx]
    ko_name, emoji, age = available[sel_key]

    st.markdown(f"## {emoji} {ko_name}")
    st.caption(f"원작: Hans Christian Andersen  ·  권장 연령: {age}  ·  출처: Project Gutenberg (공개 도메인)")

    # ── 파트 선택 ─────────────────────────────────────────────────────────────
    chunks = gb.get_chunks(stories[sel_key])
    if len(chunks) > 1:
        part_idx = st.selectbox(
            f"파트 선택  (총 {len(chunks)}파트)",
            range(len(chunks)),
            format_func=lambda i: f"파트 {i + 1}",
        )
    else:
        part_idx = 0

    eng_chunk  = chunks[part_idx]
    state_base = f"{sel_key}_{part_idx}"

    # ── 생성 버튼 ─────────────────────────────────────────────────────────────
    if st.button("🎧 한국어 번역 + 낭독 생성", type="primary", use_container_width=True):
        with st.spinner("한국어로 번역하는 중... (약 10초)"):
            try:
                ko = tts.translate(eng_chunk)
                st.session_state[f"ko_{state_base}"] = ko
            except Exception as e:
                st.error(f"번역 오류: {e}")
                return

        with st.spinner("음성 생성하는 중... (약 15초)"):
            try:
                audio = tts.speak(st.session_state[f"ko_{state_base}"])
                st.session_state[f"au_{state_base}"] = audio
            except Exception as e:
                st.error(f"음성 생성 오류: {e}")
                return

        st.rerun()

    # ── 결과 표시 ─────────────────────────────────────────────────────────────
    if f"ko_{state_base}" in st.session_state:
        # 오디오 플레이어
        if f"au_{state_base}" in st.session_state:
            st.markdown("#### 🔊 낭독")
            st.audio(st.session_state[f"au_{state_base}"], format="audio/mp3")

        st.divider()

        # 번역문 + 원문 나란히
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🇰🇷 한국어 번역")
            for para in st.session_state[f"ko_{state_base}"].split("\n\n"):
                if para.strip():
                    st.markdown(para.strip())
                    st.markdown("")
        with c2:
            st.markdown("#### 🇬🇧 영어 원문")
            for para in eng_chunk.split("\n\n"):
                if para.strip():
                    st.markdown(para.strip())
                    st.markdown("")
    else:
        # 원문 미리보기
        st.divider()
        st.markdown("#### 🇬🇧 영어 원문 미리보기")
        preview = eng_chunk[:600] + "..." if len(eng_chunk) > 600 else eng_chunk
        st.text(preview)
