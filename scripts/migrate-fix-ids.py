#!/usr/bin/env python
"""
migrate-fix-ids.py - 전체 JSONL 엔트리의 ID를 실제 date 기반으로 재할당

기존 get_next_id() 버그로 인해 ID의 날짜 부분이 첫 엔트리 날짜에 고정된 문제를 수정.
각 엔트리의 date 필드에서 실제 날짜를 추출하여 ID를 재할당한다.

Usage:
    python migrate-fix-ids.py           # dry-run
    python migrate-fix-ids.py --apply   # 실제 적용
"""

import argparse
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SUMMARIES_DIR = Path(r"Z:\_ai\session-summaries")
USER_LESSONS = Path(r"Z:\_myself\lesson-learned\lessons.jsonl")
AI_LESSONS = Path(r"Z:\_ai\lesson-learned\lessons.jsonl")


def fix_ids_in_file(filepath: Path, id_prefix: str, apply: bool) -> dict:
    """파일 내 모든 엔트리의 ID를 date 기반으로 재할당."""
    if not filepath.exists():
        return {"total": 0, "fixed": 0, "unchanged": 0}

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    entries = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        try:
            e = json.loads(s)
            if isinstance(e, dict):
                entries.append(e)
        except json.JSONDecodeError:
            continue

    if not entries:
        return {"total": 0, "fixed": 0, "unchanged": 0}

    # 날짜별 카운터: 파일 순서대로 순회하며 같은 날짜 내에서 001, 002, ... 할당
    date_counters = defaultdict(int)
    fixed = 0
    unchanged = 0
    changes = []

    for e in entries:
        date_str = e.get("date", "")
        if not date_str or len(date_str) < 10:
            unchanged += 1
            continue

        actual_date = date_str[:10].replace("-", "")
        prefix = f"{id_prefix}-{actual_date}"
        date_counters[actual_date] += 1
        new_id = f"{prefix}-{date_counters[actual_date]:03d}"
        old_id = e.get("id", "")

        if old_id != new_id:
            changes.append((old_id, new_id))
            e["id"] = new_id
            fixed += 1
        else:
            unchanged += 1

    if apply and fixed > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

    return {"total": len(entries), "fixed": fixed, "unchanged": unchanged,
            "changes": changes}


def main():
    parser = argparse.ArgumentParser(description="ID 재할당 마이그레이션")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not args.apply:
        print("=== DRY RUN ===\n")

    grand = {"total": 0, "fixed": 0}

    # 1) Session Summaries
    print("── Session Summaries ──")
    for sd in sorted(SUMMARIES_DIR.iterdir()):
        if not sd.is_dir():
            continue
        sf = sd / "summaries.jsonl"
        if not sf.exists():
            continue
        result = fix_ids_in_file(sf, "ws", args.apply)
        if result["fixed"] > 0:
            print(f"  {sd.name}: {result['fixed']}/{result['total']} fixed")
            for old, new in result["changes"][:3]:
                print(f"    {old} → {new}")
            if len(result["changes"]) > 3:
                print(f"    ... +{len(result['changes'])-3} more")
        grand["total"] += result["total"]
        grand["fixed"] += result["fixed"]

    # 2) User Lessons
    print("\n── User Lessons ──")
    result = fix_ids_in_file(USER_LESSONS, "ll-user", args.apply)
    print(f"  {result['fixed']}/{result['total']} fixed")
    for old, new in result.get("changes", [])[:3]:
        print(f"    {old} → {new}")
    if len(result.get("changes", [])) > 3:
        print(f"    ... +{len(result['changes'])-3} more")
    grand["total"] += result["total"]
    grand["fixed"] += result["fixed"]

    # 3) AI Lessons
    print("\n── AI Lessons ──")
    result = fix_ids_in_file(AI_LESSONS, "ll-ai", args.apply)
    print(f"  {result['fixed']}/{result['total']} fixed")
    for old, new in result.get("changes", [])[:3]:
        print(f"    {old} → {new}")
    if len(result.get("changes", [])) > 3:
        print(f"    ... +{len(result['changes'])-3} more")
    grand["total"] += result["total"]
    grand["fixed"] += result["fixed"]

    print(f"\n{'적용 완료' if args.apply else 'Dry-run 완료'}:")
    print(f"  전체: {grand['total']}건, 수정: {grand['fixed']}건")


if __name__ == "__main__":
    main()
