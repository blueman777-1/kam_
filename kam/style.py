"""화면 스타일. 파랑 계열의 차분한 문서형 레이아웃."""

CSS = """
<style>
:root {
  --blue-700:#1D4ED8; --blue-600:#2563EB; --blue-500:#3B82F6;
  --blue-50:#EFF6FF;  --blue-100:#DBEAFE;
  --ink:#0F172A; --muted:#64748B; --line:#E2E8F0; --paper:#F8FAFC;
}
.block-container { max-width: 920px; padding-top: 3.2rem; }

/* 헤더 */
.kam-hero { border-left:3px solid var(--blue-600); padding:.1rem 0 .1rem 1rem; margin-bottom:1.6rem; }
.kam-eyebrow { font-size:.72rem; font-weight:700; letter-spacing:.16em;
  text-transform:uppercase; color:var(--blue-600); margin-bottom:.35rem; }
.kam-title { font-size:1.85rem; font-weight:700; color:var(--ink);
  letter-spacing:-.02em; line-height:1.25; margin:0; }
.kam-sub { font-size:.9rem; color:var(--muted); margin-top:.45rem; line-height:1.6; }

/* 결과 머리말 */
.kam-corp { display:flex; align-items:baseline; gap:.6rem; margin:.2rem 0 .9rem; }
.kam-corp-name { font-size:1.45rem; font-weight:700; color:var(--ink); letter-spacing:-.02em; }
.kam-corp-code { font-size:.85rem; color:var(--muted); font-variant-numeric:tabular-nums; }

/* 메타 칩 */
.kam-chips { display:flex; flex-wrap:wrap; gap:.4rem; margin-bottom:1.4rem; }
.kam-chip { font-size:.76rem; font-weight:600; padding:.3rem .7rem; border-radius:999px;
  background:var(--blue-50); color:var(--blue-700); border:1px solid var(--blue-100); }
.kam-chip.plain { background:var(--paper); color:var(--muted); border-color:var(--line); }

/* 섹션 라벨 */
.kam-section { display:flex; align-items:center; gap:.6rem; margin:1.8rem 0 .9rem; }
.kam-section-text { font-size:.78rem; font-weight:700; letter-spacing:.12em;
  text-transform:uppercase; color:var(--muted); white-space:nowrap; }
.kam-section-rule { flex:1; height:1px; background:var(--line); }

/* KAM 카드 */
.kam-card { border:1px solid var(--line); border-radius:12px; padding:1.3rem 1.4rem;
  margin-bottom:1rem; background:#fff; }
.kam-card-head { display:flex; gap:.85rem; align-items:flex-start; }
.kam-num { flex:none; width:1.7rem; height:1.7rem; border-radius:7px;
  background:var(--blue-600); color:#fff; font-size:.78rem; font-weight:700;
  display:flex; align-items:center; justify-content:center; font-variant-numeric:tabular-nums; }
.kam-easy { font-size:1.06rem; font-weight:700; color:var(--ink);
  line-height:1.45; letter-spacing:-.01em; }
.kam-orig { font-size:.8rem; color:var(--muted); margin-top:.3rem; line-height:1.5; }
.kam-body { margin-top:1.1rem; padding-left:2.55rem; }
.kam-label { font-size:.7rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase;
  color:var(--blue-600); margin-bottom:.35rem; }
.kam-text { font-size:.92rem; color:#1E293B; line-height:1.75; margin-bottom:1rem; }
.kam-text:last-child { margin-bottom:0; }

/* 카드 안 원문 보기 */
.kam-raw { margin-top:1.1rem; padding-left:2.55rem; }
.kam-raw details { border-top:1px solid var(--line); padding-top:.85rem; }
.kam-raw summary { font-size:.8rem; font-weight:600; color:var(--muted);
  cursor:pointer; list-style:none; display:flex; align-items:center; gap:.4rem; }
.kam-raw summary::-webkit-details-marker { display:none; }
.kam-raw summary::before { content:"+"; font-weight:700; color:var(--blue-600); }
.kam-raw details[open] summary::before { content:"−"; }
.kam-raw summary:hover { color:var(--blue-600); }
.kam-raw-inner { margin-top:.9rem; padding:1rem 1.1rem; background:var(--paper);
  border-radius:9px; border:1px solid var(--line); }
.kam-raw-label { font-size:.7rem; font-weight:700; letter-spacing:.08em;
  text-transform:uppercase; color:var(--muted); margin-bottom:.3rem; }
.kam-raw-text { font-size:.85rem; color:#334155; line-height:1.7; margin-bottom:.9rem; }
.kam-raw-text:last-child { margin-bottom:0; }

/* 상태 안내용 expander (원문 전체) */
div[data-testid="stExpander"] details { border:1px solid var(--line); border-radius:10px; }
div[data-testid="stExpander"] summary { font-size:.82rem; color:var(--muted); font-weight:600; }
div[data-testid="stExpander"] summary:hover { color:var(--blue-600); }

/* 위젯 */
div[data-testid="stTextInput"] input { border-radius:9px; }
div[data-testid="stButton"] button { border-radius:9px; font-weight:600; }
div[data-testid="stAlert"] { border-radius:10px; }
hr { margin:1.6rem 0; border-color:var(--line); }
</style>
"""


def hero(title: str, subtitle: str, eyebrow: str = "DART · Key Audit Matters") -> str:
    return (
        f'<div class="kam-hero"><div class="kam-eyebrow">{eyebrow}</div>'
        f'<h1 class="kam-title">{title}</h1>'
        f'<div class="kam-sub">{subtitle}</div></div>'
    )


def section(text: str) -> str:
    return (
        f'<div class="kam-section"><span class="kam-section-text">{text}</span>'
        f'<span class="kam-section-rule"></span></div>'
    )


def corp_heading(name: str, code: str) -> str:
    return (
        f'<div class="kam-corp"><span class="kam-corp-name">{name}</span>'
        f'<span class="kam-corp-code">{code}</span></div>'
    )


def chips(*labels: tuple[str, bool]) -> str:
    items = "".join(
        f'<span class="kam-chip{"" if strong else " plain"}">{text}</span>'
        for text, strong in labels
        if text
    )
    return f'<div class="kam-chips">{items}</div>'


def card_head(number: int, headline: str, original: str | None) -> str:
    sub = f'<div class="kam-orig">{original}</div>' if original else ""
    return (
        f'<div class="kam-card-head"><div class="kam-num">{number:02d}</div>'
        f'<div><div class="kam-easy">{headline}</div>{sub}</div></div>'
    )


def body(blocks: list[tuple[str, str]]) -> str:
    parts = "".join(
        f'<div class="kam-label">{label}</div><div class="kam-text">{text}</div>'
        for label, text in blocks
    )
    return f'<div class="kam-body">{parts}</div>'


def raw_details(reason: str, response: str) -> str:
    """감사보고서 원문을 카드 안에서 펼쳐 본다."""
    return (
        '<div class="kam-raw"><details><summary>감사보고서 원문 보기</summary>'
        '<div class="kam-raw-inner">'
        '<div class="kam-raw-label">핵심감사사항으로 결정한 이유</div>'
        f'<div class="kam-raw-text">{reason}</div>'
        '<div class="kam-raw-label">핵심감사사항이 감사에서 다루어진 방법</div>'
        f'<div class="kam-raw-text">{response}</div>'
        "</div></details></div>"
    )
