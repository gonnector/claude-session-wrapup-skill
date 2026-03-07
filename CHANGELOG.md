# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.4.2] - 2026-03-07

### Changed
- 사용자 평가 텍스트 피드백 스킵 UX 개선 — "없으면 스킵" → "없으면 엔터"
  - 빈 입력(엔터만)이 기본 스킵 방식, "스킵"/"없음" 텍스트 입력도 호환 유지

---

## [1.4.1] - 2026-03-03

### Fixed
- 협의 결론 항목 제목 포맷 개선: `[주제] 내용` → `주제어 — 부연설명` 형식으로 변경
  - `[주제]` 태그 반복 제거, `[대괄호 감싸기]` 금지 규칙 추가
  - 부연설명이 불필요한 경우 `주제어`만 표기 허용
  - 금지 예시에 기존 패턴 2종 추가 (태그 반복, 대괄호 감싸기)
- 세션 평가 UI 개선
  - **5c 종합 점수**: AskUserQuestion → 텍스트 기반 번호 입력으로 변경 (AskUserQuestion 옵션 4개 제한으로 5점 척도 표현 불가)
  - **5c**: 점수별 부연 설명 삭제, "1 매우 불만족" 옵션 추가 (5→4→3→2→1 완전한 5점 척도)
  - **5d 텍스트 피드백**: AskUserQuestion → 텍스트 기반으로 변경 (AskUserQuestion "직접 입력" 옵션 선택 시 텍스트 필드 포커스 이동 불가 문제)

---

## [1.4.0] - 2026-03-02

### Added
- **세션 평가 기능**: 세션의 운영/흐름(process)에 대한 AI + 사용자 양측 품질 평가
  - **AI 자기 진단**: 5개 서브 메트릭 (목표 달성, 소통 효율, 기술적 품질, 세션 흐름, 학습 가치) 각 1-5점 + 한 줄 이유
  - **AI 개선 사항**: 태그(`tag`) 포함 구조화된 improvement — 반복 탐지용 매칭 키
  - **사용자 피드백**: 종합 점수 (1-5) + 좋았던 점/아쉬웠던 점/개선 사항 (각각 스킵 가능)
  - AI 먼저, 사용자 나중에 평가 (anchoring bias 방지)
  - "AI 만족도 = 세션 품질에 대한 AI의 자기 진단" 정의 명시
- **`evaluation` 필드**: 세션 요약 스키마에 추가 — `ai.sub_scores` (각 score+reason) + `ai.improvements` (tag+text) + `user.score/good_points/bad_points/improvements`
- **`docs/prd.md`**: 제품 요구사항 정의서 신규 생성 — 전체 기능 명세, 데이터 스키마, 워크플로우, Improvement Lifecycle 설계

### Changed
- 워크플로우: 9단계 → 10단계 (기존 Step 5-8 → Step 6-9, 새 Step 5: 세션 평가)
- `save-wrapup.py`: `build_summary_entry()`에 `evaluation` 필드 추가, 저장 조건에 evaluation 데이터 존재 여부 추가
- Step 9 완료 메시지: 평가 요약 (AI 서브 메트릭 별 + 사용자 점수) 표시 추가

---

## [1.3.0] - 2026-03-01

### Added
- **Auto Memory 연동**: Claude Code auto memory 기능과의 중복 방지 및 양방향 동기화 지원
  - Step 2: 드래프트 생성 전 auto memory 디렉토리(`~/.claude/projects/{slug}/memory/`) 스캔, 이미 기록된 사실은 `[📝 auto memory]` 태그로 중복 표시
  - Step 6 (신규): Auto Memory 동기화 제안 — AI lesson 중 auto memory에 없는 패턴을 승격 등록 제안, 이미 기록된 항목은 경량화 안내
  - Step 8 완료 메시지: auto memory 승격 건수 표시
- **`memory_ref` 필드**: Lesson-Learned 스키마에 nullable string 필드 추가 — auto memory 파일 참조 (예: `"research-sources.md"`)
  - `references/schema.md`: 필드 정의 및 하위 호환성 설명 추가
  - `scripts/save-wrapup.py`: `build_lesson_entry()`에서 `memory_ref` 처리

### Changed
- 워크플로우: 8단계 → 9단계 (기존 Step 6 /atodo → Step 7, Step 7 완료 → Step 8)

---

## [1.2.22] - 2026-02-28

### Fixed
- Step 3 드래프트 포맷: 화살표 기호(`-->`, `▶`) → 중첩 불릿(`   - `) 으로 변경
  - 기존 방식(`     ▶ 내용`)이 마크다운 렌더러에서 leading space가 strip되는 문제 해결
  - Q&A 답변, 협의 결론 `[결정]`/`[이유]`, 사용자 학습, AI 학습 4개 섹션 모두 적용
  - 자가 검증 규칙도 중첩 불릿 형식 확인으로 업데이트
  - 화살표 기호(`▶`, `-->`, `→`) 사용 금지 명시

---

## [1.2.21] - 2026-02-26

### Fixed
- Step 3 들여쓰기 규칙 강화: `-->`, `[결정]`, `[이유]` 줄의 5칸 들여쓰기 미준수 방지
  - 규칙에 각 태그별 패턴 명시 (`-->`, `[결정]`, `[이유]` 모두 5칸 적용)
  - 포맷 예시에 ✅ 올바른 예 주석 + ❌ 틀린 예(0칸) 추가
  - Q&A, 협의 결론, 사용자 학습, AI 학습 4개 섹션 모두 적용

---

## [1.2.20] - 2026-02-26

### Fixed
- Windows 환경에서 Python stdout 인코딩이 `cp949`일 때 한글이 `?????`로 출력되는 버그 수정
  - `scripts/settings.py`: UTF-8 stdout 강제 패치 추가
  - `scripts/read-stats.py`: UTF-8 stdout 강제 패치 추가
  - `scripts/save-wrapup.py`: UTF-8 stdout + stdin 강제 패치 추가

---

## [1.2.19] - 2026-02-24

### Changed
- Step 2 Lesson-Learned 탐지 로직 전면 개편 (리서치 기반):
  - `user_question_answer` → `user_fact_question` (What/Who/When/Where 사실형)
  - `user_concept_exploration` → `user_concept_question` (Why/How/비교/분석 개념형)
  - `user_insight_feedback` 탐지 신호 4계층으로 확장 — "새로 알게 됐다/깨달았다"(확실), -군/-네+후속발화(약한 신호), "그래서 ~이었구나"(통합 재구성)
  - `user_perspective_shift` 신규 추가 — 기존 관점/전제 재구조화 ("이렇게 생각하면 안 되겠다")
  - `ai_user_guided` 신규 추가 — 사용자→AI 지식 전달 (명시적 교정, 도메인 주입, 가이드라인, 방식 교정)
- `references/schema.md` 학습 유형 목록 및 예시 JSON 동기화

### Added
- `docs/research/research-report-2026-02-24-knowledge-acquisition-patterns.md`: 지식 획득 패턴 분류 체계 리서치 레포트 (팩트체크 + 자체 비평 완료)

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
