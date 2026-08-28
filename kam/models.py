"""앱 전체에서 주고받는 값 객체."""

from dataclasses import dataclass, field
from enum import Enum


class Status(str, Enum):
    """KAM 조회 결과 상태.

    'KAM이 없는 것'과 '우리가 찾지 못한 것'은 의미가 다르므로 분리한다.
    """

    SUCCESS = "success"
    KAM_NOT_PRESENT = "kam_not_present"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    FAILED = "failed"


@dataclass(frozen=True)
class CorpHit:
    """corpCode.xml 에서 찾은 기업 후보."""

    corp_code: str
    corp_name: str
    stock_code: str


@dataclass(frozen=True)
class Filing:
    """사업보고서 공시 한 건."""

    rcept_no: str
    corp_name: str
    report_nm: str
    rcept_dt: str
    period: str
    is_amended: bool


@dataclass(frozen=True)
class KamItem:
    """핵심감사사항 한 건."""

    title: str
    reason: str
    response: str


@dataclass
class ParsedOpinion:
    """감사보고서 '독립된 감사인의 감사보고서' 구간 파싱 결과."""

    status: Status
    items: list[KamItem] = field(default_factory=list)
    auditor: str | None = None
    raw_text: str = ""


@dataclass
class KamResult:
    """화면에 표시할 최종 결과."""

    status: Status
    corp_name: str = ""
    stock_code: str = ""
    items: list[KamItem] = field(default_factory=list)
    auditor: str | None = None
    report_kind: str | None = None
    filing: Filing | None = None
    dart_url: str | None = None
    raw_text: str = ""
    failed_stage: str | None = None
    message: str | None = None
