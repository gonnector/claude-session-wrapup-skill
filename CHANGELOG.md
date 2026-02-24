# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.2.10] - 2026-02-24

### Changed
- Step 3 draft: added blank line between each `▸` sub-heading and its first item for improved readability

---

## [1.2.9] - 2026-02-24

### Added
- `scripts/collect-meta.py`: single-call metadata collector combining `date`, `pwd`, `read-stats`, and `get-session` logic — returns unified JSON with all Step 1 fields

### Changed
- Step 1: replaced 4 separate bash calls with `python "$SKILL_DIR/scripts/collect-meta.py"` — zero bash-generated commands remain, eliminates risk of unexpected `head`/`tail`/`ls` usage

---

## [1.2.8] - 2026-02-24

### Changed
- Step 3 Lesson-Learned draft: replaced `**제목** · \`type\`` pattern with numbered list format
  ```
  N. 주제 내용 [학습분류]
     --> 내용 요약
  ```
  Consistent with Q&A / 협의 결론 style from v1.2.7

---

## [1.2.7] - 2026-02-24

### Changed
- Step 3 draft: Q&A and 협의 결론 switched from markdown table to numbered list format — `|` table alignment breaks in terminal monospace fonts with mixed CJK/Latin content
  - Q&A: `N. 질문\n   --> 답변` pattern
  - 협의 결론: `N. [주제] ...\n   [결정] ...\n   [이유] ...` pattern

---

## [1.2.6] - 2026-02-24

### Added
- `scripts/get-session.py`: Python script for extracting session ID and name from `~/.claude/projects/` — eliminates multi-line bash command substitution that triggered Claude Code's safety prompts

### Changed
- Step 1: replaced parallel-with-`$(pwd)` pattern with sequential `pwd` → parallel invocations, passing the path value directly; all bash calls are now single-line with no `$()` substitution

---

## [1.2.5] - 2026-02-24

### Added
- README / README_ko: "Permission Setup" section explaining that only `Bash(python:*)` needs explicit allow in `~/.claude/settings.json`; includes per-step tool breakdown with auto-approval notes

---

## [1.2.4] - 2026-02-24

### Changed
- Step 3 draft display: redesigned with Unicode visual hierarchy — `━` thick lines for major sections, `◆`/`◈` icons for summary/lesson-learned headers, `▸` for sub-sections, `•`/`✓`/`▶`/`▷`/`·` item markers by type and priority; no left/right vertical borders (CJK double-width alignment rule)

---

## [1.2.3] - 2026-02-24

### Changed
- Step 7 completion message: replaced full box borders with horizontal-line-only layout — removes left/right vertical borders that misalign with mixed Korean/English content (CJK characters are double-width), keeps inline `│` separators for same-line items

---

## [1.2.2] - 2026-02-24

### Changed
- Step 5 save method: replaced `subprocess.run` + `tempfile` + `os.unlink` with `importlib` direct module call — eliminates all remaining permission prompts (`subprocess` and file deletion were still triggering approval despite `Bash(python:*)` allow rule)
- `save-wrapup.py`: extracted core logic into `run(data: dict) -> dict` function, callable without subprocess

---

## [1.2.1] - 2026-02-24

### Changed
- Step 5 save method: replaced Write tool + `rm` with a single `Bash(python:*)` call that handles temp file creation and cleanup internally — eliminates all permission prompts during save

---

## [1.2.0] - 2026-02-24

### Added
- **`work_done` field** in session summary: records actual work performed during the session (implementations, file edits, bug fixes, tests, docs) — distinct from Q&A and discussions
- Ordered before `action_items` in both schema and draft display
- Backward compatible: existing records without this field treat it as `null`

---

## [1.1.1] - 2026-02-24

### Fixed
- Completion message language hint label now uses language-specific text (e.g. `Wrap-up Language:` for English, `랩업 언어:` for Korean) instead of hardcoded Korean label

---

## [1.1.0] - 2026-02-24

### Added
- **Multilingual support**: language auto-detection on first run, saved setting used silently thereafter
- `scripts/settings.py`: language settings manager (`read` / `detect` / `write`)
- Step 0 in workflow: language check before session metadata collection
- Language change via keyword trigger (`/wrapup 언어 변경`, `/wrapup change lang`, etc.)
- Language hint in Step 7 completion message footer (keyword shown in current language)
- Language hint mapping table in `SKILL.md` for AI reference
- `README.md` (English) and `README_ko.md` (Korean)
- `CHANGELOG.md`, `LICENSE`

### Changed
- Step 2 language rule: fixed "Korean only" → dynamic `{language_name}` from Step 0 setting
- `SKILL.md` workflow: 7 steps → 8 steps (Step 0 inserted)
- Folder structure: `research/` moved to `docs/research/`

---

## [1.0.1] - 2026-02-23

### Fixed
- Added key mapping table in `SKILL.md` Step 5 (draft terms → correct JSON keys)
- Added `--file` argument to `save-wrapup.py` (MSYS bash echo pipe causes surrogate encoding errors)
- Added `errors='replace'` to all file open calls (Unicode surrogate character fix)
- Unified session summary save path to `Z:\_ai\session-summaries\` (was per-project path)
- Changed shebang from `python3` to `python` (Windows compatibility)
- Fixed `SKILL.md` to use absolute `$SKILL_DIR` path (relative path resolution failure)

---

## [1.0.0] - 2026-02-23

### Added
- Initial implementation of `/wrapup` skill
- Two-layer structured logging: Session Summary (Layer 1) + Lesson-Learned (Layer 2)
- `SKILL.md`: 7-step workflow with AskUserQuestion-based review loop
- `scripts/save-wrapup.py`: JSONL save logic for summaries and lessons
- `scripts/read-stats.py`: cumulative stats reader
- `references/schema.md`: JSONL schema definitions with examples
- Session summary schema: `id`, `date`, `session_id`, `session_name`, `project`, `info_summary`, `qa_pairs`, `conclusions`, `action_items`
- Lesson-Learned schema: `type` (6 types across user/AI), `category`, `title`, `summary`, `context`, `tags`
- `/atodo` integration for action item registration
- JSONL format for git-friendly incremental records
