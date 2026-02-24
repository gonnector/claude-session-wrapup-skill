#!/usr/bin/env python
"""
collect-meta.py - Step 1 메타정보 일괄 수집

Usage:
    python collect-meta.py

출력: JSON (stdout)
    {
        "date":         "2026-02-24T11:38:36",
        "project":      "Z:\\_ai\\skills\\wrapup",
        "session_id":   "...",
        "session_name": "...",
        "stats": {
            "user_lessons":      {"total": N, "categories": {...}},
            "ai_lessons":        {"total": N, "categories": {...}},
            "session_summaries": {"total": N, "file": "..."}
        }
    }
"""

import io
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Windows stdout UTF-8 강제
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ── 저장 경로 상수 ────────────────────────────────────────
USER_LESSONS_FILE = Path(r"Z:\_myself\lesson-learned\lessons.jsonl")
AI_LESSONS_FILE   = Path(r"Z:\_ai\lesson-learned\lessons.jsonl")
SESSION_SUMMARIES_DIR = Path(r"Z:\_ai\session-summaries")


# ── 통계 헬퍼 ────────────────────────────────────────────
def _count_jsonl(filepath: Path) -> int:
    if not filepath.exists():
        return 0
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def _get_categories(filepath: Path) -> dict:
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


def _sanitize_project_path(project: str) -> str:
    s = project.replace("\\", "/").rstrip("/")
    s = re.sub(r"[:/]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def collect_stats(project_path: str) -> dict:
    project_slug = _sanitize_project_path(project_path)
    summary_file = SESSION_SUMMARIES_DIR / project_slug / "summaries.jsonl"
    return {
        "user_lessons": {
            "total": _count_jsonl(USER_LESSONS_FILE),
            "categories": _get_categories(USER_LESSONS_FILE),
        },
        "ai_lessons": {
            "total": _count_jsonl(AI_LESSONS_FILE),
            "categories": _get_categories(AI_LESSONS_FILE),
        },
        "session_summaries": {
            "total": _count_jsonl(summary_file),
            "file": str(summary_file),
        },
    }


# ── 세션 정보 헬퍼 ────────────────────────────────────────
def collect_session(project_path: str) -> dict:
    last_component = Path(project_path).name
    claude_projects = Path.home() / ".claude" / "projects"

    if not claude_projects.exists():
        return {"session_id": "", "session_name": "", "error": "Claude projects directory not found"}

    matching_dirs = sorted(
        [d for d in claude_projects.iterdir() if d.is_dir() and last_component.lower() in d.name.lower()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    if not matching_dirs:
        return {"session_id": "", "session_name": "", "error": f"No project directory for: {last_component}"}

    project_dir = matching_dirs[0]
    jsonl_files = sorted(
        project_dir.glob("*.jsonl"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if not jsonl_files:
        return {"session_id": "", "session_name": "", "error": "No session files found"}

    session_file = jsonl_files[0]
    session_id   = session_file.stem
    session_name = ""

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("type") == "custom-title":
                    session_name = entry.get("customTitle", "")
                    break
            except json.JSONDecodeError:
                continue
    except Exception:
        pass

    return {"session_id": session_id, "session_name": session_name}


# ── 메인 ─────────────────────────────────────────────────
def main():
    project_path = os.getcwd()

    result = {
        "date":    datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "project": project_path,
        **collect_session(project_path),
        "stats":   collect_stats(project_path),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
