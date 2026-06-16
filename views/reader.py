import html
import streamlit as st
import gutenberg as gb
import tts_engine as tts


def _render_paragraphs(text: str, bg: str) -> None:
    paras = "".join(
        f"<p style='margin:0 0 1em 0'>{html.escape(p.strip())}</p>"
        for p in text.split("\n\n")
        if p.strip()
    )
    st.markdown(
        f"<div style='background:{bg};padding:1.2rem 1.4rem;border-radius:10px;"
        f"line-height:1.9;font-size:1.05rem;min-height:200px'>{paras}</div>",
        unsafe_allow_html=True,
    )


def show(user: dict):
    with st.sidebar:
        st.markdown("### 📖 동화 읽기")
        st.caption("Project Gutenberg 원문을\n한국어로 번역해서 들어보세요")

    st.title("📖 동화 읽기")
    st.caption("영어 원문과 한국어 번역을 나란히 읽어보세요")

    # ── API 키 확인 ───────────────────────────────────────────────────────────
    try:
        _ = st.secrets["OPENAI_API_KEY"]
    except Exception:
        st.error("OpenAI API 키가 설정되지 않았습니다. `.streamlit/secrets.toml`에 키를 추가해주세요.")
        st.code('OPENAI_API_KEY = "sk-..."', language="toml")
        return

    # ── 책 모음 선택 ──────────────────────────────────────────────────────────
    book_choice = st.radio(
        "책 모음",
        ["🌊 Hans Christian Andersen", "🏰 English Fairy Tales"],
        horizontal=True,
        label_visibility="collapsed",
    )
    is_andersen = book_choice.startswith("🌊")

    # ── 동화 목록 로드 ────────────────────────────────────────────────────────
    with st.spinner("동화 목록 불러오는 중..."):
        if is_andersen:
            stories = gb.fetch_stories()
            meta = gb.STORIES_META
            source_label = "Hans Christian Andersen"
        else:
            stories = gb.fetch_english_fairy_tales()
            meta = gb.ENGLISH_TALES_META
            source_label = "Flora Annie Steel · English Fairy Tales"

    if not stories:
        st.error("Gutenberg 서버에 연결할 수 없어요. 잠시 후 다시 시도해주세요.")
        clear_fn = gb.fetch_stories if is_andersen else gb.fetch_english_fairy_tales
        if st.button("🔄 다시 시도"):
            clear_fn.clear()
            st.rerun()
        return

    available = {k: meta[k] for k in meta if k in stories}
    if not available:
        st.error("동화를 파싱할 수 없어요.")
        return

    # ── 동화 선택 ─────────────────────────────────────────────────────────────
    keys   = list(available.keys())
    labels = [f"{available[k][1]}  {available[k][0]}  ({available[k][2]})" for k in keys]

    sel_idx = st.selectbox("동화 선택", range(len(keys)), format_func=lambda i: labels[i])
    sel_key = keys[sel_idx]
    ko_name, emoji, age = available[sel_key]

    st.markdown(f"## {emoji} {ko_name}")
    st.caption(
        f"원작: {source_label}  ·  권장 연령: {age}  ·  출처: Project Gutenberg (공개 도메인)"
    )

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
    ko_key     = f"ko_{state_base}"
    au_key     = f"au_{state_base}"

    # ── 액션 버튼 ─────────────────────────────────────────────────────────────
    btn1, btn2 = st.columns(2)
    with btn1:
        if st.button("🌏 한국어 번역", type="primary", use_container_width=True):
            with st.spinner("번역 중..."):
                try:
                    st.session_state[ko_key] = tts.translate(eng_chunk)
                except Exception as e:
                    st.error(f"번역 오류: {e}")
                    return
            st.rerun()
    with btn2:
        tts_disabled = ko_key not in st.session_state
        if st.button("🎧 낭독 생성", use_container_width=True, disabled=tts_disabled):
            with st.spinner("음성 생성 중..."):
                try:
                    st.session_state[au_key] = tts.speak(st.session_state[ko_key])
                except Exception as e:
                    st.error(f"음성 오류: {e}")
                    return
            st.rerun()

    if au_key in st.session_state:
        st.audio(st.session_state[au_key], format="audio/mp3")

    st.divider()

    # ── 양쪽 페이지: 영어 LEFT / 한국어 RIGHT ────────────────────────────────
    c_eng, c_ko = st.columns(2)

    with c_eng:
        st.markdown("#### 🇬🇧 영어 원문")
        _render_paragraphs(eng_chunk, "#f9f9f9")

    with c_ko:
        st.markdown("#### 🇰🇷 한국어 번역")
        if ko_key in st.session_state:
            _render_paragraphs(st.session_state[ko_key], "#fff8f0")
        else:
            st.markdown(
                "<div style='background:#fff8f0;padding:2rem;border-radius:10px;"
                "text-align:center;color:#bbb;min-height:200px;display:flex;"
                "align-items:center;justify-content:center'>"
                "<p>🌏 위 '한국어 번역' 버튼을 누르면<br>여기에 번역이 나타납니다</p></div>",
                unsafe_allow_html=True,
            )
