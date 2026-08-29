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
# 감사절차를 예고하는 문장. '감사절차'와 '다음'이 함께 오는 것이 공통점이다.
#   "핵심감사사항에 대응하기 위한 우리의 감사절차는 다음을 포함합니다."
#   "우리가 ...와 관련하여 수행한 주요 감사 절차는 다음과 같습니다."
_PROCEDURE = re.compile(r"감사\s?절차")
# 이유 문단은 문장으로 끝난다. "…있습니다(주석14)." 처럼 괄호로 끝나기도 한다.
_SENTENCE_END = (".", "다")
MAX_REASON_LINES = 6
_SECTION_END = ("경영진과 지배기구의 책임", "감사인의 책임")
_AUDITOR = re.compile(r"^([가-힣]{2,6}회계법인)")


def _nospace(line: str) -> str:
    return line.replace(" ", "")


# 소제목은 그 문구로 끝난다. 본문 문장 안에 같은 말이 나와도 걸리지 않게 한다.
# 앞에는 '1)', '가.' 같은 번호가, 뒤에는 '등'이 붙기도 한다.
_REASON = re.compile(r"핵심감사사항으로결정[한된]이유(등)?$")
_RESPONSE = re.compile(r"핵심감사사항이감사에서다루어진방법(등)?$")


def _is_reason(line: str) -> bool:
    return bool(_REASON.search(_nospace(line)))


def _is_response(line: str) -> bool:
    return bool(_RESPONSE.search(_nospace(line)))


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


def _is_procedure_lead(line: str) -> bool:
    """'…감사절차는 다음과 같습니다' 처럼 대응 절차를 예고하는 문장."""
    return bool(_PROCEDURE.search(line)) and "다음" in line and len(line) <= 160


def _extract_items_narrative(section: list[str]) -> list[KamItem]:
    """소제목 없이 제목·이유·절차예고문으로만 이어지는 문서를 읽는다.

    항목 경계는 절차예고문 뒤에서부터 다음 절차예고문 직전까지 거슬러 올라가며
    '문장으로 끝나는 줄'(이유 문단)의 연속 구간을 찾고, 그 앞줄을 제목으로 본다.
    이유 문단이 지나치게 길면 경계를 확신할 수 없으므로 제목을 비워 둔다.
    (그 경우 상위에서 manual_review_required 로 판정된다.)
    """
    leads = [i for i, line in enumerate(section) if _is_procedure_lead(line)]
    if not leads:
        return []

    # 구간 첫머리의 정형 문구("핵심감사사항은 우리의 전문가적 판단에 따라…")를 건너뛰고
    # 문장으로 끝나지 않는 첫 줄을 첫 항목의 제목으로 본다.
    first = 0
    while first < leads[0] and section[first].endswith(_SENTENCE_END):
        first += 1
    starts = [first if first < leads[0] else -1]

    for n in range(len(leads) - 1):
        cursor = leads[n + 1] - 1
        while cursor > leads[n] and section[cursor].endswith(_SENTENCE_END):
            cursor -= 1
        too_long = leads[n + 1] - cursor > MAX_REASON_LINES
        starts.append(-1 if too_long or cursor <= leads[n] else cursor)

    items = []
    for n, lead in enumerate(leads):
        start = starts[n]
        if start < 0:
            items.append(KamItem("", "", ""))
            continue
        end = starts[n + 1] if n + 1 < len(starts) and starts[n + 1] >= 0 else len(section)
        items.append(
            KamItem(
                title=section[start].strip(),
                reason="\n".join(section[start + 1 : lead]).strip(),
                response="\n".join(section[lead:end]).strip(),
            )
        )
    return items


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
    section = lines[start + 1 : end]
    items = _extract_items(section) or _extract_items_narrative(section)
    incomplete = any(not item.title or not item.reason or not item.response for item in items)
    status = Status.SUCCESS if items and not incomplete else Status.MANUAL_REVIEW_REQUIRED

    return ParsedOpinion(status=status, items=items, auditor=auditor, raw_text=text)
