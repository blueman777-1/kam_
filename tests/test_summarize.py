"""AI 설명 계층 테스트 — 네트워크 없이 대역으로 확인."""

import pytest

from kam import summarize
from kam.models import KamItem

ITEMS = [KamItem("제목", "이유", "대응")]
GOOD = [{"easy_title": "쉬운 제목", "what": "무엇", "how": "어떻게"}]


def test_키가_없으면_건너뛴다():
    with pytest.raises(summarize.SummaryError, match="키가 없어"):
        summarize.explain(ITEMS, "")


def test_항목이_없으면_빈_목록():
    assert summarize.explain([], "key") == []


def test_앞_모델이_실패하면_다음_모델로_넘어간다(monkeypatch):
    tried = []

    def fake(prompt, api_key, model):
        tried.append(model)
        if model == "first":
            raise RuntimeError("503 UNAVAILABLE")
        return GOOD

    monkeypatch.setattr(summarize, "_call", fake)
    result = summarize.explain(ITEMS, "key", ("first", "second"))
    assert tried == ["first", "second"]
    assert result[0].easy_title == "쉬운 제목"


def test_모든_모델이_실패하면_SummaryError(monkeypatch):
    monkeypatch.setattr(summarize, "_call", lambda *a: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(summarize.SummaryError, match="생성하지 못했습니다"):
        summarize.explain(ITEMS, "key", ("a", "b"))


def test_인증키는_오류_메시지에_나오지_않는다(monkeypatch):
    secret = "AIzaSECRETKEY1234567890"

    def leaky(prompt, api_key, model):
        raise RuntimeError(f"bad key {secret}")

    monkeypatch.setattr(summarize, "_call", leaky)
    with pytest.raises(summarize.SummaryError) as caught:
        summarize.explain(ITEMS, secret, ("a",))
    assert secret not in str(caught.value)
    assert "***" in str(caught.value)


def test_항목_수가_다르면_거부한다(monkeypatch):
    monkeypatch.setattr(summarize, "_call", lambda *a: GOOD + GOOD)
    with pytest.raises(summarize.SummaryError):
        summarize.explain(ITEMS, "key", ("a",))


def test_원문이_바뀌면_지문도_바뀐다():
    a = summarize.fingerprint([KamItem("제목", "이유", "대응")])
    b = summarize.fingerprint([KamItem("제목", "이유가 수정됨", "대응")])
    assert a != b
