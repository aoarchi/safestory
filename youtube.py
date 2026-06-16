import re
import requests


def extract_id(url: str) -> str | None:
    patterns = [
        r"youtube\.com/watch\?v=([^&\s#]+)",
        r"youtu\.be/([^?\s#]+)",
        r"youtube\.com/embed/([^?\s#]+)",
        r"youtube\.com/shorts/([^?\s#]+)",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def get_info(youtube_id: str) -> dict:
    thumbnail = f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg"
    try:
        resp = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": f"https://www.youtube.com/watch?v={youtube_id}", "format": "json"},
            timeout=6,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {"title": data.get("title", ""), "thumbnail": thumbnail}
    except Exception:
        pass
    return {"title": "", "thumbnail": thumbnail}


def embed_html(youtube_id: str, height: int = 480) -> str:
    src = (
        f"https://www.youtube.com/embed/{youtube_id}"
        "?rel=0&modestbranding=1&fs=0&iv_load_policy=3&disablekb=0"
    )
    return f"""
<div style="position:relative;width:100%;padding-bottom:{height}px;">
<iframe
    width="100%" height="{height}"
    src="{src}"
    frameborder="0"
    allow="accelerometer; autoplay; encrypted-media; gyroscope"
    style="border-radius:14px;display:block;">
</iframe>
</div>
"""
