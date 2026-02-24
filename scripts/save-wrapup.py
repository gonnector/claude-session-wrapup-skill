#!/usr/bin/env python
"""
save-wrapup.py - 세션 요약 + Lesson-Learned JSONL 저장

Usage:
    python save-wrapup.py --file input.json
    python save-wrapup.py < input.json

입력 JSON 키 (summary 하위):
  info, qa, conclusions, done, actions

출력: 저장 결과 JSON (stdout)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# 고정 저장 경로
USER_LESSONS_DIR = Path(r"Z:\_myself\lesson-learned")
AI_LESSONS_DIR = Path(r"Z:\_ai\lesson-learned")
SESSION_SUMMARIES_DIR = Path(r"Z:\_ai\session-summaries")


def sanitize_project_path(project: str) -> str:
    """프로젝트 경로를 디렉토리명으로 치환. (Claude projects 방식)"""
    s = project.replace("\\", "/").rstrip("/")
    s = re.sub(r"[:/]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def get_next_id(filepath: Path, prefix: str) -> str:
    """기존 JSONL에서 마지막 ID를 읽어 다음 번호 할당."""
    if not filepath.exists() or filepath.stat().st_size == 0:
        return f"{prefix}-001"

    last_id = None
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                last_id = entry.get("id", "")
            except json.JSONDecodeError:
                continue

    if last_id:
        match = re.search(r"-(\d+)$", last_id)
        if match:
            next_num = int(match.group(1)) + 1
            return re.sub(r"-\d+$", f"-{next_num:03d}", last_id)

    return f"{prefix}-001"


def append_jsonl(filepath: Path, entry: dict) -> None:
    """JSONL 파일에 1줄 append."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False)
    with open(filepath, "a", encoding="utf-8", errors="replace") as f:
        f.write(line + "\n")


def build_summary_entry(data: dict, entry_id: str) -> dict:
    """세션 요약 JSONL 엔트리 구성."""
    summary = data.get("summary", {})
    return {
        "id": entry_id,
        "date": data["date"],
        "session_id": data["session_id"],
        "session_name": data["session_name"],
        "project": data["project"],
        "info_summary": summary.get("info", []),
        "qa_pairs": summary.get("qa", []),
        "conclusions": summary.get("conclusions", []),
        "work_done": summary.get("done", None),
        "action_items": summary.get("actions", []),
    }


def build_lesson_entry(data: dict, lesson: dict, entry_id: str) -> dict:
    """Lesson-Learned JSONL 엔트리 구성."""
    return {
        "id": entry_id,
        "date": data["date"],
        "session_id": data["session_id"],
        "session_name": data["session_name"],
        "project": data["project"],
        "type": lesson["type"],
        "category": lesson.get("category", ""),
        "title": lesson["title"],
        "summary": lesson["summary"],
        "context": lesson.get("context", ""),
        "detail_ref": lesson.get("detail_ref", ""),
        "tags": lesson.get("tags", []),
    }


def main():
    parser = argparse.ArgumentParser(description="Wrapup JSONL 저장")
    parser.add_argument("--file", "-f", help="입력 JSON 파일 경로 (미지정 시 stdin)")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read().strip()
    else:
        raw = sys.stdin.read().strip()

    if not raw:
        print(json.dumps({"error": "입력이 비어 있습니다"}))
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"JSON 파싱 실패: {e}"}))
        sys.exit(1)

    # 필수 필드 검증
    required = ["session_id", "session_name", "project", "date"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        print(json.dumps({"error": f"필수 필드 누락: {missing}"}))
        sys.exit(1)

    result = {"saved": {}, "counts": {}}

    # 1) 세션 요약 저장
    summary = data.get("summary")
    if summary and any(summary.get(k) for k in ["info", "qa", "conclusions", "done", "actions"]):
        project_slug = sanitize_project_path(data["project"])
        summary_file = SESSION_SUMMARIES_DIR / project_slug / "summaries.jsonl"
        today = data["date"][:10]
        sid = get_next_id(summary_file, f"ws-{today.replace('-', '')}")
        entry = build_summary_entry(data, sid)
        append_jsonl(summary_file, entry)
        result["saved"]["summary"] = str(summary_file)
        result["counts"]["summary"] = 1

    # 2) 사용자 Lesson-Learned 저장
    user_lessons = data.get("user_lessons", [])
    if user_lessons:
        user_file = USER_LESSONS_DIR / "lessons.jsonl"
        today = data["date"][:10]
        for lesson in user_lessons:
            lid = get_next_id(user_file, f"ll-user-{today.replace('-', '')}")
            entry = build_lesson_entry(data, lesson, lid)
            append_jsonl(user_file, entry)
        result["saved"]["user_lessons"] = str(user_file)
        result["counts"]["user_lessons"] = len(user_lessons)

    # 3) AI Lesson-Learned 저장
    ai_lessons = data.get("ai_lessons", [])
    if ai_lessons:
        ai_file = AI_LESSONS_DIR / "lessons.jsonl"
        today = data["date"][:10]
        for lesson in ai_lessons:
            lid = get_next_id(ai_file, f"ll-ai-{today.replace('-', '')}")
            entry = build_lesson_entry(data, lesson, lid)
            append_jsonl(ai_file, entry)
        result["saved"]["ai_lessons"] = str(ai_file)
        result["counts"]["ai_lessons"] = len(ai_lessons)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
