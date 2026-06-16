import streamlit as st
import requests
import db

# ── 테마 정의 ──────────────────────────────────────────────────────────────────
THEMES = {
    "🌙 잠자기 전 동화":  "fairy+tales",
    "🦁 동물 이야기":     "animals",
    "🗡️ 신나는 모험":    "adventure+stories",
    "📖 우화·교훈":       "fables",
    "🌍 세계 전래동화":   "folklore",
    "🧒 어린이 고전":     "children%27s+stories",
}


@st.cache_data(ttl=1800, show_spinner=False)
def _fetch(topic: str, page: int = 1) -> dict:
    try:
        resp = requests.get(
            "https://gutendex.com/books/",
            params={"topic": topic, "languages": "en", "page": page},
            timeout=10,
        )
        return resp.json()
    except Exception:
        return {"results": [], "count": 0, "next": None}


def _cover(book: dict) -> str:
    return book.get("formats", {}).get("image/jpeg", "")


def _author(book: dict) -> str:
    authors = book.get("authors", [])
    return authors[0]["name"] if authors else "Unknown"


# ── 메인 진입 ──────────────────────────────────────────────────────────────────

def show(user: dict):
    if "book_cart" not in st.session_state:
        st.session_state.book_cart = []

    cart     = st.session_state.book_cart
    cart_ids = {b["id"] for b in cart}

    # 사이드바
    with st.sidebar:
        st.markdown("### 📚 동화 도서관")
        st.divider()
        if cart:
            st.markdown(f"**🛒 장바구니 {len(cart)}권**")
            if st.button("장바구니 보기", use_container_width=True, type="primary"):
                st.session_state.lib_view = "cart"
            if st.button("← 계속 담기", use_container_width=True):
                st.session_state.lib_view = "browse"
        else:
            st.caption("책을 골라 장바구니에 담아보세요!")

    view = st.session_state.get("lib_view", "browse")

    if view == "cart":
        _cart_view(user, cart)
    else:
        _browse_view(cart, cart_ids)


# ── 브라우즈 뷰 ────────────────────────────────────────────────────────────────

def _browse_view(cart: list, cart_ids: set):
    st.title("📚 동화 도서관")
    st.caption("Project Gutenberg 공개 도메인 동화 · 부모가 선택 후 아이에게 공개됩니다")

    # 테마 + 페이지
    col_theme, col_page = st.columns([3, 1])
    with col_theme:
        theme_label = st.selectbox("테마", list(THEMES.keys()), label_visibility="collapsed")
    topic = THEMES[theme_label]

    if "lib_page" not in st.session_state:
        st.session_state.lib_page = 1

    with st.spinner("책 불러오는 중..."):
        data  = _fetch(topic, st.session_state.lib_page)
        books = data.get("results", [])

    total = data.get("count", 0)
    st.caption(f"총 {total}권  ·  {st.session_state.lib_page}페이지")

    if not books:
        st.info("책을 불러올 수 없어요. 잠시 후 다시 시도해주세요.")
        return

    # 4열 그리드
    cols = st.columns(4, gap="medium")
    for i, book in enumerate(books):
        with cols[i % 4]:
            _book_card(book, cart_ids)

    # 페이지네이션
    st.divider()
    p1, p2, p3 = st.columns([1, 2, 1])
    with p1:
        if st.session_state.lib_page > 1:
            if st.button("← 이전", use_container_width=True):
                st.session_state.lib_page -= 1
                st.rerun()
    with p3:
        if data.get("next"):
            if st.button("다음 →", use_container_width=True):
                st.session_state.lib_page += 1
                st.rerun()


def _book_card(book: dict, cart_ids: set):
    bid    = book["id"]
    title  = book["title"]
    short  = title[:36] + "…" if len(title) > 36 else title
    author = _author(book)
    cover  = _cover(book)
    in_cart = bid in cart_ids

    with st.container(border=True):
        if cover:
            st.image(cover, use_container_width=True)
        else:
            # 표지 없는 책 — 컬러 플레이스홀더
            color = f"hsl({bid % 360}, 60%, 55%)"
            st.markdown(
                f"""<div style="background:{color};height:180px;border-radius:8px;
                    display:flex;align-items:center;justify-content:center;padding:12px;">
                    <span style="color:white;font-size:.8rem;font-weight:700;
                    text-align:center;word-break:break-word;">{short}</span>
                    </div>""",
                unsafe_allow_html=True,
            )

        st.markdown(f"**{short}**")
        st.caption(author)

        if in_cart:
            st.button("✓ 담김", key=f"in_{bid}", disabled=True, use_container_width=True)
        else:
            if st.button("🛒 담기", key=f"add_{bid}", use_container_width=True, type="primary"):
                st.session_state.book_cart.append({
                    "id":     bid,
                    "title":  title,
                    "author": author,
                    "cover":  cover,
                })
                st.rerun()


# ── 장바구니 뷰 ────────────────────────────────────────────────────────────────

def _cart_view(user: dict, cart: list):
    st.title("🛒 장바구니")

    if not cart:
        st.info("담긴 책이 없어요.")
        if st.button("← 도서관으로"):
            st.session_state.lib_view = "browse"
            st.rerun()
        return

    for i, book in enumerate(cart):
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 5, 1])
            with c1:
                if book["cover"]:
                    st.image(book["cover"], use_container_width=True)
                else:
                    color = f"hsl({book['id'] % 360}, 60%, 55%)"
                    st.markdown(
                        f'<div style="background:{color};height:80px;border-radius:6px;"></div>',
                        unsafe_allow_html=True,
                    )
            with c2:
                st.markdown(f"**{book['title']}**")
                st.caption(book["author"])
            with c3:
                if st.button("❌", key=f"rm_{i}"):
                    st.session_state.book_cart.pop(i)
                    st.rerun()

    st.divider()
    st.info(
        "승인하면 아이 읽기 목록에 추가됩니다.\n"
        "한국어 번역·낭독은 아이 읽기 화면에서 생성할 수 있어요."
    )

    if st.button(
        f"✅ {len(cart)}권 전체 승인 — 아이 읽기 목록에 추가",
        type="primary",
        use_container_width=True,
    ):
        added = 0
        for book in cart:
            ok = db.add_approved_book(
                user["id"], book["id"], book["title"], book["author"], book["cover"]
            )
            if ok:
                added += 1
        st.session_state.book_cart = []
        st.session_state.lib_view  = "browse"
        st.success(f"🎉 {added}권을 아이 읽기 목록에 추가했어요!")
        st.balloons()
        st.rerun()
