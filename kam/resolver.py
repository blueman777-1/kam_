"""기업 하나에 대해 '최신 사업보고서의 KAM'을 확정한다.

정정공시는 첨부 감사보고서가 원공시에 매달려 있는 경우가 있다.
(제주항공 2025.12: 정정 20260515002339 이 보여주는 dcmNo 11142830 은
 원공시 20260318001439 소속이라, 정정 접수번호로는 목차가 비어 있다.)

그래서 '원공시 접수번호를 어디선가 알아낸다' 대신
같은 사업연도의 공시를 접수일 역순으로 훑으며 첫 성공을 채택한다.
이 한 루프가 정정 불일치·첨부 누락·목차 없음을 모두 흡수한다.
"""

import requests

from kam import cache, dart_api, dart_doc, kam_parser
from kam.models import CorpHit, Filing, KamResult, Status


def _failed(stage: str, message: str, hit: CorpHit) -> KamResult:
    return KamResult(
        status=Status.FAILED,
        corp_name=hit.corp_name,
        stock_code=hit.stock_code,
        failed_stage=stage,
        message=message,
    )


def latest_candidates(filings: list[Filing]) -> list[Filing]:
    """가장 최근 사업연도의 공시만, 접수일 내림차순(정정본 우선)으로."""
    dated = [f for f in filings if f.period]
    if not dated:
        return sorted(filings, key=lambda f: f.rcept_dt, reverse=True)
    newest = max(f.period for f in dated)
    return sorted(
        [f for f in dated if f.period == newest], key=lambda f: f.rcept_dt, reverse=True
    )


def _try_filing(filing: Filing, hit: CorpHit) -> KamResult | None:
    """공시 한 건에서 감사보고서를 읽어본다. 못 읽으면 None."""
    attachments = dart_doc.fetch_attachments(filing.rcept_no)
    picked = dart_doc.pick_audit_report(attachments)
    if not picked:
        return None
    dcm_no, report_kind = picked

    node = dart_doc.find_opinion_node(dart_doc.fetch_toc(filing.rcept_no, dcm_no))
    if node is None:
        return None

    parsed = kam_parser.parse_opinion(dart_doc.fetch_section(node))
    return KamResult(
        status=parsed.status,
        corp_name=hit.corp_name,
        stock_code=hit.stock_code,
        items=parsed.items,
        auditor=parsed.auditor,
        report_kind=report_kind,
        filing=filing,
        dart_url=dart_doc.document_url(filing.rcept_no),
        raw_text=parsed.raw_text,
    )


def resolve_latest_kam(api_key: str, hit: CorpHit, refresh: bool = False) -> KamResult:
    """기업 후보 하나에 대한 최신 KAM 조회 결과."""
    try:
        filings = dart_api.list_annual_reports(api_key, hit.corp_code)
    except dart_api.DartApiError as error:
        return _failed("공시목록", error.message, hit)

    candidates = latest_candidates(filings)
    if not candidates:
        return _failed("공시목록", "최근 3년간 사업보고서를 찾지 못했습니다.", hit)

    key = f"{hit.corp_code}_{candidates[0].rcept_no}"
    if not refresh:
        cached = cache.load(key)
        if cached is not None:
            return cached

    for filing in candidates:
        try:
            result = _try_filing(filing, hit)
        except requests.RequestException as exc:
            return _failed("감사보고서", f"DART 연결에 실패했습니다: {type(exc).__name__}", hit)
        if result is not None:
            cache.save(key, result)
            return result

    return _failed(
        "감사보고서",
        f"{candidates[0].period} 사업보고서에서 감사보고서를 찾지 못했습니다.",
        hit,
    )
