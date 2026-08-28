"""OpenDART 응답 해석 테스트 (네트워크 없음)."""

import pytest

from kam.dart_api import DartApiError, describe_status, to_filing


def test_알려진_오류코드는_한국어로_설명된다():
    assert "점검" in describe_status("800")
    assert "한도" in describe_status("020")
    assert "조회된 공시가 없습니다." == describe_status("013")


def test_모르는_코드는_코드번호를_보여준다():
    assert "777" in describe_status("777")


def test_예외는_한국어_메시지를_갖는다():
    with pytest.raises(DartApiError) as caught:
        raise DartApiError("800")
    assert "점검" in str(caught.value)


def test_보고기간을_보고서명에서_뽑는다():
    filing = to_filing({"report_nm": "사업보고서 (2025.12)", "rcept_no": "20260318001423"})
    assert filing.period == "2025.12"
    assert filing.is_amended is False


@pytest.mark.parametrize("name", ["[기재정정]사업보고서 (2024.12)", "[첨부정정]사업보고서 (2025.12)"])
def test_정정공시를_표시한다(name):
    assert to_filing({"report_nm": name}).is_amended is True
