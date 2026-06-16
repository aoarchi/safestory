import re
import requests
import streamlit as st

# Curated Andersen stories — title as it appears in the Gutenberg text
STORIES_META = {
    "THE LITTLE MERMAID":         ("인어공주",         "🧜‍♀️", "5세 이상"),
    "THUMBELINA":                  ("엄지공주",         "🌸",  "4세 이상"),
    "THE EMPEROR'S NEW CLOTHES":  ("벌거벗은 임금님", "👑",  "4세 이상"),
    "THE UGLY DUCKLING":          ("미운 오리 새끼",  "🦢",  "4세 이상"),
    "THE LITTLE MATCH GIRL":      ("성냥팔이 소녀",   "🕯️",  "6세 이상"),
    "THE STEADFAST TIN SOLDIER":  ("용감한 주석 병정","🪖",  "5세 이상"),
    "THE WILD SWANS":             ("야생 백조",        "🦢",  "5세 이상"),
    "THE NIGHTINGALE":            ("나이팅게일",       "🐦",  "5세 이상"),
}

_TITLE_ORDER = list(STORIES_META.keys())


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stories() -> dict[str, str]:
    """Fetch Andersen's Fairy Tales from Project Gutenberg and split into stories."""
    url = "https://www.gutenberg.org/cache/epub/1597/pg1597.txt"
    try:
        resp = requests.get(url, timeout=20)
        resp.encoding = "utf-8"
        raw = resp.text
    except Exception:
        return {}

    # Strip Gutenberg boilerplate
    start = re.search(r"\*{3} START OF .+? \*{3}", raw)
    end   = re.search(r"\*{3} END OF .+? \*{3}", raw)
    body  = raw[start.end() if start else 0 : end.start() if end else len(raw)]

    stories: dict[str, str] = {}
    positions: list[tuple[int, str]] = []

    for title in _TITLE_ORDER:
        pos = body.find(title)
        if pos == -1:
            # Try case-insensitive fallback
            m = re.search(re.escape(title), body, re.IGNORECASE)
            pos = m.start() if m else -1
        if pos != -1:
            positions.append((pos, title))

    positions.sort()

    for i, (pos, title) in enumerate(positions):
        content_start = pos + len(title)
        content_end   = positions[i + 1][0] if i + 1 < len(positions) else len(body)
        content       = body[content_start:content_end].strip()
        if len(content) > 300:
            stories[title] = content

    return stories


def get_chunks(text: str, chars: int = 2800) -> list[str]:
    """Split story text into paragraph-aligned chunks for TTS."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, current, length = [], [], 0
    for para in paragraphs:
        if length + len(para) > chars and current:
            chunks.append("\n\n".join(current))
            current, length = [para], len(para)
        else:
            current.append(para)
            length += len(para)
    if current:
        chunks.append("\n\n".join(current))
    return chunks
