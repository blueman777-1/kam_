"""여러 상장사를 한꺼번에 조회해 추출 성공률을 측정한다.

'모든 기업에서 잘 되는가'는 주장할 수 없고 측정해야 하는 값이다.
이 스크립트는 그 값을 숫자로 만든다.

사용법:
    OPENDART_API_KEY=... .venv/bin/python scripts/validate_batch.py [개수]
"""

import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kam import corp_index  # noqa: E402
from kam.models import Status  # noqa: E402
from kam.resolver import resolve_latest_kam  # noqa: E402
from kam.settings import OPENDART_KEY, get_secret  # noqa: E402

SAMPLE = [
    "005930", "000660", "035420", "035720", "005380", "051910", "006400", "207940",
    "068270", "005490", "012330", "028260", "066570", "003550", "015760", "017670",
    "034730", "018260", "032830", "086790", "105560", "055550", "316140", "024110",
    "010130", "011200", "009150", "090430", "097950", "271560", "128940", "302440",
    "247540", "086520", "196170", "222800", "141080", "145020", "091990", "068760",
]


def main():
    api_key = get_secret(OPENDART_KEY)
    if not api_key:
        print("OPENDART_API_KEY 가 필요합니다.")
        return 1

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(SAMPLE)
    index = corp_index.load_index(api_key)
    counts = Counter()
    problems = []

    targets = SAMPLE[:limit]
    for n, code in enumerate(targets, start=1):
        hits = corp_index.search(index, code)
        if not hits:
            counts["종목코드미확인"] += 1
            problems.append((code, "종목코드미확인", ""))
            continue

        hit = hits[0]
        started = time.time()
        result = resolve_latest_kam(api_key, hit)
        elapsed = time.time() - started

        counts[result.status.value] += 1
        mark = {
            Status.SUCCESS: "OK",
            Status.KAM_NOT_PRESENT: "--",
            Status.MANUAL_REVIEW_REQUIRED: "??",
            Status.FAILED: "XX",
        }[result.status]
        detail = f"{len(result.items)}건" if result.status is Status.SUCCESS else (
            result.message or result.status.value
        )
        print(f"[{n:2d}/{len(targets)}] {mark} {hit.corp_name:16s} {detail:34s} {elapsed:5.1f}s")

        if result.status in (Status.MANUAL_REVIEW_REQUIRED, Status.FAILED):
            problems.append((hit.corp_name, result.status.value, result.message or ""))

    total = sum(counts.values())
    print("\n" + "=" * 60)
    print(f"총 {total}개사")
    for status, count in counts.most_common():
        print(f"  {status:24s} {count:3d}건  ({count / total * 100:5.1f}%)")

    readable = counts["success"] + counts["kam_not_present"]
    print(f"\n정상 판정(성공 + KAM없음): {readable}/{total} = {readable / total * 100:.1f}%")
    if problems:
        print("\n확인이 필요한 건:")
        for name, status, message in problems:
            print(f"  - {name}: {status} {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
