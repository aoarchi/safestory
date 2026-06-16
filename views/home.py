import streamlit as st
import requests

_HIDE_CHROME = """
<style>
header[data-testid="stHeader"] { display:none !important; }
#MainMenu  { display:none !important; }
footer     { display:none !important; }
section[data-testid="stSidebar"] { display:none !important; }
.block-container { padding:0 !important; max-width:100% !important; }
</style>
"""

# 배경 팔레트 — 표지 없는 책에 사용
_PALETTES = [
    ("#e8c4a0","#c9956a"),("_d4e8c2","#8fbe6e"),("#c4cfe8","#6a82be"),
    ("#e8c4d4","#be6a95"),("#e8dfc4","#bea96a"),("#c4e8e8","#6abebe"),
    ("#d4c4e8","#8a6abe"),("#e8c4c4","#be6a6a"),("#c4e8d0","#6abe8a"),
    ("#e0e8c4","#9abe6a"),
]


@st.cache_data(ttl=3600, show_spinner=False)
def _books(n: int = 30) -> list:
    collected, seen = [], set()
    for topic in ["fairy+tales", "children%27s+stories", "fables", "folklore"]:
        if len(collected) >= n:
            break
        try:
            r = requests.get(
                "https://gutendex.com/books/",
                params={"topic": topic, "languages": "en", "page": 1},
                timeout=10,
            )
            for b in r.json().get("results", []):
                if b["id"] not in seen:
                    seen.add(b["id"])
                    collected.append(b)
                    if len(collected) >= n:
                        break
        except Exception:
            pass
    return collected[:n]


def _card(book: dict, idx: int) -> str:
    cover  = book.get("formats", {}).get("image/jpeg", "")
    title  = book["title"]
    short  = title[:30] + "…" if len(title) > 30 else title
    authors = book.get("authors", [])
    author = authors[0]["name"].split(",")[0] if authors else ""
    bid    = book["id"]

    # 살짝 기울기 — 자연스러운 놓여진 느낌
    tilts = [-4, 1, -2, 3, 0, -1, 2, -3, 1, 0]
    tilt  = tilts[idx % len(tilts)]

    p = _PALETTES[idx % len(_PALETTES)]
    bg1, bg2 = p[0], p[1]

    if cover:
        inner = f'<img src="{cover}" alt="{short}" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block;">'
    else:
        inner = f"""
        <div style="width:100%;height:100%;
             background:linear-gradient(160deg,{bg1},{bg2});
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


def show(user: dict):
    st.markdown(_HIDE_CHROME, unsafe_allow_html=True)

    with st.spinner(""):
        books = _books(30)

    cards_html = "\n".join(_card(b, i) for i, b in enumerate(books))

    # 우상단 설정 아이콘 (Streamlit 버튼 — HTML 밖에 배치)
    _, col_gear = st.columns([20, 1])
    with col_gear:
        if st.button("⚙️", help="설정 / 부모 관리", key="gear"):
            st.session_state.show_nav = not st.session_state.get("show_nav", False)
            st.rerun()

    # 설정 드롭다운
    if st.session_state.get("show_nav"):
        cols = st.columns(5)
        labels = ["👨‍👩‍👧 부모", "👶 아이 모드", "📚 도서관", "🌍 큐레이터", "📖 읽기"]
        modes  = ["parent", "child",    "library",  "explore",   "reader"]
        for col, label, mode in zip(cols, labels, modes):
            with col:
                if st.button(label, use_container_width=True):
                    st.session_state.app_mode = mode
                    st.session_state.show_nav = False
                    st.rerun()

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{
    background:#f0e6d3;
    font-family:-apple-system,BlinkMacSystemFont,sans-serif;
    padding:32px 24px 64px;
  }}
  .grid{{
    display:flex;
    flex-wrap:wrap;
    gap:32px;
    justify-content:center;
    max-width:1200px;
    margin:0 auto;
  }}
  .book{{
    width:116px;
    height:168px;
    border-radius:2px 6px 6px 2px;
    overflow:hidden;
    box-shadow:2px 4px 12px rgba(0,0,0,.22),
               0 1px 3px rgba(0,0,0,.12);
    cursor:pointer;
    transition:transform .2s ease, box-shadow .2s ease;
    flex-shrink:0;
    position:relative;
    background:#ddd;
  }}
  .spine{{
    position:absolute;
    left:0;top:0;bottom:0;width:7px;
    background:rgba(0,0,0,.18);
    z-index:2;
  }}
  .book:hover{{
    transform:rotate(0deg) translateY(-12px) scale(1.07) !important;
    box-shadow:4px 20px 40px rgba(0,0,0,.28);
    z-index:30;
  }}
</style>
</head>
<body>
  <div class="grid">
    {cards_html}
  </div>
</body>
</html>"""

    st.components.v1.html(html, height=1700, scrolling=False)
