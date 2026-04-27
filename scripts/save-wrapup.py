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
import os
import re
import sys
from pathlib import Path

# Windows stdout/stdin UTF-8 강제
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stdin.encoding and sys.stdin.encoding.lower() != "utf-8":
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

# 저장 경로 — 환경변수 우선, fallback 신표준
USER_LESSONS_DIR = Path(os.environ.get("PERSONAL_PATH") or r"E:\GD\내 드라이브\_myself") / "lesson-learned"
_AIOS_FALLBACK = os.environ.get("AIOS_PATH") or r"c:\aios"
AI_LESSONS_DIR = Path(_AIOS_FALLBACK) / "lesson-learned"
SESSION_SUMMARIES_DIR = Path(_AIOS_FALLBACK) / "session-summaries"
AI_ROOT = Path(os.environ.get("AIOS_PATH") or os.environ.get("AI_ROOT") or os.environ.get("AIOS") or r"Z:\_ai")


def sanitize_project_path(project: str) -> str:
    """프로젝트 경로를 디렉토리명으로 치환. (Claude projects 방식)"""
    s = project.replace("\\", "/").rstrip("/")
    s = re.sub(r"[:/]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def get_next_id(filepath: Path, prefix: str) -> str:
    """같은 prefix(날짜 포함)를 가진 기존 ID 중 최대 번호 + 1을 반환."""
    if not filepath.exists() or filepath.stat().st_size == 0:
        return f"{prefix}-001"

    max_num = 0
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if not isinstance(entry, dict):
                    continue
                eid = entry.get("id", "")
                if eid.startswith(prefix):
                    match = re.search(r"-(\d+)$", eid)
                    if match:
                        max_num = max(max_num, int(match.group(1)))
            except json.JSONDecodeError:
                continue

    return f"{prefix}-{max_num + 1:03d}"


def append_jsonl(filepath: Path, entry: dict) -> None:
    """JSONL 파일에 1줄 append."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False)
    with open(filepath, "a", encoding="utf-8", errors="replace") as f:
        f.write(line + "\n")


def build_summary_entry(data: dict, entry_id: str, agent: str | None) -> dict:
    """세션 요약 JSONL 엔트리 구성."""
    summary = data.get("summary", {})
    return {
        "id": entry_id,
        "agent": agent,
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
        "timing": data.get("timing", None),
    }


def build_lesson_entry(data: dict, lesson: dict, entry_id: str, agent: str | None) -> dict:
    """Lesson-Learned JSONL 엔트리 구성."""
    return {
        "id": entry_id,
        "agent": agent,
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

    # 에이전트 식별
    agent = data.get("agent")
    if isinstance(agent, str):
        agent = agent.strip().lower() or None

    result = {"saved": {}, "counts": {}}

    # 경로 분기
    project_slug = sanitize_project_path(data["project"])
    today = data["date"][:10].replace("-", "")

    if agent:
        agent_wrapup_dir = AI_ROOT / "agents" / agent / "wrapup"
        summary_file = agent_wrapup_dir / "sessions" / f"{project_slug}.jsonl"
        ai_file = agent_wrapup_dir / "lessons.jsonl"
        summary_id_prefix = f"ws-{agent}-{today}"
        ai_id_prefix = f"ll-ai-{agent}-{today}"
    else:
        summary_file = SESSION_SUMMARIES_DIR / project_slug / "summaries.jsonl"
        ai_file = AI_LESSONS_DIR / "lessons.jsonl"
        summary_id_prefix = f"ws-{today}"
        ai_id_prefix = f"ll-ai-{today}"

    # User 학습은 항상 중앙
    user_file = USER_LESSONS_DIR / "lessons.jsonl"
    user_id_prefix = f"ll-user-{today}"

    # 1) 세션 요약 저장
    summary = data.get("summary")
    has_summary = summary and any(summary.get(k) for k in ["info", "qa", "conclusions", "done", "actions"])
    has_evaluation = data.get("evaluation") is not None
    if has_summary or has_evaluation:
        sid = get_next_id(summary_file, summary_id_prefix)
        entry = build_summary_entry(data, sid, agent)
        append_jsonl(summary_file, entry)
        result["saved"]["summary"] = str(summary_file)
        result["counts"]["summary"] = 1

    # 2) 사용자 Lesson-Learned 저장
    user_lessons = data.get("user_lessons", [])
    if user_lessons:
        for lesson in user_lessons:
            lid = get_next_id(user_file, user_id_prefix)
            entry = build_lesson_entry(data, lesson, lid, agent)
            append_jsonl(user_file, entry)
        result["saved"]["user_lessons"] = str(user_file)
        result["counts"]["user_lessons"] = len(user_lessons)

    # 3) AI Lesson-Learned 저장
    ai_lessons = data.get("ai_lessons", [])
    if ai_lessons:
        for lesson in ai_lessons:
            lid = get_next_id(ai_file, ai_id_prefix)
            entry = build_lesson_entry(data, lesson, lid, agent)
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
