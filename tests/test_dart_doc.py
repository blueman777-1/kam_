"""DART 뷰어 HTML 파싱 테스트 — 저장된 실제 화면 기반."""

from pathlib import Path

from kam.dart_doc import (
    find_opinion_node,
    parse_attachments,
    parse_toc,
    pick_audit_report,
)

FIXTURES = Path(__file__).parent / "fixtures"


def read(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_첨부라벨의_날짜_접두사가_제거된다():
    labels = [a.label for a in parse_attachments(read("attlist_jejuair_amended.html"))]
    assert "연결감사보고서" in labels
    assert not any(label.startswith("2026") for label in labels)


def test_연결감사보고서를_우선_선택한다():
    attachments = parse_attachments(read("attlist_jejuair_amended.html"))
    dcm_no, kind = pick_audit_report(attachments)
    assert kind == "연결"
    assert dcm_no == "11142830"


def test_연결이_없으면_별도를_쓴다():
    from kam.dart_doc import Attachment

    dcm_no, kind = pick_audit_report([Attachment("1", "감사보고서"), Attachment("2", "정관")])
    assert (dcm_no, kind) == ("1", "별도")


def test_감사보고서가_없으면_None():
    from kam.dart_doc import Attachment

    assert pick_audit_report([Attachment("2", "정관")]) is None


def test_목차에서_감사의견_구간을_찾는다():
    node = find_opinion_node(parse_toc(read("toc_samsung.html")))
    assert node is not None
    assert node["eleId"] == "2"
    assert node["offset"] == "7769"
    assert node["length"] == "9032"
    assert node["dtd"] == "dart4.xsd"


def test_정정공시_rcpNo와_원공시_dcmNo_조합은_빈_목차를_준다():
    """제주항공 사례. 이 조합으로는 감사보고서를 읽을 수 없다."""
    nodes = parse_toc(read("toc_jejuair_mismatch.html"))
    assert nodes == []
    assert find_opinion_node(nodes) is None
