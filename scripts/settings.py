#!/usr/bin/env python
"""
settings.py - wrapup 스킬 언어 설정 관리

Usage:
    python settings.py read                            # 현재 설정 출력
    python settings.py detect                          # 시스템 언어 감지
    python settings.py write --lang ko --name "한국어"  # 설정 저장
"""

import argparse
import io
import json
import locale
import os
import sys
from pathlib import Path

# Windows stdout UTF-8 강제
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SETTINGS_FILE = Path.home() / ".claude" / "skill-settings" / "wrapup" / "settings.json"

# 지원 언어: code → (name, change_hint)
SUPPORTED_LANGUAGES = {
    "ko":    ("한국어",      "/wrapup 언어 변경"),
    "en":    ("English",    "/wrapup change lang"),
    "ja":    ("日本語",      "/wrapup 言語変更"),
    "zh-cn": ("中文(简体)",  "/wrapup 切换语言"),
    "zh":    ("中文(简体)",  "/wrapup 切换语言"),
    "de":    ("Deutsch",    "/wrapup change lang"),
    "fr":    ("Français",   "/wrapup change lang"),
    "es":    ("Español",    "/wrapup change lang"),
}


def read_settings() -> dict:
    if not SETTINGS_FILE.exists():
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def detect_system_language() -> dict:
    """시스템 언어를 감지하여 {lang, name, change_hint} 반환."""
    code = None

    # 1순위: 환경변수
    for env_var in ("LANG", "LANGUAGE", "LC_ALL", "LC_MESSAGES"):
        val = os.environ.get(env_var, "")
        if val:
            code = val.split(".")[0].split("_")[0].lower()
            break

    # 2순위: Python locale
    if not code:
        try:
            loc = locale.getdefaultlocale()[0] or ""
            code = loc.split("_")[0].lower() if loc else ""
        except Exception:
            code = ""

    # 3순위: Windows 코드페이지 기반 추정
    if not code:
        try:
            import ctypes
            lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            # 한국어: 0x0412, 일본어: 0x0411, 중국어 간체: 0x0804
            lcid_map = {0x0412: "ko", 0x0411: "ja", 0x0804: "zh", 0x0409: "en"}
            code = lcid_map.get(lcid, "en")
        except Exception:
            code = "en"

    name, hint = SUPPORTED_LANGUAGES.get(code, ("English", "/wrapup change lang"))
    return {"lang": code, "name": name, "change_hint": hint}


def write_settings(lang: str, name: str) -> None:
    _, hint = SUPPORTED_LANGUAGES.get(lang, ("", "/wrapup change lang"))
    settings = {
        "language": lang,
        "language_name": name,
        "change_hint": hint,
        "initialized": True,
    }
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    print(json.dumps({"saved": str(SETTINGS_FILE), "settings": settings}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="wrapup 언어 설정 관리")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("read")
    subparsers.add_parser("detect")

    write_p = subparsers.add_parser("write")
    write_p.add_argument("--lang", required=True, help="언어 코드 (ko, en, ja, zh-cn, ...)")
    write_p.add_argument("--name", required=True, help="언어 표시명")

    args = parser.parse_args()

    if args.command == "read":
        print(json.dumps(read_settings(), ensure_ascii=False))
    elif args.command == "detect":
        print(json.dumps(detect_system_language(), ensure_ascii=False))
    elif args.command == "write":
        write_settings(args.lang, args.name)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
