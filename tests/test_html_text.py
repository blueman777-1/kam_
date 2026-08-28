"""HTML → 블록 텍스트 변환 테스트.

핵심 요구사항: 인라인 태그로 쪼개진 문장이 한 줄로 복원되어야 한다.
카카오 감사보고서는 "우리의 의견형성 <span>시</span> 다루어졌으며" 처럼
문장 중간이 인라인 태그로 끊겨 있어, 단순 태그→개행 변환은 문장을 파괴한다.
"""
from pathlib import Path

from kam.html_text import to_block_text

FIXTURES = Path(__file__).parent / "fixtures"


def read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_인라인_태그로_쪼개진_문장이_한_줄로_복원된다():
    text = to_block_text(read("opinion_kakao.html"))
    assert "의견형성 시 다루어졌으며, 우리는 이런 사항에 대하여" in text


def test_블록_경계는_줄로_나뉜다():
    text = to_block_text(read("opinion_samsung.html"))
    lines = text.split("\n")
    assert "핵심감사사항" in lines
    assert "핵심감사사항으로 결정한 이유" in lines


def test_스크립트와_스타일은_제거된다():
    text = to_block_text("<div>보임</div><script>var x=1;</script><style>.a{color:red}</style>")
    assert text == "보임"


def test_엔티티가_풀린다():
    assert to_block_text("<p>&amp;&nbsp;끝</p>") == "& 끝"


def test_빈_줄은_남지_않는다():
    text = to_block_text(read("opinion_jejuair.html"))
    assert all(line.strip() for line in text.split("\n"))
