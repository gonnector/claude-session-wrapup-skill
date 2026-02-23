#!/usr/bin/env python3
"""
read-stats.py - Lesson-Learned 및 세션 요약 누적 통계 조회

Usage:
    python read-stats.py [project_path]

project_path 미지정 시 세션 요약은 제외하고 lesson-learned 통계만 출력.
출력: JSON (stdout)
"""

import json
import sys
from pathlib import Path

USER_LESSONS_FILE = Path(r"Z:\_myself\lesson-learned\lessons.jsonl")
AI_LESSONS_FILE = Path(r"Z:\_ai\lesson-learned\lessons.jsonl")


def count_jsonl(filepath: Path) -> int:
    """JSONL 파일의 유효한 행 수 반환."""
    if not filepath.exists():
        return 0
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def get_categories(filepath: Path) -> dict:
    """카테고리별 건수를 집계."""
    cats = {}
    if not filepath.exists():
        return cats
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                cat = entry.get("category", "uncategorized")
                cats[cat] = cats.get(cat, 0) + 1
            except json.JSONDecodeError:
                continue
    return cats


def main():
    project_path = sys.argv[1] if len(sys.argv) > 1 else None

    stats = {
        "user_lessons": {
            "total": count_jsonl(USER_LESSONS_FILE),
            "categories": get_categories(USER_LESSONS_FILE),
        },
        "ai_lessons": {
            "total": count_jsonl(AI_LESSONS_FILE),
            "categories": get_categories(AI_LESSONS_FILE),
        },
    }

    if project_path:
        summary_file = Path(project_path) / ".claude" / "session-summaries" / "summaries.jsonl"
        stats["session_summaries"] = {
            "total": count_jsonl(summary_file),
            "file": str(summary_file),
        }

    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
