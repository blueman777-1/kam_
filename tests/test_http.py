"""DART 요청 경로 테스트 — 중계 설정 여부에 따른 분기."""

import pytest

from kam import http


class FakeResponse:
    pass


@pytest.fixture
def calls(monkeypatch):
    recorded = []

    def fake_get(url, params=None, headers=None, timeout=None):
        recorded.append({"url": url, "params": params, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr(http.requests, "get", fake_get)
    return recorded


def test_중계가_없으면_DART로_직접_나간다(calls, monkeypatch):
    monkeypatch.setattr(http, "get_secret", lambda name: None)
    http.get("https://opendart.fss.or.kr/api/list.json", {"corp_code": "00126380"})
    assert calls[0]["url"] == "https://opendart.fss.or.kr/api/list.json"
    assert calls[0]["params"] == {"corp_code": "00126380"}


def test_중계가_있으면_중계를_거친다(calls, monkeypatch):
    monkeypatch.setattr(http, "get_secret", lambda name: "https://relay.vercel.app")
    http.get("https://opendart.fss.or.kr/api/list.json", {"corp_code": "00126380"})
    assert calls[0]["url"] == "https://relay.vercel.app/api/dart"
    assert calls[0]["params"] == {
        "url": "https://opendart.fss.or.kr/api/list.json?corp_code=00126380"
    }


def test_중계_주소_끝의_슬래시를_정리한다(calls, monkeypatch):
    monkeypatch.setattr(http, "get_secret", lambda name: "https://relay.vercel.app/")
    http.get("https://dart.fss.or.kr/dsaf001/main.do")
    assert calls[0]["url"] == "https://relay.vercel.app/api/dart"


def test_파라미터가_없으면_주소만_넘긴다(calls, monkeypatch):
    monkeypatch.setattr(http, "get_secret", lambda name: "https://relay.vercel.app")
    http.get("https://dart.fss.or.kr/dsaf001/main.do")
    assert calls[0]["params"] == {"url": "https://dart.fss.or.kr/dsaf001/main.do"}


def test_타임아웃이_전달된다(calls, monkeypatch):
    monkeypatch.setattr(http, "get_secret", lambda name: None)
    http.get("https://opendart.fss.or.kr/api/corpCode.xml", {"crtfc_key": "k"}, timeout=60)
    assert calls[0]["timeout"] == 60
