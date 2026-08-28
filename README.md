# DART 핵심감사사항(KAM) 조회

기업명이나 종목코드를 입력하면 **최신 사업보고서에 첨부된 감사보고서**를 찾아
핵심감사사항(Key Audit Matters)을 구조화해 보여주고, Gemini로 쉬운 설명을 덧붙입니다.

DART에서 직접 확인하려면 `기업 검색 → 최신 사업보고서 → 첨부문서 → 연결/별도 감사보고서
→ 독립된 감사인의 감사보고서 → 핵심감사사항` 순서를 매번 거쳐야 합니다. 이 앱은 그 경로를
한 번에 통과합니다.

## 설계 원칙

**기업·공시·감사보고서를 고르는 일은 규칙 기반, AI는 설명에만.**
어느 공시를 골랐는지는 재현 가능하고 원문으로 추적할 수 있어야 하므로 AI에 맡기지 않습니다.
AI는 이미 확보한 원문을 읽기 쉽게 전달하는 역할만 합니다.

**"KAM이 없는 것"과 "찾지 못한 것"을 구분합니다.**

| 상태 | 의미 |
|---|---|
| `success` | 핵심감사사항을 정상적으로 추출 |
| `kam_not_present` | 감사보고서는 찾았으나 핵심감사사항이 기재되어 있지 않음 |
| `manual_review_required` | 원문은 찾았으나 구조를 완전히 해석하지 못함 (원문 직접 확인 필요) |
| `failed` | 기업·공시·감사보고서 조회 단계에서 실패 (실패한 단계를 표시) |

**정정공시는 원공시까지 따라갑니다.**
정정 사업보고서가 보여주는 첨부 `dcmNo`가 원공시에 속해 있어, 정정 접수번호로는
감사보고서를 열 수 없는 경우가 있습니다. 같은 사업연도의 공시를 접수일 역순으로
훑으며 첫 성공을 채택하는 방식으로 처리합니다.

**실패는 캐시하지 않습니다.**
일시적인 네트워크 오류가 캐시에 남으면 문제가 해결된 뒤에도 옛 실패가 계속 돌아옵니다.
`success`와 `kam_not_present`만 저장합니다.

## 설치와 실행

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# secrets.toml 에 키를 채운 뒤
.venv/bin/streamlit run app.py
```

`OPENDART_API_KEY`는 [OpenDART](https://opendart.fss.or.kr)에서 무료로 발급받습니다.
`GEMINI_API_KEY`는 선택이며, 없으면 AI 설명 없이 원문만 표시됩니다.

모델은 `kam/settings.py`의 `GEMINI_MODELS`를 앞에서부터 시도합니다.
모델이 폐기되거나(404) 일시적으로 과부하일 때(503) 다음 모델로 넘어갑니다.
둘 다 실제로 겪은 실패라 목록으로 두었습니다.

## 테스트

```bash
.venv/bin/python -m pytest tests/ -q
```

파서 테스트는 실제 DART 감사보고서 HTML을 `tests/fixtures/`에 저장해 두고 씁니다.
네트워크 없이 돌아가며, 삼성전자(KAM 2건)·SK하이닉스(번호 붙은 소제목)·카카오(문장 파편화)·
쌍용씨앤이(KAM 없음)·제주항공(정정공시)의 실제 사례를 회귀 테스트로 고정합니다.

## 추출 성공률 측정

```bash
OPENDART_API_KEY=... .venv/bin/python scripts/validate_batch.py 20
```

모든 상장기업에서 정확히 추출된다고 보장하지 않습니다. 이 스크립트가 실제 성공률을
숫자로 알려주고, 앱은 불완전한 파싱을 성공으로 위장하지 않습니다.

## 구조

```
app.py              Streamlit 화면
kam/
  style.py          화면 스타일 (파랑 계열 문서형 레이아웃)
  corp_index.py     corpCode.xml → 기업 검색 (종목코드 앞자리 0, 영문 포함 코드 대응)
  dart_api.py       OpenDART list.json + 오류코드 한국어 해석
  dart_doc.py       DART 뷰어 스크래핑 (첨부목록 / 목차 / 원문)
  html_text.py      HTML → 블록 텍스트 (인라인 태그로 쪼개진 문장 복원)
  kam_parser.py     텍스트 → 핵심감사사항 구조 + 상태 판정
  resolver.py       위 조각을 잇고 정정공시를 처리
  summarize.py      Gemini 설명 (실패해도 원문 표시는 유지)
  cache.py          성공 결과만 캐시
```
