import streamlit as st
import requests

_HIDE_CHROME = """
<style>
header[data-testid="stHeader"] { display:none !important; }
#MainMenu  { display:none !important; }
footer     { display:none !important; }
section[data-testid="stSidebar"] { display:none !important; }
.block-container { padding:0 !important; max-width:100% !important; }

/* 카테고리 pills 스타일 */
div[data-testid="stRadio"] > div {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    gap: 8px !important;
    padding: 12px 16px 4px !important;
    background: #f0e6d3 !important;
    scrollbar-width: none !important;
}
div[data-testid="stRadio"] > div::-webkit-scrollbar { display:none !important; }
div[data-testid="stRadio"] label {
    background: #e0d0bc !important;
    border-radius: 20px !important;
    padding: 6px 18px !important;
    white-space: nowrap !important;
    cursor: pointer !important;
    font-size: 0.82rem !important;
    color: #4a3728 !important;
    border: none !important;
    font-weight: 500 !important;
}
div[data-testid="stRadio"] label:has(input:checked) {
    background: #3d2b1f !important;
    color: #fff !important;
    font-weight: 700 !important;
}
div[data-testid="stRadio"] input[type="radio"] { display:none !important; }
div[data-testid="stRadio"] > label { display:none !important; }

/* 설정 버튼 우상단 */
div[data-testid="column"]:last-child button {
    background: transparent !important;
    border: none !important;
    color: #8b6f5e !important;
    font-size: 1.1rem !important;
}
</style>
"""

CATEGORIES = [
    {"key": "bedtime",   "name": "잠자기 전",       "topic": "fairy+tales"},
    {"key": "travel",    "name": "여행하면서",       "topic": "adventure+stories"},
    {"key": "morning",   "name": "신나는 아침",      "topic": "children%27s+stories"},
    {"key": "calm",      "name": "차분하게",         "topic": "nature"},
    {"key": "funny",     "name": "웃긴 이야기",      "topic": "humor"},
    {"key": "animals",   "name": "동물 친구들",      "topic": "animals"},
    {"key": "adventure", "name": "용감한 모험",      "topic": "adventure+stories"},
    {"key": "world",     "name": "세계 전래동화",    "topic": "folklore"},
    {"key": "magic",     "name": "마법 이야기",      "topic": "fairy+tales"},
    {"key": "fables",    "name": "우화·교훈",        "topic": "fables"},
    {"key": "rainy",     "name": "비 오는 날",       "topic": "fairy+tales"},
    {"key": "family",    "name": "가족과 함께",      "topic": "children%27s+stories"},
    {"key": "brave",     "name": "용기가 필요할 때", "topic": "adventure+stories"},
    {"key": "nature",    "name": "자연 이야기",      "topic": "nature"},
    {"key": "classic",   "name": "클래식 동화",      "topic": "fairy+tales"},
]

_PALETTES = [
    ("#e8c4a0","#c9956a"),("#d4e8c2","#8fbe6e"),("#c4cfe8","#6a82be"),
    ("#e8c4d4","#be6a95"),("#e8dfc4","#bea96a"),("#c4e8e8","#6abebe"),
    ("#d4c4e8","#8a6abe"),("#e8c4c4","#be6a6a"),("#c4e8d0","#6abe8a"),
    ("#e0e8c4","#9abe6a"),
]


@st.cache_data(ttl=1800, show_spinner=False)
def _books(topic: str, n: int = 32) -> list:
    collected, seen = [], set()
    page = 1
    while len(collected) < n and page <= 3:
        try:
            r = requests.get(
                "https://gutendex.com/books/",
                params={"topic": topic, "languages": "en", "page": page},
                timeout=10,
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
    # 부족하면 fairy tales 보충
    if len(collected) < n and topic != "fairy+tales":
        try:
            r = requests.get(
                "https://gutendex.com/books/",
                params={"topic": "fairy+tales", "languages": "en", "page": 1},
                timeout=10,
            )
            for b in r.json().get("results", []):
                if b["id"] not in seen and len(collected) < n:
                    seen.add(b["id"])
                    collected.append(b)
        except Exception:
            pass
    return collected[:n]


def _card(book: dict, idx: int) -> str:
    cover   = book.get("formats", {}).get("image/jpeg", "")
    title   = book["title"]
    short   = title[:28] + "…" if len(title) > 28 else title
    authors = book.get("authors", [])
    author  = authors[0]["name"].split(",")[0] if authors else ""

    tilts = [-4, 1, -2, 3, 0, -1, 2, -3, 1, 0]
    tilt  = tilts[idx % len(tilts)]
    p     = _PALETTES[idx % len(_PALETTES)]

    if cover:
        inner = (f'<img src="{cover}" alt="{short}" loading="lazy" '
                 f'style="width:100%;height:100%;object-fit:cover;display:block;">')
    else:
        inner = f"""
        <div style="width:100%;height:100%;
             background:linear-gradient(160deg,{p[0]},{p[1]});
             display:flex;flex-direction:column;
             justify-content:space-between;padding:12px 8px;">
          <span style="color:#fff;font-size:.62rem;font-weight:700;
            line-height:1.4;text-align:center;">{short}</span>
          <span style="color:rgba(255,255,255,.65);font-size:.52rem;
            text-align:center;">{author}</span>
        </div>"""

    return f"""
    <div class="book" style="transform:rotate({tilt}deg);" title="{title}">
      <div class="spine"></div>
      {inner}
    </div>"""


def _grid_html(books: list) -> str:
    cards = "\n".join(_card(b, i) for i, b in enumerate(books))
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{
    background:#f0e6d3;
    padding:20px 16px 60px;
    font-family:-apple-system,sans-serif;
  }}
  .grid{{
    display:grid;
    grid-template-columns:repeat(auto-fill,minmax(108px,1fr));
    gap:24px;
    justify-items:center;
  }}
  .book{{
    width:108px;
    height:157px;
    border-radius:2px 6px 6px 2px;
    overflow:hidden;
    box-shadow:2px 4px 12px rgba(0,0,0,.22),0 1px 3px rgba(0,0,0,.1);
    cursor:pointer;
    transition:transform .2s ease,box-shadow .2s ease;
    position:relative;
    background:#ddd;
  }}
  .spine{{
    position:absolute;left:0;top:0;bottom:0;width:6px;
    background:rgba(0,0,0,.18);z-index:2;
  }}
  .book:hover{{
    transform:rotate(0deg) translateY(-10px) scale(1.06) !important;
    box-shadow:4px 18px 36px rgba(0,0,0,.28);z-index:30;
  }}

  /* 모바일: 4열 고정 */
  @media (max-width:600px){{
    body{{ padding:12px 10px 40px; }}
    .grid{{
      grid-template-columns:repeat(4,1fr);
      gap:10px;
    }}
    .book{{
      width:100%;
      height:0;
      padding-bottom:145%;
      position:relative;
    }}
    .book .spine,
    .book img,
    .book > div{{
      position:absolute;
      top:0;left:0;width:100%;height:100%;
    }}
  }}
</style>
</head>
<body>
  <div class="grid">{cards}</div>
</body>
</html>"""


def show(user: dict):
    st.markdown(_HIDE_CHROME, unsafe_allow_html=True)

    # ── 상단: SafeStory 로고 + 설정 버튼 ────────────────────────────────────
    col_logo, col_gear = st.columns([10, 1])
    with col_logo:
        st.markdown(
            "<div style='padding:14px 16px 0;"
            "font-size:1.2rem;font-weight:800;color:#3d2b1f;"
            "background:#f0e6d3;'>SafeStory</div>",
            unsafe_allow_html=True,
        )
    with col_gear:
        st.markdown("<div style='padding-top:10px;background:#f0e6d3;'>", unsafe_allow_html=True)
        if st.button("⚙️", key="gear"):
            st.session_state.show_nav = not st.session_state.get("show_nav", False)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 설정 내비게이션
    if st.session_state.get("show_nav"):
        ncols = st.columns(5)
        for nc, (lbl, mode) in zip(ncols, [
            ("부모 관리", "parent"), ("아이 모드", "child"),
            ("도서관", "library"), ("큐레이터", "explore"), ("동화 읽기", "reader")
        ]):
            with nc:
                if st.button(lbl, use_container_width=True):
                    st.session_state.app_mode = mode
                    st.session_state.show_nav = False
                    st.rerun()

    # ── 카테고리 가로 탭 ──────────────────────────────────────────────────────
    cat_names = [c["name"] for c in CATEGORIES]
    sel_name  = st.radio(
        "카테고리",
        cat_names,
        horizontal=True,
        label_visibility="collapsed",
        key="cat_radio",
    )
    sel_cat = next(c for c in CATEGORIES if c["name"] == sel_name)

    # ── 책 그리드 ─────────────────────────────────────────────────────────────
    with st.spinner(""):
        books = _books(sel_cat["topic"], 32)

    st.components.v1.html(_grid_html(books), height=1600, scrolling=False)
