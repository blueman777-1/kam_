"""KAM 원문을 초보자용 설명으로 바꾼다.

기업·공시·감사보고서를 고르는 일은 재현 가능해야 하므로 규칙 기반으로 두고,
AI 는 이미 확보한 원문을 '읽기 쉽게 전달'하는 데에만 쓴다.
키가 없거나 호출이 실패하면 요약만 조용히 빠지고 원문 표시는 그대로 남는다.
"""

import hashlib
import json
from dataclasses import dataclass

from kam.models import KamItem
from kam.settings import GEMINI_MODELS, redact

PROMPT = """당신은 회계감사를 처음 접하는 사람에게 설명하는 선생님입니다.
아래는 어느 상장기업 감사보고서의 핵심감사사항(KAM) 원문입니다.

원문에 없는 내용을 지어내지 마세요. 숫자를 바꾸지 마세요.
어려운 회계 용어가 나오면 괄호로 짧게 풀어 주세요.

각 항목마다 다음 세 가지를 한국어로 작성하세요.
- easy_title: 이 사안을 한 문장으로 (25자 이내)
- what: 무엇이 문제였는지, 왜 감사인이 중요하게 봤는지 (2~3문장)
- how: 감사인이 이를 확인하려고 무엇을 했는지 (2~3문장)

원문:
{body}
"""

SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "easy_title": {"type": "STRING"},
            "what": {"type": "STRING"},
            "how": {"type": "STRING"},
        },
        "required": ["easy_title", "what", "how"],
    },
}


@dataclass(frozen=True)
class Explanation:
    easy_title: str
    what: str
    how: str


class SummaryError(RuntimeError):
    """요약에 실패했지만 원문 표시는 계속되어야 하는 경우."""


def fingerprint(items: list[KamItem]) -> str:
    """원문이 바뀌면 요약 캐시도 새로 만들도록 하는 해시."""
    body = "␟".join(f"{i.title}{i.reason}{i.response}" for i in items)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def _as_prompt(items: list[KamItem]) -> str:
    blocks = []
    for n, item in enumerate(items, start=1):
        blocks.append(
            f"[{n}] 제목: {item.title}\n"
            f"핵심감사사항으로 결정한 이유:\n{item.reason}\n"
            f"감사에서 다루어진 방법:\n{item.response}"
        )
    return PROMPT.format(body="\n\n".join(blocks))


def _validate(payload, expected: int) -> list[Explanation]:
    if not isinstance(payload, list) or len(payload) != expected:
        raise SummaryError("AI 응답 형식이 예상과 다릅니다.")
    explanations = []
    for row in payload:
        if not isinstance(row, dict) or not all(k in row for k in ("easy_title", "what", "how")):
            raise SummaryError("AI 응답에 필요한 항목이 없습니다.")
        explanations.append(
            Explanation(str(row["easy_title"]), str(row["what"]), str(row["how"]))
        )
    return explanations


def _call(prompt: str, api_key: str, model: str) -> list:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SCHEMA,
        ),
    )
    return json.loads(response.text)


def explain(
    items: list[KamItem], api_key: str, models: tuple[str, ...] = GEMINI_MODELS
) -> list[Explanation]:
    """KAM 항목마다 쉬운 설명을 만든다. 실패하면 SummaryError.

    모델은 앞에서부터 시도한다. 모델이 폐기되거나(404) 일시적으로 과부하일 때(503)
    다음 모델로 넘어간다. 둘 다 실제로 겪은 실패다.
    """
    if not items:
        return []
    if not api_key:
        raise SummaryError("Gemini 키가 없어 AI 설명을 건너뜁니다.")

    prompt = _as_prompt(items)
    last_error = "호출을 시도하지 못했습니다."
    for model in models:
        try:
            return _validate(_call(prompt, api_key, model), len(items))
        except SummaryError as error:
            last_error = str(error)
        except Exception as exc:
            last_error = redact(f"{type(exc).__name__}: {exc}", api_key)

    raise SummaryError(f"AI 설명을 생성하지 못했습니다. ({last_error})")
