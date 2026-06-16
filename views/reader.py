import html
import streamlit as st
import db
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


def _bilingual_reader(eng_chunk: str, state_base: str) -> None:
    ko_key = f"ko_{state_base}"
    au_key = f"au_{state_base}"

    btn1, btn2 = st.columns(2)
    with btn1:
        if st.button("🌏 한국어 번역", type="primary", use_container_width=True,
                     key=f"tr_{state_base}"):
            with st.spinner("번역 중..."):
                try:
                    st.session_state[ko_key] = tts.translate(eng_chunk)
                except Exception as e:
                    st.error(f"번역 오류: {e}")
                    return
            st.rerun()
    with btn2:
        if st.button("🎧 낭독 생성", use_container_width=True,
                     disabled=ko_key not in st.session_state,
                     key=f"sp_{state_base}"):
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
                "text-align:center;color:#bbb;min-height:200px'>"
                "<p>🌏 위 '한국어 번역' 버튼을 누르면<br>여기에 번역이 나타납니다</p></div>",
                unsafe_allow_html=True,
            )


def _show_curated(fetch_fn, meta: dict, source_label: str, tab_key: str) -> None:
    with st.spinner("동화 목록 불러오는 중..."):
        stories = fetch_fn()

    if not stories:
        st.error("Gutenberg 서버에 연결할 수 없어요. 잠시 후 다시 시도해주세요.")
        if st.button("🔄 다시 시도", key=f"retry_{tab_key}"):
            fetch_fn.clear()
            st.rerun()
        return

    available = {k: meta[k] for k in meta if k in stories}
    if not available:
        st.error("동화를 파싱할 수 없어요.")
        return

    keys   = list(available.keys())
    labels = [f"{available[k][1]}  {available[k][0]}  ({available[k][2]})" for k in keys]
    sel_idx = st.selectbox("동화 선택", range(len(keys)),
                           format_func=lambda i: labels[i],
                           key=f"sel_{tab_key}")
    sel_key = keys[sel_idx]
    ko_name, emoji, age = available[sel_key]

    st.markdown(f"## {emoji} {ko_name}")
    st.caption(f"원작: {source_label}  ·  권장 연령: {age}  ·  출처: Project Gutenberg (공개 도메인)")

    chunks = gb.get_chunks(stories[sel_key])
    if len(chunks) > 1:
        part_idx = st.selectbox(
            f"파트 선택  (총 {len(chunks)}파트)", range(len(chunks)),
            format_func=lambda i: f"파트 {i + 1}",
            key=f"part_{tab_key}_{sel_idx}",
        )
    else:
        part_idx = 0

    _bilingual_reader(chunks[part_idx], f"{tab_key}_{sel_key[:20]}_{part_idx}")


def _show_my_books(user: dict) -> None:
    books = db.get_approved_books(user["id"])

    if not books:
        st.info("아직 승인된 책이 없어요. **동화 도서관**에서 책을 골라 승인하면 여기서 읽을 수 있어요!")
        if st.button("📚 동화 도서관으로"):
            st.session_state.app_mode = "library"
            st.rerun()
        return

    labels = [f"📖  {b['title']}  —  {b['author']}" for b in books]
    sel_idx = st.selectbox("책 선택", range(len(books)),
                           format_func=lambda i: labels[i],
                           key="my_book_sel")
    book = books[sel_idx]
    gid  = book["gutenberg_id"]

    col_info, col_cover = st.columns([3, 1])
    with col_info:
        st.markdown(f"## 📖 {book['title']}")
        st.caption(f"저자: {book['author']}  ·  출처: Project Gutenberg (공개 도메인)")
    with col_cover:
        if book.get("cover_url"):
            st.image(book["cover_url"], width=100)

    with st.spinner("책 내용 불러오는 중..."):
        text = gb.fetch_book_text(gid)

    if not text:
        st.error("책 내용을 불러올 수 없어요. 잠시 후 다시 시도해주세요.")
        if st.button("🔄 다시 시도", key="retry_book"):
            gb.fetch_book_text.clear()
            st.rerun()
        return

    chunks = gb.get_chunks(text)
    if len(chunks) > 1:
        part_idx = st.selectbox(
            f"파트 선택  (총 {len(chunks)}파트)", range(len(chunks)),
            format_func=lambda i: f"파트 {i + 1}",
            key=f"my_part_{gid}",
        )
    else:
        part_idx = 0

    _bilingual_reader(chunks[part_idx], f"book_{gid}_{part_idx}")


def show(user: dict):
    with st.sidebar:
        st.markdown("### 📖 동화 읽기")
        st.caption("Project Gutenberg 원문을\n한국어로 번역해서 들어보세요")

    st.title("📖 동화 읽기")
    st.caption("영어 원문과 한국어 번역을 나란히 읽어보세요")

    try:
        _ = st.secrets["OPENAI_API_KEY"]
    except Exception:
        st.error("OpenAI API 키가 설정되지 않았습니다. `.streamlit/secrets.toml`에 키를 추가해주세요.")
        st.code('OPENAI_API_KEY = "sk-..."', language="toml")
        return

    tab_and, tab_eng, tab_my = st.tabs(["🌊 안데르센", "🏰 영국 동화", "📚 내 책장"])

    with tab_and:
        _show_curated(gb.fetch_stories, gb.STORIES_META,
                      "Hans Christian Andersen", "and")

    with tab_eng:
        _show_curated(gb.fetch_english_fairy_tales, gb.ENGLISH_TALES_META,
                      "Flora Annie Steel · English Fairy Tales", "eng")

    with tab_my:
        _show_my_books(user)
