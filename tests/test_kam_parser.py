"""KAM 파서 테스트 — 전부 실제 DART 감사보고서 fixture 기반."""

from pathlib import Path

import pytest

from kam.kam_parser import parse_opinion
from kam.models import Status

FIXTURES = Path(__file__).parent / "fixtures"


def parse(name):
    return parse_opinion((FIXTURES / f"{name}.html").read_text(encoding="utf-8"))


def test_삼성전자는_KAM_2건을_추출한다():
    result = parse("opinion_samsung")
    assert result.status is Status.SUCCESS
    assert len(result.items) == 2
    assert result.items[0].title == "건설중인자산의 감가상각개시시점 평가"
    assert result.items[1].title == "재화의 판매장려활동에 대한 매출차감의 정확성과 완전성"


def test_삼성전자_항목의_이유와_대응이_모두_채워진다():
    for item in parse("opinion_samsung").items:
        assert item.reason.strip()
        assert item.response.strip()
        assert "결정한 이유" not in item.reason
        assert "다루어진 방법" not in item.response


def test_SK하이닉스는_번호가_붙은_소제목도_파싱한다():
    """소제목이 '1) 핵심감사사항으로 결정한 이유' 형태."""
    result = parse("opinion_skhynix")
    assert result.status is Status.SUCCESS
    assert len(result.items) == 1
    assert result.items[0].title == "기계장치의 감가상각개시시점에 대한 적정성 검토"
    assert "유형자산은" in result.items[0].reason
    assert "감가상각 개시시점" in result.items[0].response


def test_쌍용씨앤이는_KAM이_없는_것으로_구분된다():
    """파싱 실패가 아니라 '실제로 KAM이 없음'이어야 한다."""
    result = parse("opinion_ssangyong")
    assert result.status is Status.KAM_NOT_PRESENT
    assert result.items == []


def test_제주항공_원공시는_정상_파싱된다():
    result = parse("opinion_jejuair")
    assert result.status is Status.SUCCESS
    assert result.items[0].title == "이연법인세자산과 관련된 회계추정의 적정성"


def test_카카오는_파편화된_문장에도_정상_파싱된다():
    result = parse("opinion_kakao")
    assert result.status is Status.SUCCESS
    assert len(result.items) == 1
    assert "영업권" in result.items[0].title


@pytest.mark.parametrize(
    "name,expected",
    [
        ("opinion_samsung", "삼정회계법인"),
        ("opinion_skhynix", "삼정회계법인"),
        ("opinion_jejuair", "안진회계법인"),
        ("opinion_ssangyong", "안진회계법인"),
    ],
)
def test_감사인명을_추출한다(name, expected):
    assert parse(name).auditor == expected


def test_원문_텍스트가_보존된다():
    result = parse("opinion_samsung")
    assert "독립된 감사인의 감사보고서" in result.raw_text


def test_KAM_문구는_있으나_구조를_못_읽으면_수동확인이_필요하다():
    """헤딩 없이 소제목만 있는 문서 → 성공으로 위장하지 않는다."""
    html = "<p>핵심감사사항으로 결정한 이유</p><p>어떤 이유</p>"
    result = parse_opinion(html)
    assert result.status is Status.MANUAL_REVIEW_REQUIRED
