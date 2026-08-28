"""OpenDART REST API 호출.

DART가 돌려주는 상태코드를 그대로 노출하면 사용자가 다음 행동을 정할 수 없으므로
한국어 설명으로 바꿔서 올린다. 인증키는 어떤 예외 메시지에도 실리지 않는다.
"""

import re
from datetime import date, timedelta

import requests

from kam.models import Filing

LIST_URL = "https://opendart.fss.or.kr/api/list.json"

STATUS_MESSAGES = {
    "010": "등록되지 않은 인증키입니다. OpenDART에서 발급받은 키인지 확인하세요.",
    "011": "사용할 수 없는 인증키입니다. OpenDART에서 키 상태를 확인하세요.",
    "012": "접근할 수 없는 IP입니다.",
    "013": "조회된 공시가 없습니다.",
    "014": "파일이 존재하지 않습니다.",
    "020": "OpenDART 일일 요청 한도(20,000건)를 초과했습니다. 내일 다시 시도하세요.",
    "021": "조회 가능한 회사 수를 초과했습니다.",
    "100": "요청 값이 올바르지 않습니다.",
    "101": "부적절한 접근입니다.",
    "800": "OpenDART가 시스템 점검 중입니다. 잠시 후 다시 시도하세요.",
    "900": "OpenDART에서 정의되지 않은 오류가 발생했습니다.",
    "901": "사용자 계정의 개인정보보호 정책 위반입니다.",
}

_PERIOD = re.compile(r"\((\d{4})\.(\d{2})\)")
_AMENDED = re.compile(r"^\[[^\]]*정정[^\]]*\]")


class DartApiError(RuntimeError):
    """OpenDART가 정상(000) 외의 상태를 돌려준 경우."""

    def __init__(self, status: str, message: str | None = None):
        self.status = status
        self.message = message or STATUS_MESSAGES.get(
            status, f"OpenDART 요청에 실패했습니다. 오류 코드: {status}"
        )
        super().__init__(self.message)


def describe_status(status: str) -> str:
    """상태코드를 사람이 읽는 문장으로."""
    return STATUS_MESSAGES.get(status, f"OpenDART 요청에 실패했습니다. 오류 코드: {status}")


def to_filing(row: dict) -> Filing:
    """list.json 한 행을 Filing 으로."""
    report_nm = (row.get("report_nm") or "").strip()
    match = _PERIOD.search(report_nm)
    return Filing(
        rcept_no=(row.get("rcept_no") or "").strip(),
        corp_name=(row.get("corp_name") or "").strip(),
        report_nm=report_nm,
        rcept_dt=(row.get("rcept_dt") or "").strip(),
        period=f"{match.group(1)}.{match.group(2)}" if match else "",
        is_amended=bool(_AMENDED.match(report_nm)),
    )


def list_annual_reports(api_key: str, corp_code: str, years: int = 3) -> list[Filing]:
    """최근 N년치 사업보고서를 접수일 내림차순으로 돌려준다.

    정정공시와 원공시를 모두 포함한다. 정정공시의 첨부가 원공시에 매달려 있는
    경우가 있어, 위에서부터 차례로 시도하려면 둘 다 필요하다.
    """
    today = date.today()
    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bgn_de": (today - timedelta(days=365 * years)).strftime("%Y%m%d"),
        "end_de": today.strftime("%Y%m%d"),
        "pblntf_detail_ty": "A001",
        "page_count": "100",
    }
    try:
        response = requests.get(LIST_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise DartApiError("900", f"OpenDART 연결에 실패했습니다: {type(exc).__name__}") from None

    status = str(payload.get("status", "")).strip()
    if status != "000":
        raise DartApiError(status, payload.get("message"))

    filings = [to_filing(row) for row in payload.get("list", [])]
    return sorted(filings, key=lambda f: f.rcept_dt, reverse=True)
