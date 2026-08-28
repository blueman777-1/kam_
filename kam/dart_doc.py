"""DART 전자공시 뷰어에서 감사보고서 원문을 가져온다.

OpenDART API 는 첨부 감사보고서 본문을 제공하지 않으므로 뷰어 화면을 읽는다.
파싱 함수는 순수 함수로 두고 네트워크는 fetch_* 에만 둔다.
"""

import re
from typing import NamedTuple

from kam import http

BASE = "https://dart.fss.or.kr"
MAIN_URL = f"{BASE}/dsaf001/main.do"
VIEWER_URL = f"{BASE}/report/viewer.do"

_ATT_SELECT = re.compile(r'<select[^>]*id="att"[^>]*>(.*?)</select>', re.S | re.I)
_OPTION = re.compile(r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>', re.S | re.I)
_DCM_NO = re.compile(r"dcmNo=(\d+)")
_DATE_PREFIX = re.compile(r"^\s*\d{4}\.\d{2}\.\d{2}\s*")
_NODE_FIELD = re.compile(r"node\d+\['(\w+)'\]\s*=\s*\"?([^\";]*)\"?;")

VIEWER_FIELDS = ("rcpNo", "dcmNo", "eleId", "offset", "length", "dtd")


class Attachment(NamedTuple):
    dcm_no: str
    label: str


def _clean_label(raw: str) -> str:
    """'2026.03.17 연결감사보고서' -> '연결감사보고서'."""
    text = re.sub(r"<[^>]+>", "", raw)
    text = text.replace("&nbsp;", " ").replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return _DATE_PREFIX.sub("", text).replace(" ", "")


def parse_attachments(html: str) -> list[Attachment]:
    """공시 화면의 첨부문서 선택상자를 읽는다."""
    block = _ATT_SELECT.search(html)
    if not block:
        return []
    attachments = []
    for value, label in _OPTION.findall(block.group(1)):
        dcm = _DCM_NO.search(value.replace("&amp;", "&"))
        if dcm:
            attachments.append(Attachment(dcm.group(1), _clean_label(label)))
    return attachments


def pick_audit_report(attachments: list[Attachment]) -> tuple[str, str] | None:
    """연결감사보고서를 우선하고, 없으면 별도 감사보고서를 쓴다."""
    for label, kind in (("연결감사보고서", "연결"), ("감사보고서", "별도")):
        for attachment in attachments:
            if attachment.label == label:
                return attachment.dcm_no, kind
    return None


def parse_toc(html: str) -> list[dict]:
    """뷰어 화면의 목차 트리를 읽는다."""
    nodes, current = [], {}
    for key, value in _NODE_FIELD.findall(html):
        if key == "text" and current:
            nodes.append(current)
            current = {}
        current[key] = value
    if current:
        nodes.append(current)
    return nodes


def find_opinion_node(nodes: list[dict]) -> dict | None:
    """'독립된 감사인의 감사보고서' 목차 항목을 찾는다."""
    for node in nodes:
        if "독립된 감사인" in node.get("text", ""):
            return node
    return None


def fetch_attachments(rcept_no: str) -> list[Attachment]:
    response = http.get(MAIN_URL, {"rcpNo": rcept_no})
    response.raise_for_status()
    return parse_attachments(response.text)


def fetch_toc(rcept_no: str, dcm_no: str) -> list[dict]:
    response = http.get(MAIN_URL, {"rcpNo": rcept_no, "dcmNo": dcm_no})
    response.raise_for_status()
    return parse_toc(response.text)


def fetch_section(node: dict) -> str:
    params = {field: node.get(field, "") for field in VIEWER_FIELDS}
    response = http.get(VIEWER_URL, params)
    response.raise_for_status()
    return response.text


def document_url(rcept_no: str) -> str:
    """사용자에게 보여줄 DART 원문 링크."""
    return f"{MAIN_URL}?rcpNo={rcept_no}"
