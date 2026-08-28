"""DART 핵심감사사항(KAM) 조회 앱."""

from html import escape

import streamlit as st

from kam import corp_index, style, summarize
from kam.dart_api import DartApiError
from kam.models import Status
from kam.resolver import resolve_latest_kam
from kam.settings import GEMINI_KEY, GEMINI_MODELS, OPENDART_KEY, get_secret

st.set_page_config(page_title="KAM Finder", page_icon="🔷", layout="centered")
st.markdown(style.CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_corp_index(_api_key: str, refresh: bool):
    return corp_index.load_index(_api_key, refresh=refresh)


@st.cache_data(show_spinner=False)
def explain_cached(fingerprint: str, _items, _api_key: str):
    """원문 해시가 캐시 키이므로 원문이 바뀌면 설명도 새로 만들어진다."""
    return summarize.explain(_items, _api_key, GEMINI_MODELS)


def paragraphs(text: str) -> str:
    return "<br>".join(escape(line) for line in text.split("\n") if line.strip())


def render_items(result, explanations):
    st.markdown(style.section(f"핵심감사사항 {len(result.items)}건"), unsafe_allow_html=True)

    for n, item in enumerate(result.items):
        explanation = explanations[n] if explanations and n < len(explanations) else None
        headline = escape(explanation.easy_title if explanation else item.title)
        original = escape(item.title) if explanation else None

        blocks = []
        if explanation:
            blocks = [
                ("무엇이 문제인가", escape(explanation.what)),
                ("감사인이 한 일", escape(explanation.how)),
            ]

        st.markdown(
            f'<div class="kam-card">{style.card_head(n + 1, headline, original)}'
            f"{style.body(blocks) if blocks else ''}"
            f"{style.raw_details(paragraphs(item.reason), paragraphs(item.response))}</div>",
            unsafe_allow_html=True,
        )


def render_success(result):
    explanations = None
    gemini_key = get_secret(GEMINI_KEY)
    if gemini_key:
        with st.spinner("원문을 쉬운 말로 옮기는 중..."):
            try:
                explanations = explain_cached(
                    summarize.fingerprint(result.items), result.items, gemini_key
                )
            except summarize.SummaryError as error:
                st.warning(f"{error} 원문은 그대로 보여드립니다.")
    else:
        st.info("GEMINI_API_KEY 를 설정하면 쉬운 설명이 함께 표시됩니다. 지금은 원문만 보여줍니다.")

    render_items(result, explanations)


def render(result):
    st.divider()
    st.markdown(
        style.corp_heading(escape(result.corp_name), escape(result.stock_code)),
        unsafe_allow_html=True,
    )

    if result.status is Status.FAILED:
        st.error(f"**{result.failed_stage} 단계에서 실패했습니다.**\n\n{result.message}")
        return

    filing = result.filing
    st.markdown(
        style.chips(
            (escape(filing.period) if filing else "", True),
            (f"{result.report_kind}감사보고서" if result.report_kind else "", False),
            (escape(result.auditor or ""), False),
            ("정정공시" if filing and filing.is_amended else "", False),
        ),
        unsafe_allow_html=True,
    )

    if result.status is Status.SUCCESS:
        render_success(result)
    elif result.status is Status.KAM_NOT_PRESENT:
        st.info(
            "**이 감사보고서에는 핵심감사사항이 없습니다.**\n\n"
            "찾지 못한 것이 아니라, 보고서에 실제로 기재되지 않은 경우입니다."
        )
    else:
        st.warning(
            "**구조를 완전히 읽지 못했습니다.**\n\n"
            "핵심감사사항으로 보이는 내용은 있으나 항목을 나누지 못했습니다. "
            "아래 원문과 DART 원본을 직접 확인해 주세요."
        )
        with st.expander("감사보고서 원문 보기", expanded=True):
            st.text(result.raw_text)

    if result.dart_url:
        st.link_button("DART에서 원문 보기", result.dart_url, use_container_width=True)


# ── 화면 ─────────────────────────────────────────────────────────────
st.markdown(
    style.hero(
        "핵심감사사항 조회",
        "기업명이나 종목코드를 넣으면 최신 사업보고서에 첨부된 감사보고서를 찾아 "
        "핵심감사사항을 정리하고, 어려운 감사 문구를 쉬운 말로 옮깁니다.",
    ),
    unsafe_allow_html=True,
)

dart_key = get_secret(OPENDART_KEY)
if not dart_key:
    st.error(
        "**OPENDART_API_KEY 가 없습니다.**\n\n"
        "`.streamlit/secrets.toml` 에 키를 넣어 주세요. "
        "(`.streamlit/secrets.toml.example` 참고)"
    )
    st.stop()

query = st.text_input("기업명 또는 종목코드", placeholder="삼성전자, 005930, 카카오 …")
left, right = st.columns([2, 1])
searched = left.button("기업 찾기", type="primary", use_container_width=True)
refresh = right.checkbox("기업목록 새로 받기")

if searched:
    st.session_state.pop("result", None)
    if not query.strip():
        st.warning("기업명이나 종목코드를 입력해 주세요.")
    else:
        with st.spinner("상장기업 목록에서 찾는 중..."):
            try:
                index = load_corp_index(dart_key, refresh)
                st.session_state["hits"] = corp_index.search(index, query)
            except DartApiError as error:
                st.session_state.pop("hits", None)
                st.error(error.message)
            except Exception as error:
                st.session_state.pop("hits", None)
                st.error(f"기업 목록을 불러오지 못했습니다: {type(error).__name__}")

hits = st.session_state.get("hits")
if hits is not None:
    if not hits:
        st.info("해당 상장기업을 찾지 못했습니다. 기업명 일부나 6자리 종목코드로 다시 시도해 보세요.")
    else:
        st.markdown(style.section(f"검색 결과 {len(hits)}곳"), unsafe_allow_html=True)
        labels = [f"{hit.corp_name}  ·  {hit.stock_code}" for hit in hits]
        chosen = st.radio("기업 선택", labels, index=0, label_visibility="collapsed")
        if st.button("최신 KAM 조회", type="primary", use_container_width=True):
            hit = hits[labels.index(chosen)]
            with st.spinner(f"{hit.corp_name}의 최신 감사보고서를 찾는 중..."):
                st.session_state["result"] = resolve_latest_kam(dart_key, hit, refresh=refresh)

if "result" in st.session_state:
    render(st.session_state["result"])
