#!/usr/bin/env python
"""
migrate-timing.py - 기존 summaries.jsonl에 timing 데이터를 소급 적용

Usage:
    python migrate-timing.py           # dry-run (변경 없이 결과만 출력)
    python migrate-timing.py --apply   # 실제 적용

기존 엔트리의 session_id로 세션 JSONL 파일을 찾아 session_start를 추출하고,
date 필드(= wrapup 시각)와의 차이로 elapsed_minutes를 계산한다.
같은 session_id가 여러 번 등장하면 continuation 처리.
"""

import argparse
import io
import json
import sys
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SESSION_SUMMARIES_DIR = Path(r"Z:\_ai\session-summaries")
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


def utc_to_local_naive(utc_str: str) -> datetime:
    """UTC ISO string → local naive datetime."""
    if utc_str.endswith("Z"):
        utc_str = utc_str[:-1] + "+00:00"
    utc_dt = datetime.fromisoformat(utc_str)
    local_dt = utc_dt.astimezone()
    return local_dt.replace(tzinfo=None)


def find_session_start(session_id: str) -> str | None:
    """세션 JSONL 파일에서 가장 이른 타임스탬프를 추출."""
    matches = list(CLAUDE_PROJECTS_DIR.glob(f"*/{session_id}.jsonl"))
    if not matches:
        return None

    session_file = matches[0]
    earliest = None

    try:
        with open(session_file, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= 20:
                    break
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    entry = json.loads(stripped)
                    if not isinstance(entry, dict):
                        continue
                    ts = entry.get("timestamp")
                    if not ts:
                        snapshot = entry.get("snapshot")
                        if isinstance(snapshot, dict):
                            ts = snapshot.get("timestamp")
                    if ts and (earliest is None or ts < earliest):
                        earliest = ts
                except json.JSONDecodeError:
                    continue
    except Exception:
        return None

    return earliest


def process_file(summary_file: Path, apply: bool) -> dict:
    """하나의 summaries.jsonl 파일을 처리."""
    stats = {"total": 0, "updated": 0, "skipped_has_timing": 0,
             "skipped_no_session": 0, "skipped_no_date": 0}

    with open(summary_file, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    entries = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            entries.append(None)
            continue
        try:
            entry = json.loads(stripped)
            entries.append(entry if isinstance(entry, dict) else stripped)
        except json.JSONDecodeError:
            entries.append(stripped)

    # 1차: session_id별 wrapup 시각을 시간순 정렬 (continuation 처리용)
    session_wrapups = {}  # session_id -> [(index, date_str)]
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        sid = entry.get("session_id", "")
        date_str = entry.get("date", "")
        if sid and date_str:
            session_wrapups.setdefault(sid, []).append((i, date_str))

    # 시간순 정렬
    for sid in session_wrapups:
        session_wrapups[sid].sort(key=lambda x: x[1])

    # 2차: 각 엔트리에 timing 추가
    # session_start 캐시
    session_start_cache = {}
    modified = False

    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        stats["total"] += 1

        if entry.get("timing") is not None:
            stats["skipped_has_timing"] += 1
            continue

        sid = entry.get("session_id", "")
        date_str = entry.get("date", "")
        if not date_str:
            stats["skipped_no_date"] += 1
            continue

        # session_start 찾기
        if sid not in session_start_cache:
            utc_ts = find_session_start(sid)
            session_start_cache[sid] = utc_ts

        utc_ts = session_start_cache[sid]
        if not utc_ts:
            stats["skipped_no_session"] += 1
            continue

        session_start = utc_to_local_naive(utc_ts)
        wrapup_dt = datetime.fromisoformat(date_str)

        # continuation 체크: 이 session_id의 wrapup 목록에서 현재 엔트리의 순서 확인
        wrapup_list = session_wrapups.get(sid, [])
        wrapup_number = 1
        prev_wrapup_dt = None

        for idx, (entry_idx, entry_date) in enumerate(wrapup_list):
            if entry_idx == i:
                wrapup_number = idx + 1
                if idx > 0:
                    prev_date_str = wrapup_list[idx - 1][1]
                    prev_wrapup_dt = datetime.fromisoformat(prev_date_str)
                break

        is_continuation = prev_wrapup_dt is not None
        segment_start = prev_wrapup_dt if is_continuation else session_start

        elapsed = wrapup_dt - segment_start
        elapsed_minutes = max(0, int(elapsed.total_seconds() / 60))

        timing = {
            "session_start": session_start.strftime("%Y-%m-%dT%H:%M:%S"),
            "wrapup_start": wrapup_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "segment_start": segment_start.strftime("%Y-%m-%dT%H:%M:%S"),
            "elapsed_minutes": elapsed_minutes,
            "is_continuation": is_continuation,
            "wrapup_number": wrapup_number,
        }

        entry["timing"] = timing
        stats["updated"] += 1
        modified = True

    # 저장
    if apply and modified:
        with open(summary_file, "w", encoding="utf-8") as f:
            for entry in entries:
                if entry is None:
                    f.write("\n")
                elif isinstance(entry, dict):
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                else:
                    f.write(str(entry) + "\n")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Timing 소급 적용 마이그레이션")
    parser.add_argument("--apply", action="store_true", help="실제 적용 (없으면 dry-run)")
    args = parser.parse_args()

    if not args.apply:
        print("=== DRY RUN (--apply 없이 실행) ===\n")

    total_stats = {"total": 0, "updated": 0, "skipped_has_timing": 0,
                   "skipped_no_session": 0, "skipped_no_date": 0}
    total_elapsed = 0

    for summary_dir in sorted(SESSION_SUMMARIES_DIR.iterdir()):
        if not summary_dir.is_dir():
            continue
        sf = summary_dir / "summaries.jsonl"
        if not sf.exists():
            continue

        stats = process_file(sf, args.apply)

        if stats["total"] > 0:
            print(f"  {summary_dir.name}: {stats['updated']}/{stats['total']} updated"
                  + (f", {stats['skipped_no_session']} no session file" if stats['skipped_no_session'] else "")
                  + (f", {stats['skipped_has_timing']} already has timing" if stats['skipped_has_timing'] else ""))

        for k in total_stats:
            total_stats[k] += stats[k]

    # 적용 후 총 elapsed 확인
    if args.apply:
        for summary_dir in SESSION_SUMMARIES_DIR.iterdir():
            if not summary_dir.is_dir():
                continue
            sf = summary_dir / "summaries.jsonl"
            if not sf.exists():
                continue
            with open(sf, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if isinstance(entry, dict):
                            timing = entry.get("timing")
                            if timing and isinstance(timing, dict):
                                total_elapsed += timing.get("elapsed_minutes", 0)
                    except json.JSONDecodeError:
                        continue

    print(f"\n{'적용 완료' if args.apply else 'Dry-run 완료'}:")
    print(f"  전체 엔트리: {total_stats['total']}")
    print(f"  업데이트됨:  {total_stats['updated']}")
    print(f"  세션 파일 없음: {total_stats['skipped_no_session']}")
    if args.apply and total_elapsed > 0:
        h, m = divmod(total_elapsed, 60)
        print(f"  누적 협업 시간: {h}h {m:02d}m ({total_elapsed}분)")


if __name__ == "__main__":
    main()
