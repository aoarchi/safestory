import re
import requests
import streamlit as st
from bs4 import BeautifulSoup

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


ENGLISH_TALES_META = {
    "The Story of the Three Bears":            ("세 마리 곰",               "🐻", "5세 이상"),
    "Lazy Jack":                                ("게으른 잭",               "😴", "5세 이상"),
    "Titty Mouse and Tatty Mouse":              ("티티 마우스와 태티 마우스", "🐭", "5세 이상"),
    "The Three Little Pigs":                    ("세 마리 아기 돼지",        "🐷", "5세 이상"),
    "Henny-Penny":                              ("헤니 페니",                "🐔", "5세 이상"),
    "The Old Woman and Her Pig":                ("할머니와 돼지",            "🐷", "5세 이상"),
    "Little Red Riding-Hood":                   ("빨간 모자",                "🐺", "5세 이상"),
    "Master of All Masters":                    ("만능 주인",                "😄", "5세 이상"),
    "Tom-Tit-Tot":                              ("톰팃톳",                   "🧵", "7세 이상"),
    "Tattercoats":                              ("누더기 외투",              "✨", "7세 이상"),
    "The Three Sillies":                        ("세 바보",                  "😄", "7세 이상"),
    "Jack and the Beanstalk":                   ("잭과 콩나무",              "🌱", "7세 이상"),
    "Dick Whittington and His Cat":             ("딕 위팅턴과 고양이",       "🐱", "7세 이상"),
    "The Bogey-Beast":                          ("보기 비스트",              "😄", "7세 이상"),
    "The Babes in the Wood":                    ("숲속의 아이들",            "🌲", "7세 이상"),
    "Molly Whuppie and the Double-Faced Giant": ("몰리 위피와 거인",         "💪", "7세 이상"),
}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_english_fairy_tales() -> dict[str, str]:
    """Fetch English Fairy Tales (Flora Annie Steel) from Project Gutenberg and split into stories."""
    url = "https://www.gutenberg.org/files/17034/17034-h/17034-h.htm"
    try:
        resp = requests.get(url, timeout=30)
        resp.encoding = "utf-8"
    except Exception:
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")
    stories: dict[str, str] = {}

    for h2 in soup.find_all("h2"):
        raw = h2.get_text(strip=True)
        key = next((k for k in ENGLISH_TALES_META if k.lower() == raw.lower()), None)
        if not key:
            continue

        parts = []
        for sib in h2.next_siblings:
            if getattr(sib, "name", None) == "h2":
                break
            if getattr(sib, "name", None) in ("p", "blockquote", "div", "h3", "h4"):
                text = sib.get_text(" ", strip=True)
                if text:
                    parts.append(text)

        content = "\n\n".join(parts)
        if len(content) > 100:
            stories[key] = content

    return stories


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_book_text(gutenberg_id: int) -> str:
    """Fetch any Gutenberg book's plain text by ID, stripped of boilerplate."""
    url = f"https://www.gutenberg.org/cache/epub/{gutenberg_id}/pg{gutenberg_id}.txt"
    try:
        resp = requests.get(url, timeout=30)
        resp.encoding = "utf-8"
        raw = resp.text
    except Exception:
        return ""

    start = re.search(r"\*{3} START OF .+? \*{3}", raw)
    end   = re.search(r"\*{3} END OF .+? \*{3}", raw)
    body  = raw[start.end() if start else 0 : end.start() if end else len(raw)]
    return body.strip()


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
