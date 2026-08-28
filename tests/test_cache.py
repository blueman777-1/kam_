"""캐시 정책 테스트 — 실패는 절대 남지 않아야 한다."""

import pytest

from kam import cache
from kam.models import Filing, KamItem, KamResult, Status


@pytest.fixture(autouse=True)
def temp_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path / "kam")


def result(status):
    return KamResult(
        status=status,
        corp_name="삼성전자",
        stock_code="005930",
        items=[KamItem("제목", "이유", "대응")],
        auditor="삼정회계법인",
        report_kind="연결",
        filing=Filing("20260310002820", "삼성전자", "사업보고서 (2025.12)", "20260310", "2025.12", False),
        dart_url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260310002820",
        raw_text="원문",
    )


def test_성공은_저장되고_그대로_복원된다():
    assert cache.save("k", result(Status.SUCCESS)) is True
    restored = cache.load("k")
    assert restored.status is Status.SUCCESS
    assert restored.items[0].title == "제목"
    assert restored.filing.period == "2025.12"
    assert restored.auditor == "삼정회계법인"


def test_KAM_없음도_저장된다():
    assert cache.save("k", result(Status.KAM_NOT_PRESENT)) is True
    assert cache.load("k").status is Status.KAM_NOT_PRESENT


def test_실패는_저장되지_않는다():
    assert cache.save("k", result(Status.FAILED)) is False
    assert cache.load("k") is None


def test_수동확인필요도_저장되지_않는다():
    assert cache.save("k", result(Status.MANUAL_REVIEW_REQUIRED)) is False
    assert cache.load("k") is None


def test_없는_키는_None():
    assert cache.load("존재하지않음") is None


def test_깨진_캐시는_None을_돌려준다(tmp_path):
    cache.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (cache.CACHE_DIR / "broken.json").write_text("{not json", encoding="utf-8")
    assert cache.load("broken") is None
