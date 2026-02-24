# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
