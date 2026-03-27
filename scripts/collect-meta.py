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
        "timing": {
            "session_start":   "2026-03-09T14:00:00",
            "wrapup_start":    "2026-03-09T16:30:00",
            "segment_start":   "2026-03-09T14:00:00",
            "elapsed_minutes": 150,
            "is_continuation": false,
            "wrapup_number":   1
        },
        "stats": {
            "user_lessons":      {"total": N, "categories": {...}},
            "ai_lessons":        {"total": N, "categories": {...}},
            "session_summaries": {"total": N, "global_total": N, "total_elapsed_minutes": N, "file": "..."}
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
USER_LESSONS_FILE = Path(r"E:\0\_myself\lesson-learned\lessons.jsonl")
AI_LESSONS_FILE   = Path(r"E:\0\_ai\lesson-learned\lessons.jsonl")
SESSION_SUMMARIES_DIR = Path(r"E:\0\_ai\session-summaries")
AI_ROOT = Path(r"Z:\_ai")


# ── 시간 헬퍼 ─────────────────────────────────────────────
def _utc_to_local_naive(utc_str: str) -> datetime:
    """UTC ISO string (Z 또는 +00:00 접미사) → 로컬 naive datetime."""
    if utc_str.endswith("Z"):
        utc_str = utc_str[:-1] + "+00:00"
    utc_dt = datetime.fromisoformat(utc_str)
    local_dt = utc_dt.astimezone()
    return local_dt.replace(tzinfo=None)


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


def _scan_summaries(base_dir: Path) -> tuple[int, int, set]:
    """summaries 디렉토리를 스캔하여 (총 건수, 총 소요시간, 세션ID set) 반환."""
    total = 0
    elapsed = 0
    session_ids = set()
    if not base_dir.exists():
        return total, elapsed, session_ids
    for summary_dir in base_dir.iterdir():
        if not summary_dir.is_dir():
            continue
        sf = summary_dir / "summaries.jsonl"
        if not sf.exists():
            continue
        total, elapsed, session_ids = _scan_jsonl_summaries(sf, total, elapsed, session_ids)
    return total, elapsed, session_ids


def _scan_agent_wrapups(agents_dir: Path) -> tuple[int, int, set]:
    """모든 에이전트의 wrapup/sessions/ 를 스캔."""
    total = 0
    elapsed = 0
    session_ids = set()
    if not agents_dir.exists():
        return total, elapsed, session_ids
    for agent_dir in agents_dir.iterdir():
        if not agent_dir.is_dir():
            continue
        sessions_dir = agent_dir / "wrapup" / "sessions"
        if not sessions_dir.exists():
            continue
        for sf in sessions_dir.glob("*.jsonl"):
            total, elapsed, session_ids = _scan_jsonl_summaries(sf, total, elapsed, session_ids)
    return total, elapsed, session_ids


def _scan_jsonl_summaries(filepath: Path, total: int, elapsed: int, session_ids: set) -> tuple[int, int, set]:
    """단일 JSONL 파일에서 요약 통계를 누적."""
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
                    session_ids.add(sid)
                timing = entry.get("timing")
                if timing and isinstance(timing, dict):
                    elapsed += timing.get("elapsed_minutes", 0)
            except json.JSONDecodeError:
                continue
    return total, elapsed, session_ids


def collect_stats(project_path: str, agent: str | None = None) -> dict:
    project_slug = _sanitize_project_path(project_path)

    # 에이전트별 경로 결정
    if agent:
        agent_wrapup_dir = AI_ROOT / "agents" / agent / "wrapup"
        summary_file = agent_wrapup_dir / "sessions" / f"{project_slug}.jsonl"
        ai_lessons_file = agent_wrapup_dir / "lessons.jsonl"
    else:
        summary_file = SESSION_SUMMARIES_DIR / project_slug / "summaries.jsonl"
        ai_lessons_file = AI_LESSONS_FILE

    # 글로벌 통계: 기존 경로 + 모든 에이전트 폴더 합산
    g1_total, g1_elapsed, g1_sids = _scan_summaries(SESSION_SUMMARIES_DIR)
    g2_total, g2_elapsed, g2_sids = _scan_agent_wrapups(AI_ROOT / "agents")
    global_total = g1_total + g2_total
    total_elapsed = g1_elapsed + g2_elapsed
    unique_session_ids = g1_sids | g2_sids

    return {
        "user_lessons": {
            "total": _count_jsonl(USER_LESSONS_FILE),
            "categories": _get_categories(USER_LESSONS_FILE),
        },
        "ai_lessons": {
            "total": _count_jsonl(ai_lessons_file),
            "categories": _get_categories(ai_lessons_file),
        },
        "session_summaries": {
            "total": _count_jsonl(summary_file),
            "global_total": global_total,
            "unique_sessions": len(unique_session_ids),
            "total_elapsed_minutes": total_elapsed,
            "file": str(summary_file),
        },
    }


# ── 세션 정보 헬퍼 ────────────────────────────────────────
def _path_to_slug(path_str: str) -> str:
    """프로젝트 경로를 Claude Code의 slug 형식으로 변환.
    non-ASCII, 특수문자를 모두 개별 '-'로 치환 (축소 안 함 — Claude Code 동작 일치)."""
    s = path_str.replace("\\", "/").rstrip("/")
    s = re.sub(r"[^a-zA-Z0-9-]", "-", s)
    return s


def collect_session(project_path: str) -> dict:
    claude_projects = Path.home() / ".claude" / "projects"

    if not claude_projects.exists():
        return {"session_id": "", "session_name": "", "session_start": None,
                "error": "Claude projects directory not found"}

    # cwd와 상위 경로들에 대해 slug 매칭을 시도하고,
    # 모든 매칭 디렉토리에서 가장 최근 세션 파일을 선택한다.
    # (Claude Code는 CLAUDE.md 위치를 프로젝트 루트로 사용하므로 cwd와 다를 수 있음)
    path = Path(project_path)
    candidates = [path] + list(path.parents)
    all_matching_dirs = []

    for candidate in candidates:
        slug = _path_to_slug(str(candidate))
        for d in claude_projects.iterdir():
            if d.is_dir() and d.name == slug and d not in all_matching_dirs:
                all_matching_dirs.append(d)

    if not all_matching_dirs:
        return {"session_id": "", "session_name": "", "session_start": None,
                "error": f"No project directory for: {project_path}"}

    # 모든 매칭 디렉토리에서 JSONL 파일을 수집하고, 가장 최근 파일을 선택
    all_jsonl = []
    for d in all_matching_dirs:
        all_jsonl.extend(d.glob("*.jsonl"))
    all_jsonl.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    if not all_jsonl:
        return {"session_id": "", "session_name": "", "session_start": None,
                "error": "No session files found"}

    session_file = all_jsonl[0]
    session_id   = session_file.stem
    session_name = ""
    session_start = None

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 세션 시작 시각: 첫 20줄에서 가장 이른 timestamp 추출
        for line in lines[:20]:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entry = json.loads(stripped)
                ts = entry.get("timestamp")
                if not ts:
                    snapshot = entry.get("snapshot")
                    if isinstance(snapshot, dict):
                        ts = snapshot.get("timestamp")
                if ts:
                    if session_start is None or ts < session_start:
                        session_start = ts
            except json.JSONDecodeError:
                continue

        # 세션명: 마지막 custom-title 엔트리에서 추출
        for line in reversed(lines):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entry = json.loads(stripped)
                if entry.get("type") == "custom-title":
                    session_name = entry.get("customTitle", "")
                    break
            except json.JSONDecodeError:
                continue
    except Exception:
        pass

    return {"session_id": session_id, "session_name": session_name,
            "session_start": session_start}


# ── 시간 측정 ─────────────────────────────────────────────
def collect_timing(session_id: str, session_start_utc: str,
                   project_path: str, now: datetime,
                   agent: str | None = None) -> dict | None:
    """세션 시간 측정 데이터를 수집한다."""
    if not session_start_utc:
        return None

    session_start = _utc_to_local_naive(session_start_utc)

    # 같은 세션에서 직전 wrapup이 있는지 확인 (에이전트별 경로)
    project_slug = _sanitize_project_path(project_path)
    if agent:
        summary_file = AI_ROOT / "agents" / agent / "wrapup" / "sessions" / f"{project_slug}.jsonl"
    else:
        summary_file = SESSION_SUMMARIES_DIR / project_slug / "summaries.jsonl"

    prev_wrapup_dt = None
    wrapup_count = 0

    if summary_file.exists():
        with open(summary_file, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    entry = json.loads(stripped)
                    if entry.get("session_id") == session_id:
                        wrapup_count += 1
                        entry_date = entry.get("date", "")
                        if entry_date:
                            dt = datetime.fromisoformat(entry_date)
                            if prev_wrapup_dt is None or dt > prev_wrapup_dt:
                                prev_wrapup_dt = dt
                except json.JSONDecodeError:
                    continue

    is_continuation = prev_wrapup_dt is not None
    segment_start = prev_wrapup_dt if is_continuation else session_start

    elapsed = now - segment_start
    elapsed_minutes = max(0, int(elapsed.total_seconds() / 60))

    return {
        "session_start": session_start.strftime("%Y-%m-%dT%H:%M:%S"),
        "wrapup_start": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "segment_start": segment_start.strftime("%Y-%m-%dT%H:%M:%S"),
        "elapsed_minutes": elapsed_minutes,
        "is_continuation": is_continuation,
        "wrapup_number": wrapup_count + 1,
    }


# ── 메인 ─────────────────────────────────────────────────
def main():
    project_path = os.getcwd()
    now = datetime.now()

    # 에이전트 식별
    agent_raw = os.environ.get("CLAUDE_AGENT_NAME", "").strip().lower()
    agent = agent_raw if agent_raw else None

    session_info = collect_session(project_path)
    session_start_utc = session_info.pop("session_start", None)

    timing = collect_timing(
        session_info.get("session_id", ""),
        session_start_utc,
        project_path,
        now,
        agent=agent,
    )

    result = {
        "date":    now.strftime("%Y-%m-%dT%H:%M:%S"),
        "project": project_path,
        "agent":   agent,
        **session_info,
        "timing":  timing,
        "stats":   collect_stats(project_path, agent=agent),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
