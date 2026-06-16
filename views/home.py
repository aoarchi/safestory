import streamlit as st
import requests

_HIDE_CHROME = """
<style>
header[data-testid="stHeader"] { display:none !important; }
#MainMenu  { display:none !important; }
footer     { display:none !important; }
section[data-testid="stSidebar"] { display:none !important; }
.block-container { padding:0 !important; max-width:100% !important; }

/* 카테고리 버튼 스타일 */
div[data-testid="stVerticalBlock"] button[kind="secondary"] {
    background: transparent !important;
    border: none !important;
    text-align: left !important;
    padding: 8px 14px !important;
    border-radius: 10px !important;
    font-size: 0.88rem !important;
    color: #4a3728 !important;
    transition: background .15s !important;
}
div[data-testid="stVerticalBlock"] button[kind="secondary"]:hover {
    background: rgba(0,0,0,.07) !important;
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
    # 부족하면 fairy tales로 보충
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
    bid     = book["id"]

    tilts = [-4, 1, -2, 3, 0, -1, 2, -3, 1, 0]
    tilt  = tilts[idx % len(tilts)]
    p     = _PALETTES[idx % len(_PALETTES)]

    if cover:
        inner = f'<img src="{cover}" alt="{short}" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block;">'
    else:
        inner = f"""
        <div style="width:100%;height:100%;
             background:linear-gradient(160deg,{p[0]},{p[1]});
             display:flex;flex-direction:column;
             justify-content:space-between;padding:14px 10px;">
          <span style="color:#fff;font-size:.65rem;font-weight:700;
            line-height:1.45;text-align:center;opacity:.95;">{short}</span>
          <span style="color:rgba(255,255,255,.65);font-size:.55rem;
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
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#f0e6d3;padding:24px 16px 60px;font-family:-apple-system,sans-serif;}}
  .grid{{display:flex;flex-wrap:wrap;gap:26px;justify-content:flex-start;}}
  .book{{width:112px;height:164px;border-radius:2px 6px 6px 2px;overflow:hidden;
         box-shadow:2px 4px 12px rgba(0,0,0,.22),0 1px 3px rgba(0,0,0,.1);
         cursor:pointer;transition:transform .2s ease,box-shadow .2s ease;
         flex-shrink:0;position:relative;background:#ddd;}}
  .spine{{position:absolute;left:0;top:0;bottom:0;width:7px;
          background:rgba(0,0,0,.18);z-index:2;}}
  .book:hover{{transform:rotate(0deg) translateY(-12px) scale(1.07) !important;
               box-shadow:4px 20px 40px rgba(0,0,0,.28);z-index:30;}}
</style>
</head>
<body><div class="grid">{cards}</div></body>
</html>"""


def show(user: dict):
    st.markdown(_HIDE_CHROME, unsafe_allow_html=True)

    # 현재 카테고리
    sel_key = st.session_state.get("cat_key", "bedtime")
    sel_cat = next((c for c in CATEGORIES if c["key"] == sel_key), CATEGORIES[0])

    # ── 레이아웃: 카테고리 사이드 | 책 그리드 ────────────────────────────────
    col_cat, col_books = st.columns([1, 5], gap="small")

    with col_cat:
        # 최상단 — 설정 접근
        st.markdown(
            "<div style='padding:16px 0 8px 10px;"
            "font-size:1.3rem;font-weight:800;color:#3d2b1f;'>📚</div>",
            unsafe_allow_html=True,
        )
        if st.button("⚙️ 설정", key="gear_btn", use_container_width=True):
            st.session_state.show_nav = not st.session_state.get("show_nav", False)
            st.rerun()

        st.markdown(
            "<div style='padding:16px 0 6px 4px;"
            "font-size:.7rem;font-weight:700;color:#8b6f5e;"
            "letter-spacing:.08em;text-transform:uppercase;'>카테고리</div>",
            unsafe_allow_html=True,
        )

        for cat in CATEGORIES:
            is_sel = cat["key"] == sel_key
            label  = cat["name"]
            style  = (
                "background:rgba(0,0,0,.09);font-weight:700;"
                if is_sel else ""
            )
            st.markdown(
                f"<style>#cat_{cat['key']} button{{text-align:left !important;"
                f"{style}}}</style>",
                unsafe_allow_html=True,
            )
            if st.button(label, key=f"cat_{cat['key']}", use_container_width=True):
                st.session_state.cat_key = cat["key"]
                st.rerun()

    with col_books:
        # 설정 내비게이션
        if st.session_state.get("show_nav"):
            st.markdown(
                f"<div style='padding:8px 0 4px;"
                f"font-size:.8rem;color:#666;'>다른 화면으로 이동</div>",
                unsafe_allow_html=True,
            )
            ncols = st.columns(5)
            nav = [("👨‍👩‍👧 부모","parent"),("👶 아이","child"),
                   ("📚 도서관","library"),("🌍 큐레이터","explore"),("📖 읽기","reader")]
            for nc, (lbl, mode) in zip(ncols, nav):
                with nc:
                    if st.button(lbl, use_container_width=True):
                        st.session_state.app_mode = mode
                        st.session_state.show_nav = False
                        st.rerun()
            st.divider()

        # 카테고리 제목
        st.markdown(
            f"<div style='padding:16px 0 4px;"
            f"font-size:1.4rem;font-weight:800;color:#3d2b1f;'>"
            f"{sel_cat['name']}</div>",
            unsafe_allow_html=True,
        )

        # 책 불러오기
        with st.spinner("책 불러오는 중..."):
            books = _books(sel_cat["topic"], 32)

        st.components.v1.html(_grid_html(books), height=1600, scrolling=False)
