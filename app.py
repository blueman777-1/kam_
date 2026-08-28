"""DART 핵심감사사항(KAM) 조회 앱."""

import streamlit as st

from kam import corp_index, summarize
from kam.models import Status
from kam.resolver import resolve_latest_kam
from kam.settings import (
    DEFAULT_GEMINI_MODEL,
    GEMINI_KEY,
    GEMINI_MODEL_KEY,
    OPENDART_KEY,
    get_secret,
)

st.set_page_config(page_title="DART KAM 조회", page_icon="📑")

STATUS_HELP = {
    Status.KAM_NOT_PRESENT: (
        "이 감사보고서에는 핵심감사사항이 없습니다. "
        "찾지 못한 것이 아니라 보고서에 실제로 기재되지 않은 경우입니다."
    ),
    Status.MANUAL_REVIEW_REQUIRED: (
        "핵심감사사항으로 보이는 내용은 있으나 구조를 완전히 읽지 못했습니다. "
        "아래 원문과 DART 원본을 직접 확인해 주세요."
    ),
}


@st.cache_data(show_spinner=False)
def load_corp_index(_api_key: str, refresh: bool):
    return corp_index.load_index(_api_key, refresh=refresh)


@st.cache_data(show_spinner=False)
def explain_cached(fingerprint: str, model: str, _items, _api_key: str):
    """원문 해시가 캐시 키이므로 원문이 바뀌면 설명도 새로 만들어진다."""
    return summarize.explain(_items, _api_key, model)


def render_success(result):
    left, right = st.columns(2)
    left.metric("보고기간", result.filing.period if result.filing else "-")
    right.metric("감사인", result.auditor or "-")

    caption = f"{result.report_kind}감사보고서 · {result.filing.report_nm}"
    if result.filing and result.filing.is_amended:
        caption += " · 정정공시"
    st.caption(caption)

    explanations = None
    gemini_key = get_secret(GEMINI_KEY)
    if gemini_key:
        model = get_secret(GEMINI_MODEL_KEY) or DEFAULT_GEMINI_MODEL
        with st.spinner("쉬운 설명을 만드는 중..."):
            try:
                explanations = explain_cached(
                    summarize.fingerprint(result.items), model, result.items, gemini_key
                )
            except summarize.SummaryError as error:
                st.warning(str(error))
    else:
        st.info("GEMINI_API_KEY 를 설정하면 쉬운 설명이 함께 표시됩니다. 지금은 원문만 보여줍니다.")

    st.subheader(f"핵심감사사항 {len(result.items)}건")
    for n, item in enumerate(result.items):
        explanation = explanations[n] if explanations and n < len(explanations) else None
        heading = explanation.easy_title if explanation else item.title
        with st.container(border=True):
            st.markdown(f"**{n + 1}. {heading}**")
            st.caption(item.title)
            if explanation:
                st.markdown(f"**무엇이 문제인가**\n\n{explanation.what}")
                st.markdown(f"**감사인이 한 일**\n\n{explanation.how}")
            with st.expander("감사보고서 원문 보기"):
                st.markdown("**핵심감사사항으로 결정한 이유**")
                st.text(item.reason)
                st.markdown("**핵심감사사항이 감사에서 다루어진 방법**")
                st.text(item.response)


def render(result):
    st.divider()
    st.markdown(f"### {result.corp_name} ({result.stock_code})")

    if result.status is Status.FAILED:
        st.error(f"[{result.failed_stage}] {result.message}")
        return

    if result.dart_url:
        st.link_button("DART 원문 열기", result.dart_url)

    if result.status is Status.SUCCESS:
        render_success(result)
    elif result.status is Status.KAM_NOT_PRESENT:
        st.info(STATUS_HELP[Status.KAM_NOT_PRESENT])
    else:
        st.warning(STATUS_HELP[Status.MANUAL_REVIEW_REQUIRED])
        with st.expander("감사보고서 원문 보기", expanded=True):
            st.text(result.raw_text)


st.title("DART 핵심감사사항 조회")
st.caption("최신 사업보고서의 핵심감사사항을 찾고, 어려운 감사 문구를 쉬운 말로 설명합니다.")

dart_key = get_secret(OPENDART_KEY)
if not dart_key:
    st.error(
        "OPENDART_API_KEY 가 없습니다. `.streamlit/secrets.toml` 에 키를 넣어 주세요. "
        "(`.streamlit/secrets.toml.example` 참고)"
    )
    st.stop()

query = st.text_input("기업명 또는 종목코드", placeholder="예: 삼성전자 또는 005930")
search_col, refresh_col = st.columns([3, 1])
searched = search_col.button("기업 찾기", type="primary", use_container_width=True)
refresh = refresh_col.checkbox("기업목록 새로 받기")

if searched:
    st.session_state.pop("result", None)
    if not query.strip():
        st.warning("기업명이나 종목코드를 입력해 주세요.")
    else:
        with st.spinner("기업 목록에서 찾는 중..."):
            try:
                index = load_corp_index(dart_key, refresh)
                st.session_state["hits"] = corp_index.search(index, query)
            except Exception as error:
                st.session_state.pop("hits", None)
                st.error(f"기업 목록을 불러오지 못했습니다: {type(error).__name__}")

hits = st.session_state.get("hits")
if hits is not None:
    if not hits:
        st.info("해당 상장기업을 찾지 못했습니다.")
    else:
        labels = [f"{hit.corp_name} ({hit.stock_code})" for hit in hits]
        chosen = st.radio("기업 선택", labels, index=0)
        if st.button("최신 KAM 조회", type="primary"):
            hit = hits[labels.index(chosen)]
            with st.spinner(f"{hit.corp_name}의 최신 감사보고서를 찾는 중..."):
                st.session_state["result"] = resolve_latest_kam(dart_key, hit, refresh=refresh)

if "result" in st.session_state:
    render(st.session_state["result"])
