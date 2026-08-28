"""DART 감사보고서 HTML을 줄 단위 텍스트로 변환한다.

DART 문서는 문장 중간에도 <span>, <font> 같은 인라인 태그가 끼어든다.
모든 태그를 개행으로 바꾸면 문장이 조각나 파싱이 불가능해지므로,
블록 태그만 개행으로 바꾸고 인라인 태그는 흔적 없이 지운다.
"""

import html
import re

_DROP = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
_BLOCK = re.compile(
    r"</?(?:p|div|tr|td|th|li|ul|ol|table|thead|tbody|h[1-6]|br|hr|caption)\b[^>]*>",
    re.I,
)
_TAG = re.compile(r"<[^>]+>")


def to_block_text(source: str) -> str:
    """HTML을 블록 단위로 줄바꿈한 평문으로 만든다."""
    text = _DROP.sub("", source)
    text = _BLOCK.sub("\n", text)
    text = _TAG.sub("", text)
    text = html.unescape(text)
    text = text.replace("\xa0", " ")

    lines = []
    for line in text.split("\n"):
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)
