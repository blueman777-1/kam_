"""공시 후보 선택 규칙 테스트."""

from kam.models import Filing
from kam.resolver import latest_candidates


def filing(rcept_no, period, rcept_dt, amended=False):
    name = f"{'[첨부정정]' if amended else ''}사업보고서 ({period})"
    return Filing(rcept_no, "제주항공", name, rcept_dt, period, amended)


def test_가장_최근_사업연도만_남긴다():
    filings = [
        filing("20250318001006", "2024.12", "20250318"),
        filing("20260318001439", "2025.12", "20260318"),
    ]
    assert [f.period for f in latest_candidates(filings)] == ["2025.12"]


def test_같은_사업연도면_정정본을_먼저_시도한다():
    """정정본이 먼저, 실패하면 원공시로 내려간다."""
    original = filing("20260318001439", "2025.12", "20260318")
    amended = filing("20260515002339", "2025.12", "20260515", amended=True)
    order = [f.rcept_no for f in latest_candidates([original, amended])]
    assert order == ["20260515002339", "20260318001439"]


def test_보고기간을_못_읽어도_접수일순으로_돌려준다():
    filings = [Filing("1", "X", "사업보고서", "20240101", "", False),
               Filing("2", "X", "사업보고서", "20260101", "", False)]
    assert [f.rcept_no for f in latest_candidates(filings)] == ["2", "1"]


def test_빈_목록():
    assert latest_candidates([]) == []
