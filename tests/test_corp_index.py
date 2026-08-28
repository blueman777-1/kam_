"""기업 검색 테스트 — corpCode.xml 파싱과 검색 규칙."""

from kam.corp_index import parse_corp_xml, search

SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<result>
  <list><corp_code>00126380</corp_code><corp_name>삼성전자</corp_name>
        <stock_code>005930</stock_code><modify_date>20260101</modify_date></list>
  <list><corp_code>00164779</corp_code><corp_name>삼성SDI</corp_name>
        <stock_code>006400</stock_code><modify_date>20260101</modify_date></list>
  <list><corp_code>01515323</corp_code><corp_name>삼성에피스홀딩스</corp_name>
        <stock_code>0126Z0</stock_code><modify_date>20260101</modify_date></list>
  <list><corp_code>00999999</corp_code><corp_name>비상장회사</corp_name>
        <stock_code> </stock_code><modify_date>20260101</modify_date></list>
</result>
"""


def index():
    return parse_corp_xml(SAMPLE)


def test_비상장사는_제외된다():
    names = [hit.corp_name for hit in index()]
    assert "비상장회사" not in names
    assert len(index()) == 3


def test_종목코드_앞자리_0이_보존된다():
    hit = search(index(), "005930")[0]
    assert hit.stock_code == "005930"
    assert hit.corp_name == "삼성전자"


def test_영문자가_포함된_종목코드도_찾는다():
    hit = search(index(), "0126Z0")[0]
    assert hit.corp_name == "삼성에피스홀딩스"


def test_종목코드는_대소문자를_가리지_않는다():
    assert search(index(), "0126z0")[0].corp_name == "삼성에피스홀딩스"


def test_기업명_부분일치로_여러_후보를_돌려준다():
    names = [hit.corp_name for hit in search(index(), "삼성")]
    assert names == ["삼성SDI", "삼성에피스홀딩스", "삼성전자"] or set(names) == {
        "삼성전자",
        "삼성SDI",
        "삼성에피스홀딩스",
    }
    assert len(names) == 3


def test_정확히_일치하는_기업명이_맨_앞에_온다():
    assert search(index(), "삼성전자")[0].corp_name == "삼성전자"


def test_공백은_무시된다():
    assert search(index(), " 삼성전자 ")[0].corp_name == "삼성전자"


def test_없는_기업은_빈_목록():
    assert search(index(), "존재하지않는회사") == []


def test_점검중_응답은_한국어_오류로_바뀐다():
    """정상 응답은 zip 이므로, XML 이 오면 오류다. BadZipFile 로 죽으면 안 된다."""
    import pytest

    from kam.corp_index import raise_if_error_xml
    from kam.dart_api import DartApiError

    payload = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        "<result><status>800</status><message>시스템 점검으로 인한  서비스가 중지 중입니다."
        "</message></result>"
    ).encode("utf-8")

    with pytest.raises(DartApiError) as caught:
        raise_if_error_xml(payload)
    assert caught.value.status == "800"
    assert "점검" in str(caught.value)


def test_zip_본문은_통과시킨다():
    from kam.corp_index import raise_if_error_xml

    raise_if_error_xml(b"PK\x03\x04somezipbytes")
