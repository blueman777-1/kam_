"""OpenDART corpCode.xml 로 기업명·종목코드를 DART 고유번호로 바꾼다.

종목코드는 '005930' 처럼 앞자리 0이 의미를 가지며 '0126Z0' 처럼 영문자가
섞이기도 하므로 끝까지 문자열로 다룬다.
"""

import io
import re
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import requests

from kam.dart_api import DartApiError
from kam.models import CorpHit

CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
CACHE_PATH = Path(".cache/corpcode.xml")
CACHE_TTL_SECONDS = 60 * 60 * 24 * 7
_STOCK_CODE = re.compile(r"^[0-9A-Za-z]{6}$")


def raise_if_error_xml(payload: bytes) -> None:
    """정상 응답은 zip 이다. 오류일 때만 상태코드 XML 이 온다."""
    if payload[:5] != b"<?xml":
        return
    try:
        root = ET.fromstring(payload.decode("utf-8", "replace"))
    except ET.ParseError:
        raise DartApiError("900", "OpenDART 응답을 해석하지 못했습니다.") from None
    status = (root.findtext("status") or "900").strip()
    if status != "000":
        raise DartApiError(status, (root.findtext("message") or "").strip() or None)


def parse_corp_xml(source: str) -> list[CorpHit]:
    """corpCode.xml 본문에서 상장기업만 뽑는다."""
    root = ET.fromstring(source)
    hits = []
    for node in root.iter("list"):
        stock_code = (node.findtext("stock_code") or "").strip()
        if not stock_code:
            continue
        hits.append(
            CorpHit(
                corp_code=(node.findtext("corp_code") or "").strip(),
                corp_name=(node.findtext("corp_name") or "").strip(),
                stock_code=stock_code,
            )
        )
    return hits


def search(index: list[CorpHit], query: str, limit: int = 30) -> list[CorpHit]:
    """종목코드면 정확 일치, 아니면 기업명 부분 일치로 후보를 돌려준다."""
    query = query.strip()
    if not query:
        return []

    if _STOCK_CODE.match(query):
        exact = [hit for hit in index if hit.stock_code.upper() == query.upper()]
        if exact:
            return exact

    lowered = query.lower()
    matched = [hit for hit in index if lowered in hit.corp_name.lower()]

    def rank(hit: CorpHit) -> tuple[int, int, str]:
        name = hit.corp_name.lower()
        if name == lowered:
            order = 0
        elif name.startswith(lowered):
            order = 1
        else:
            order = 2
        return order, len(hit.corp_name), hit.corp_name

    return sorted(matched, key=rank)[:limit]


def load_index(api_key: str, refresh: bool = False) -> list[CorpHit]:
    """corpCode.xml 을 받아 파싱한다. 일주일간 로컬에 캐시한다."""
    if not refresh and CACHE_PATH.exists():
        age = time.time() - CACHE_PATH.stat().st_mtime
        if age < CACHE_TTL_SECONDS:
            return parse_corp_xml(CACHE_PATH.read_text(encoding="utf-8"))

    response = requests.get(CORP_CODE_URL, params={"crtfc_key": api_key}, timeout=60)
    response.raise_for_status()
    raise_if_error_xml(response.content)

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        name = next(n for n in archive.namelist() if n.lower().endswith(".xml"))
        xml_text = archive.read(name).decode("utf-8")

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(xml_text, encoding="utf-8")
    return parse_corp_xml(xml_text)
