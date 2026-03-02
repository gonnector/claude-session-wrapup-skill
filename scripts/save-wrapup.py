#!/usr/bin/env python
"""
save-wrapup.py - 세션 요약 + Lesson-Learned JSONL 저장

Usage:
    python save-wrapup.py --file input.json
    python save-wrapup.py < input.json

    또는 직접 import:
    import importlib.util
    spec = importlib.util.spec_from_file_location("save_wrapup", "path/to/save-wrapup.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    result = mod.run(data)

입력 JSON 키 (summary 하위):
  info, qa, conclusions, done, actions
"""

import argparse
import io
import json
import re
import sys
from pathlib import Path

# Windows stdout/stdin UTF-8 강제
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stdin.encoding and sys.stdin.encoding.lower() != "utf-8":
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

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
                if not isinstance(entry, dict):
                    continue
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
        "evaluation": data.get("evaluation", None),
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
        "memory_ref": lesson.get("memory_ref", None),
    }


def run(data: dict) -> dict:
    """데이터 dict를 받아 저장하고 결과 dict를 반환한다."""
    required = ["session_id", "session_name", "project", "date"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return {"error": f"필수 필드 누락: {missing}"}

    result = {"saved": {}, "counts": {}}

    # 1) 세션 요약 저장
    summary = data.get("summary")
    has_summary = summary and any(summary.get(k) for k in ["info", "qa", "conclusions", "done", "actions"])
    has_evaluation = data.get("evaluation") is not None
    if has_summary or has_evaluation:
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

    return result


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
    except json.JSONDecodeError:
        # Windows 경로 백슬래시 미이스케이프 자동 수정 후 재시도
        # 유효한 JSON 이스케이프(\\ \" \/ \b \f \n \r \t \uXXXX)가 아닌 \ 를 \\ 로 치환
        import re as _re
        fixed = _re.sub(r'\\(?![\\/"bfnrtu])', r'\\\\', raw)
        try:
            data = json.loads(fixed)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"JSON 파싱 실패: {e}"}))
            sys.exit(1)

    result = run(data)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
