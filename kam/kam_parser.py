"""감사보고서 '독립된 감사인의 감사보고서' 구간에서 핵심감사사항을 뽑아낸다.

DART 감사보고서의 KAM 구간은 아래 형태로 반복된다.

    핵심감사사항                          <- 구간 시작 (단독 헤딩)
    핵심감사사항은 우리의 전문가적 ...    <- 정형 문구
    <항목 제목>
    핵심감사사항으로 결정한 이유          <- 번호가 붙기도 한다 ('1) ...')
    ...
    핵심감사사항이 감사에서 다루어진 방법
    ...
    연결재무제표에 대한 경영진과 ... 책임 <- 구간 끝

표 형식으로 작성된 보고서도 html_text 를 거치면 같은 줄 구조가 되므로
별도 분기 없이 한 경로로 처리한다.
"""

import re

from kam.html_text import to_block_text
from kam.models import KamItem, ParsedOpinion, Status

_HEADING = re.compile(r"^핵심감사사항(\(.*\))?$")
_SECTION_END = ("경영진과 지배기구의 책임", "감사인의 책임")
_AUDITOR = re.compile(r"^([가-힣]{2,6}회계법인)")


def _nospace(line: str) -> str:
    return line.replace(" ", "")


def _is_reason(line: str) -> bool:
    packed = _nospace(line)
    return "결정한이유" in packed and len(packed) <= 30


def _is_response(line: str) -> bool:
    packed = _nospace(line)
    return "다루어진방법" in packed and len(packed) <= 35


def _find_auditor(lines: list[str]) -> str | None:
    """서명부는 문서 끝에 있으므로 뒤에서부터 찾는다."""
    for line in reversed(lines):
        match = _AUDITOR.match(_nospace(line))
        if match:
            return match.group(1)
    return None


def _section_bounds(lines: list[str]) -> tuple[int, int] | None:
    start = next((i for i, line in enumerate(lines) if _HEADING.match(_nospace(line))), None)
    if start is None:
        return None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if any(marker in lines[i] for marker in _SECTION_END):
            end = i
            break
    return start, end


def _extract_items(section: list[str]) -> list[KamItem]:
    anchors = [i for i, line in enumerate(section) if _is_reason(line)]
    items = []
    for n, reason_at in enumerate(anchors):
        title = section[reason_at - 1].strip() if reason_at > 0 else ""
        if _is_reason(title) or _HEADING.match(_nospace(title)):
            title = ""

        stop = (anchors[n + 1] - 1) if n + 1 < len(anchors) else len(section)
        body = section[reason_at + 1 : stop]

        response_at = next((i for i, line in enumerate(body) if _is_response(line)), None)
        if response_at is None:
            reason, response = body, []
        else:
            reason, response = body[:response_at], body[response_at + 1 :]

        items.append(
            KamItem(
                title=title,
                reason="\n".join(reason).strip(),
                response="\n".join(response).strip(),
            )
        )
    return items


def parse_opinion(source: str) -> ParsedOpinion:
    """감사의견 구간 HTML을 파싱해 상태와 항목을 돌려준다."""
    text = to_block_text(source)
    lines = text.split("\n")
    auditor = _find_auditor(lines)

    bounds = _section_bounds(lines)
    if bounds is None:
        # 헤딩이 없어도 소제목이 보이면 KAM이 없는 게 아니라 우리가 못 읽은 것이다.
        status = (
            Status.MANUAL_REVIEW_REQUIRED
            if any(_is_reason(line) or _is_response(line) for line in lines)
            else Status.KAM_NOT_PRESENT
        )
        return ParsedOpinion(status=status, auditor=auditor, raw_text=text)

    start, end = bounds
    items = _extract_items(lines[start + 1 : end])
    incomplete = any(not item.title or not item.reason or not item.response for item in items)
    status = Status.SUCCESS if items and not incomplete else Status.MANUAL_REVIEW_REQUIRED

    return ParsedOpinion(status=status, items=items, auditor=auditor, raw_text=text)
