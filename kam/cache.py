"""조회 결과를 로컬 JSON 으로 캐시한다.

실패를 캐시하면 원인이 해결된 뒤에도 옛 실패가 계속 돌아온다.
그래서 '성공'과 'KAM 없음'만 저장하고 나머지는 저장하지 않는다.
"""

import json
from pathlib import Path

from kam.models import Filing, KamItem, KamResult, Status

CACHE_DIR = Path(".cache/kam")
CACHEABLE = (Status.SUCCESS, Status.KAM_NOT_PRESENT)


def _path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def to_dict(result: KamResult) -> dict:
    return {
        "status": result.status.value,
        "corp_name": result.corp_name,
        "stock_code": result.stock_code,
        "items": [{"title": i.title, "reason": i.reason, "response": i.response} for i in result.items],
        "auditor": result.auditor,
        "report_kind": result.report_kind,
        "filing": vars(result.filing) if result.filing else None,
        "dart_url": result.dart_url,
        "raw_text": result.raw_text,
    }


def from_dict(payload: dict) -> KamResult:
    filing = payload.get("filing")
    return KamResult(
        status=Status(payload["status"]),
        corp_name=payload.get("corp_name", ""),
        stock_code=payload.get("stock_code", ""),
        items=[KamItem(**item) for item in payload.get("items", [])],
        auditor=payload.get("auditor"),
        report_kind=payload.get("report_kind"),
        filing=Filing(**filing) if filing else None,
        dart_url=payload.get("dart_url"),
        raw_text=payload.get("raw_text", ""),
    )


def load(key: str) -> KamResult | None:
    path = _path(key)
    if not path.exists():
        return None
    try:
        return from_dict(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def save(key: str, result: KamResult) -> bool:
    """캐시 가능한 상태만 저장한다. 저장했으면 True."""
    if result.status not in CACHEABLE:
        return False
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _path(key).write_text(
        json.dumps(to_dict(result), ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return True
