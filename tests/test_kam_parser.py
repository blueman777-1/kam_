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


# ── 소제목 없는 서술형 ────────────────────────────────────────────────
# 다수 감사보고서는 '핵심감사사항으로 결정한 이유' 같은 소제목을 쓰지 않고,
# 제목 → 이유 문단 → '…감사절차는 다음과 같습니다' → 절차 목록 으로 이어진다.


def test_에코프로비엠_소제목_없는_문서도_파싱한다():
    result = parse("opinion_ecopro")
    assert result.status is Status.SUCCESS
    assert len(result.items) == 1
    assert result.items[0].title == "제품매출 기간귀속의 적정성"
    assert "2,447,031백만원" in result.items[0].reason
    assert "감사절차" in result.items[0].response


def test_현대자동차_가나다_번호_제목을_여러건_파싱한다():
    result = parse("opinion_hyundai")
    assert result.status is Status.SUCCESS
    assert len(result.items) >= 2
    assert result.items[0].title == "가. 판매보증충당부채의 평가"
    assert result.items[1].title == "나. 금융업채권의 평가"
    assert "판매보증충당부채를 측정" in result.items[0].response


def test_아모레퍼시픽_괄호번호_제목을_파싱한다():
    result = parse("opinion_amore")
    assert result.status is Status.SUCCESS
    assert result.items[0].title.startswith("(1)")
    assert "수익인식" in result.items[0].title


def test_이유와_대응이_서로_섞이지_않는다():
    """대응 절차 문장이 이유에 남아 있으면 안 된다."""
    for name in ("opinion_ecopro", "opinion_hyundai", "opinion_amore"):
        for item in parse(name).items:
            assert item.reason.strip()
            assert item.response.strip()
            assert "다음과 같습니다" not in item.reason.split("\n")[-1]


def test_피동형_소제목도_인식한다():
    """'결정한 이유'(능동)와 '결정된 이유'(피동)를 모두 쓰는 보고서가 있다."""
    from kam.kam_parser import _is_reason

    assert _is_reason("핵심감사사항으로 결정한 이유")
    assert _is_reason("핵심감사사항으로 결정된 이유")
    assert _is_reason("가. 핵심감사사항으로 결정된 이유 등")
    assert _is_reason("1) 핵심감사사항으로 결정한 이유")
    assert not _is_reason("우리는 이를 핵심감사사항으로 결정한 이유를 아래와 같이 설명합니다.")
