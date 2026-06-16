import json
import streamlit as st
import requests
import db

_HIDE_CHROME = """
<style>
header[data-testid="stHeader"] { display:none !important; }
#MainMenu  { display:none !important; }
footer     { display:none !important; }
section[data-testid="stSidebar"] { display:none !important; }
.block-container { padding:0 !important; max-width:100% !important; }
/* 전체 앱 배경 베이지 */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stVerticalBlock"], section.main > div {
    background: #f0e6d3 !important;
}
/* baseweb 입력 내부 padding 제거 */
div[data-baseweb="base-input"] { padding: 0 !important; }
/* 검색창 — Streamlit 기본 스타일 완전 제거 */
div[data-testid="stTextInput"],
div[data-testid="stTextInput"] > div,
div[data-baseweb="input"],
div[data-baseweb="base-input"] {
    background: #f0e6d3 !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}
div[data-testid="stTextInput"] { padding-left: 16px !important; }
div[data-testid="stTextInput"] input {
    background: #f0e6d3 !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    outline: none !important;
    padding: 10px 4px !important;
    font-size: 1rem !important;
    color: #3d2b1f !important;
    letter-spacing: .06em !important;
}
div[data-testid="stTextInput"] input:focus {
    box-shadow: none !important;
    border: none !important;
    outline: none !important;
}
div[data-testid="stTextInput"] input::placeholder { color: #b09a8a !important; }
div[data-testid="stTextInput"] > label { display:none !important; }
/* Streamlit 실행 중 스피너(우상단 돌아가는 아이콘) 숨기기 */
[data-testid="stStatusWidget"] { display:none !important; }
</style>
"""

_KEYWORD_MAP = {
    "잠자기": "fairy+tales",      "잠자리": "fairy+tales",
    "포근": "fairy+tales",        "졸려": "fairy+tales",
    "모험": "adventure+stories",  "여행": "adventure+stories",
    "신나": "adventure+stories",  "용감": "adventure+stories",
    "차분": "nature",             "힐링": "nature",
    "자연": "nature",             "평화": "nature",
    "동물": "animals",            "귀여": "animals",
    "웃긴": "humor",              "재미있": "humor",
    "유머": "humor",              "웃음": "humor",
    "교훈": "fables",             "우화": "fables",
    "배움": "fables",             "이솝": "fables",
    "전래": "folklore",           "세계": "folklore",
    "공부": "children%27s+stories",
    "가족": "children%27s+stories",
    "비 오": "fairy+tales",       "비오": "fairy+tales",
}

_TOPIC_DESC = {
    "fairy+tales":           "포근하고 따뜻한 동화",
    "adventure+stories":     "두근두근 모험 이야기",
    "nature":                "자연 속 조용한 이야기",
    "animals":               "귀여운 동물 친구들",
    "humor":                 "빵 터지는 웃긴 이야기",
    "fables":                "지혜가 담긴 우화",
    "folklore":              "세계 각국 전래동화",
    "children%27s+stories":  "어린이를 위한 이야기",
}


def _fb(bid: int, title: str, author: str) -> dict:
    return {
        "id": bid,
        "title": title,
        "authors": [{"name": author}],
        "formats": {
            "image/jpeg": f"https://www.gutenberg.org/cache/epub/{bid}/pg{bid}.cover.medium.jpg"
        },
    }

_FALLBACK_BOOKS = [
    _fb(2591,  "Grimms' Fairy Tales",                     "Grimm, Jacob"),
    _fb(1597,  "Andersen's Fairy Tales",                  "Andersen, H. C."),
    _fb(11,    "Alice's Adventures in Wonderland",         "Carroll, Lewis"),
    _fb(55,    "The Wonderful Wizard of Oz",               "Baum, L. Frank"),
    _fb(236,   "The Jungle Book",                          "Kipling, Rudyard"),
    _fb(289,   "The Wind in the Willows",                  "Grahame, Kenneth"),
    _fb(120,   "Treasure Island",                          "Stevenson, Robert Louis"),
    _fb(74,    "The Adventures of Tom Sawyer",             "Twain, Mark"),
    _fb(76,    "Adventures of Huckleberry Finn",           "Twain, Mark"),
    _fb(21,    "Aesop's Fables",                           "Aesop"),
    _fb(46,    "A Christmas Carol",                        "Dickens, Charles"),
    _fb(521,   "Robinson Crusoe",                          "Defoe, Daniel"),
    _fb(829,   "Gulliver's Travels",                       "Swift, Jonathan"),
    _fb(514,   "Little Women",                             "Alcott, Louisa May"),
    _fb(271,   "Black Beauty",                             "Sewell, Anna"),
    _fb(113,   "The Secret Garden",                        "Burnett, Frances Hodgson"),
    _fb(164,   "Twenty Thousand Leagues Under the Sea",    "Verne, Jules"),
    _fb(103,   "Around the World in Eighty Days",          "Verne, Jules"),
    _fb(215,   "The Call of the Wild",                     "London, Jack"),
    _fb(910,   "White Fang",                               "London, Jack"),
    _fb(964,   "The Merry Adventures of Robin Hood",       "Pyle, Howard"),
    _fb(1818,  "The Story of Doctor Dolittle",             "Lofting, Hugh"),
    _fb(3750,  "Swiss Family Robinson",                    "Wyss, Johann David"),
    _fb(16,    "Peter Pan",                                "Barrie, J. M."),
    _fb(2852,  "The Hound of the Baskervilles",            "Doyle, Arthur Conan"),
    _fb(1661,  "The Adventures of Sherlock Holmes",        "Doyle, Arthur Conan"),
    _fb(42,    "The Strange Case of Dr Jekyll and Mr Hyde","Stevenson, Robert Louis"),
    _fb(1400,  "Great Expectations",                       "Dickens, Charles"),
    _fb(730,   "Oliver Twist",                             "Dickens, Charles"),
    _fb(1184,  "The Count of Monte Cristo",                "Dumas, Alexandre"),
    _fb(749,   "Five Little Peppers and How They Grew",    "Sidney, Margaret"),
    _fb(203,   "Uncle Tom's Cabin",                        "Stowe, Harriet Beecher"),
]


def _keyword_fallback(query: str) -> str:
    for kw, topic in _KEYWORD_MAP.items():
        if kw in query:
            return topic
    return "fairy+tales"


def _gpt_topic(query: str) -> tuple[str, str]:
    """GPT로 기분 → Gutenberg 토픽 매핑. 실패하면 키워드 폴백."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a children's audiobook recommender. "
                        "Map the user's mood or situation to one Gutenberg topic. "
                        "Topics: fairy+tales, adventure+stories, nature, animals, "
                        "humor, fables, folklore, children%27s+stories. "
                        'Reply ONLY with JSON: {"topic":"...","desc_ko":"...짧은 한국어 설명..."}'
                    ),
                },
                {"role": "user", "content": query},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
        return data["topic"], data["desc_ko"]
    except Exception:
        t = _keyword_fallback(query)
        return t, _TOPIC_DESC.get(t, "추천 동화")


@st.cache_data(ttl=1800, show_spinner=False)
def _books(topic: str, n: int = 32) -> list:
    collected, seen = [], set()
    page = 1
    while len(collected) < n and page <= 3:
        try:
            r = requests.get(
                "https://gutendex.com/books/",
                params={"topic": topic, "languages": "en", "page": page},
                timeout=8,
            )
            data = r.json()
            for b in data.get("results", []):
                if b["id"] not in seen:
                    seen.add(b["id"])
                    collected.append(b)
            if not data.get("next"):
                break
            page += 1
        except Exception:
            break
    # 부족하면 fairy+tales 로 보충
    if len(collected) < n:
        try:
            r = requests.get(
                "https://gutendex.com/books/",
                params={"topic": "fairy+tales", "languages": "en", "page": 1},
                timeout=8,
            )
            for b in r.json().get("results", []):
                if b["id"] not in seen and len(collected) < n:
                    seen.add(b["id"])
                    collected.append(b)
        except Exception:
            pass
    if not collected:
        return _FALLBACK_BOOKS[:n]
    if len(collected) < n:
        for fb in _FALLBACK_BOOKS:
            if fb["id"] not in seen and len(collected) < n:
                collected.append(fb)
    return collected[:n]


def _book_grid(books: list, user: dict) -> None:
    n_cols = 8
    for row_start in range(0, len(books), n_cols):
        row = books[row_start:row_start + n_cols]
        cols = st.columns(n_cols, gap="small")
        for col, book in zip(cols, row):
            bid    = book["id"]
            cover  = book.get("formats", {}).get("image/jpeg", "")
            title  = book["title"]
            short  = title[:14] + "…" if len(title) > 14 else title
            authors = book.get("authors", [])
            author  = authors[0]["name"].split(",")[0] if authors else ""

            with col:
                if cover:
                    st.image(cover, use_container_width=True)
                else:
                    hue = bid % 360
                    st.markdown(
                        f'<div style="background:hsl({hue},55%,58%);height:90px;'
                        f'border-radius:3px 6px 6px 3px;display:flex;align-items:center;'
                        f'justify-content:center;padding:6px;margin-bottom:4px;'
                        f'box-shadow:2px 4px 8px rgba(0,0,0,.18);">'
                        f'<span style="color:#fff;font-size:.55rem;font-weight:700;'
                        f'text-align:center;line-height:1.3;">{short}</span></div>',
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    f"<div style='font-size:.6rem;font-weight:700;line-height:1.2;"
                    f"margin:3px 0 1px;'>{short}</div>"
                    f"<div style='font-size:.55rem;color:#888;margin-bottom:3px;'>{author}</div>",
                    unsafe_allow_html=True,
                )

                if st.button("읽기", key=f"read_{bid}", use_container_width=True):
                    db.add_approved_book(user["id"], bid, title, author, cover)
                    st.session_state["quick_book_id"] = bid
                    st.session_state.app_mode = "reader"
                    st.rerun()


def show(user: dict):
    st.markdown(_HIDE_CHROME, unsafe_allow_html=True)

    # ── 헤더: columns([10,1]) — gear 오른쪽 고정 ──────────────────────────────
    col_logo, col_gear = st.columns([10, 1])
    with col_logo:
        st.markdown(
            "<div style='padding:18px 0 0 16px;font-size:1.25rem;font-weight:800;"
            "color:#3d2b1f;'>SafeStory</div>",
            unsafe_allow_html=True,
        )
    with col_gear:
        if st.button("⚙️", key="gear"):
            st.session_state.show_nav = not st.session_state.get("show_nav", False)
            st.rerun()

    if st.session_state.get("show_nav"):
        ncols = st.columns(5)
        for nc, (lbl, mode) in zip(ncols, [
            ("부모 관리","parent"),("아이 모드","child"),
            ("도서관","library"),("큐레이터","explore"),("동화 읽기","reader"),
        ]):
            with nc:
                if st.button(lbl, use_container_width=True):
                    st.session_state.app_mode = mode
                    st.session_state.show_nav = False
                    st.rerun()

    # ── 검색창 ─────────────────────────────────────────────────────────────────
    col_search, _ = st.columns([10, 1])
    with col_search:
        st.markdown("<div style='padding-top:10px;'>", unsafe_allow_html=True)
        query = st.text_input(
            "mood",
            placeholder="SEARCH",
            label_visibility="collapsed",
            key="mood_q",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 책 그리드 ─────────────────────────────────────────────────────────────
    if query and query.strip():
        topic, desc = _gpt_topic(query.strip())
        st.markdown(
            f"<div style='background:#f0e6d3;padding:4px 16px 8px;"
            f"font-size:.82rem;color:#8b6f5e;'>"
            f"✦ {desc}</div>",
            unsafe_allow_html=True,
        )
        books = _books(topic, 32)
    else:
        books = _books("fairy+tales", 32)

    st.markdown("<div style='padding:12px 16px 0;'>", unsafe_allow_html=True)
    _book_grid(books, user)
    st.markdown("</div>", unsafe_allow_html=True)
