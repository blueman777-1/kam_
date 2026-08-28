"""인증키를 한 곳에서 읽는다.

로컬 스크립트(환경변수)와 Streamlit(secrets) 양쪽에서 같은 이름을 쓴다.
"""

import os

OPENDART_KEY = "OPENDART_API_KEY"
GEMINI_KEY = "GEMINI_API_KEY"
GEMINI_MODEL_KEY = "GEMINI_MODEL"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def get_secret(name: str) -> str | None:
    """환경변수를 먼저 보고, 없으면 Streamlit secrets 를 본다."""
    value = os.environ.get(name)
    if value:
        return value.strip()

    try:
        import streamlit as st

        value = st.secrets.get(name)
    except Exception:
        return None
    return value.strip() if value else None


def redact(text: str, *secrets: str | None) -> str:
    """오류 메시지에 인증키가 섞여 나가지 않도록 지운다."""
    for secret in secrets:
        if secret and len(secret) >= 8:
            text = text.replace(secret, "***")
    return text
