#!/usr/bin/env python
"""
get-session.py - 현재 세션 ID와 세션명 추출

Usage:
    python get-session.py <project_path>

출력: JSON (stdout)
    {"session_id": "...", "session_name": "...", "project_dir": "...", "session_file": "..."}
"""

import io
import json
import sys
from pathlib import Path

# Windows에서 stdout을 UTF-8로 강제 설정
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"session_id": "", "session_name": "", "error": "project_path argument required"}))
        return

    project_path = sys.argv[1]
    last_component = Path(project_path).name

    claude_projects = Path.home() / ".claude" / "projects"
    if not claude_projects.exists():
        print(json.dumps({"session_id": "", "session_name": "", "error": "Claude projects directory not found"}))
        return

    # 마지막 경로 컴포넌트 이름이 포함된 디렉터리 검색 (최신 수정순)
    matching_dirs = sorted(
        [d for d in claude_projects.iterdir() if d.is_dir() and last_component.lower() in d.name.lower()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )

    if not matching_dirs:
        print(json.dumps({"session_id": "", "session_name": "", "error": f"No project directory for: {last_component}"}))
        return

    project_dir = matching_dirs[0]

    # 최신 JSONL 파일 선택
    jsonl_files = sorted(
        project_dir.glob("*.jsonl"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not jsonl_files:
        print(json.dumps({"session_id": "", "session_name": "", "error": "No session files found"}))
        return

    session_file = jsonl_files[0]
    session_id = session_file.stem

    # custom-title 마지막 항목에서 세션명 추출
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

    print(json.dumps({
        "session_id": session_id,
        "session_name": session_name,
        "project_dir": str(project_dir),
        "session_file": str(session_file),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
