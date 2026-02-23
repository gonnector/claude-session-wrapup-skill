#!/usr/bin/env python3
"""
save-wrapup.py - 세션 요약 + Lesson-Learned JSONL 저장

Usage:
    echo '{"session_id":...}' | python save-wrapup.py

stdin JSON 구조:
{
  "session_id": "abc-123",
  "session_name": "세션 이름",
  "project": "z:/_ai/skills/lesson-learned",
  "date": "2026-02-23T15:30:00",
  "summary": { "info": [], "qa": [], "conclusions": [], "actions": [] },
  "user_lessons": [ { "type": "...", "category": "...", "title": "...", "summary": "...", "context": "...", "detail_ref": "", "tags": [] } ],
  "ai_lessons": [ { "type": "...", "category": "...", "title": "...", "summary": "...", "context": "...", "detail_ref": "", "tags": [] } ]
}

출력: 저장 결과 JSON (stdout)
"""

import json
import os
import re
import sys
from pathlib import Path

# Lesson-Learned 저장 경로 (고정)
USER_LESSONS_DIR = Path(r"Z:\_myself\lesson-learned")
AI_LESSONS_DIR = Path(r"Z:\_ai\lesson-learned")


def get_next_id(filepath: Path, prefix: str) -> str:
    """기존 JSONL에서 마지막 ID를 읽어 다음 번호 할당."""
    if not filepath.exists() or filepath.stat().st_size == 0:
        return f"{prefix}-001"

    last_id = None
    with open(filepath, "r", encoding="utf-8") as f:
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
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


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
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"error": "stdin이 비어 있습니다"}))
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
    if summary and any(summary.get(k) for k in ["info", "qa", "conclusions", "actions"]):
        project_path = Path(data["project"].replace("/", os.sep))
        summary_file = project_path / ".claude" / "session-summaries" / "summaries.jsonl"
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
