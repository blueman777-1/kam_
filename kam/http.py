"""DART 로 나가는 모든 요청이 지나는 한 곳.

Streamlit Community Cloud 는 해외 리전에서 도는데, FSS 서버는 그쪽 IP로부터의
연결을 받아주지 않는다 (실측: ConnectTimeout). 그래서 DART_PROXY_BASE 가
설정되어 있으면 국내 리전에 둔 중계를 거쳐 나간다. 설정이 없으면 직접 나간다.
"""

from urllib.parse import urlencode

import requests

from kam.settings import get_secret

PROXY_KEY = "DART_PROXY_BASE"
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://dart.fss.or.kr/"}
DEFAULT_TIMEOUT = 30


def build_url(url: str, params: dict | None) -> str:
    return f"{url}?{urlencode(params)}" if params else url


def get(url: str, params: dict | None = None, timeout: int = DEFAULT_TIMEOUT):
    """DART 에 GET 요청한다. 중계가 설정되어 있으면 그쪽을 거친다."""
    proxy = get_secret(PROXY_KEY)
    if proxy:
        return requests.get(
            f"{proxy.rstrip('/')}/api/dart",
            params={"url": build_url(url, params)},
            headers=HEADERS,
            timeout=timeout,
        )
    return requests.get(url, params=params, headers=HEADERS, timeout=timeout)
