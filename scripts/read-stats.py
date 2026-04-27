#!/usr/bin/env python
"""
read-stats.py - Lesson-Learned 및 세션 요약 누적 통계 조회

Usage:
    python read-stats.py [project_path]

project_path 미지정 시 세션 요약은 제외하고 lesson-learned 통계만 출력.
출력: JSON (stdout)
"""

import io
import json
import os
import re
import sys
from pathlib import Path

# Windows stdout UTF-8 강제
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

USER_LESSONS_FILE = Path(r"E:\0\_myself\lesson-learned\lessons.jsonl")
AI_LESSONS_FILE = Path(r"E:\0\_ai\lesson-learned\lessons.jsonl")
SESSION_SUMMARIES_DIR = Path(r"E:\0\_ai\session-summaries")
AI_ROOT = Path(os.environ.get("AIOS_PATH") or os.environ.get("AI_ROOT") or os.environ.get("AIOS") or r"Z:\_ai")


def sanitize_project_path(project: str) -> str:
    """프로젝트 경로를 디렉토리명으로 치환."""
    s = project.replace("\\", "/").rstrip("/")
    s = re.sub(r"[:/]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


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


def _scan_summaries_dir(base_dir: Path) -> tuple[int, int, set]:
    """summaries 디렉토리 스캔 → (총 건수, 총 소요시간, 세션ID set)."""
    total = 0; elapsed = 0; sids = set()
    if not base_dir.exists():
        return total, elapsed, sids
    for d in base_dir.iterdir():
        if not d.is_dir():
            continue
        sf = d / "summaries.jsonl"
        if sf.exists():
            total, elapsed, sids = _scan_jsonl(sf, total, elapsed, sids)
    return total, elapsed, sids


def _scan_agent_wrapups(agents_dir: Path) -> tuple[int, int, set]:
    """모든 에이전트의 wrapup/sessions/ 스캔."""
    total = 0; elapsed = 0; sids = set()
    if not agents_dir.exists():
        return total, elapsed, sids
    for agent_dir in agents_dir.iterdir():
        if not agent_dir.is_dir():
            continue
        sessions_dir = agent_dir / "wrapup" / "sessions"
        if not sessions_dir.exists():
            continue
        for sf in sessions_dir.glob("*.jsonl"):
            total, elapsed, sids = _scan_jsonl(sf, total, elapsed, sids)
    return total, elapsed, sids


def _scan_jsonl(filepath: Path, total: int, elapsed: int, sids: set) -> tuple[int, int, set]:
    """단일 JSONL 파일에서 요약 통계 누적."""
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if not isinstance(entry, dict):
                    continue
                total += 1
                sid = entry.get("session_id", "")
                if sid:
                    sids.add(sid)
                timing = entry.get("timing")
                if timing and isinstance(timing, dict):
                    elapsed += timing.get("elapsed_minutes", 0)
            except json.JSONDecodeError:
                continue
    return total, elapsed, sids


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Wrapup 누적 통계 조회")
    parser.add_argument("project_path", nargs="?", default=None)
    parser.add_argument("--agent", default=None, help="에이전트명 (또는 CLAUDE_AGENT_NAME 환경변수)")
    args = parser.parse_args()

    project_path = args.project_path
    import os
    agent = (args.agent or os.environ.get("CLAUDE_AGENT_NAME", "")).strip().lower() or None

    # AI 학습 파일 결정
    if agent:
        ai_lessons_file = AI_ROOT / "agents" / agent / "wrapup" / "lessons.jsonl"
    else:
        ai_lessons_file = AI_LESSONS_FILE

    stats = {
        "user_lessons": {
            "total": count_jsonl(USER_LESSONS_FILE),
            "categories": get_categories(USER_LESSONS_FILE),
        },
        "ai_lessons": {
            "total": count_jsonl(ai_lessons_file),
            "categories": get_categories(ai_lessons_file),
        },
    }

    # 글로벌 통계: 기존 경로 + 모든 에이전트 폴더 합산
    g1_total, g1_elapsed, g1_sids = _scan_summaries_dir(SESSION_SUMMARIES_DIR)
    g2_total, g2_elapsed, g2_sids = _scan_agent_wrapups(AI_ROOT / "agents")
    global_total = g1_total + g2_total
    total_elapsed = g1_elapsed + g2_elapsed
    unique_session_ids = g1_sids | g2_sids

    if project_path:
        project_slug = sanitize_project_path(project_path)
        if agent:
            summary_file = AI_ROOT / "agents" / agent / "wrapup" / "sessions" / f"{project_slug}.jsonl"
        else:
            summary_file = SESSION_SUMMARIES_DIR / project_slug / "summaries.jsonl"
        stats["session_summaries"] = {
            "total": count_jsonl(summary_file),
            "global_total": global_total,
            "unique_sessions": len(unique_session_ids),
            "total_elapsed_minutes": total_elapsed,
            "file": str(summary_file),
        }
    else:
        stats["session_summaries"] = {
            "global_total": global_total,
            "unique_sessions": len(unique_session_ids),
            "total_elapsed_minutes": total_elapsed,
        }

    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
