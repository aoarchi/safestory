import hashlib
import streamlit as st
from openai import OpenAI


@st.cache_resource
def _client() -> OpenAI:
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def _key(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:14]


def translate(english_text: str) -> str:
    """Translate English fairy tale chunk to natural Korean using GPT-4o-mini."""
    ck = f"tr_{_key(english_text)}"
    if ck in st.session_state:
        return st.session_state[ck]

    resp = _client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 어린이 동화 번역 전문가입니다. "
                    "영어 동화를 4~8세 아이들이 이해하기 쉽고 아름다운 한국어로 번역해주세요. "
                    "동화 특유의 따뜻한 톤, 리듬감, 서정적인 표현을 살려주세요. "
                    "번역문만 출력하고 설명이나 주석은 넣지 마세요."
                ),
            },
            {"role": "user", "content": english_text},
        ],
        temperature=0.3,
    )
    result = resp.choices[0].message.content.strip()
    st.session_state[ck] = result
    return result


def speak(korean_text: str) -> bytes:
    """Convert Korean text to MP3 audio using OpenAI TTS (tts-1-hd, nova voice)."""
    ck = f"au_{_key(korean_text)}"
    if ck in st.session_state:
        return st.session_state[ck]

    # OpenAI TTS limit is 4096 chars
    text = korean_text[:4000]
    resp = _client().audio.speech.create(
        model="tts-1-hd",
        voice="nova",          # 따뜻하고 친근한 여성 목소리
        input=text,
        response_format="mp3",
    )
    audio = resp.content
    st.session_state[ck] = audio
    return audio
