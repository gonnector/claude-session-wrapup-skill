[English](README.md) | [한국어](README_ko.md)

# /wrapup — Claude Code 세션 랩업 스킬

세션 종료 시 2계층 구조의 노트를 자동으로 기록하는 Claude Code 스킬:

- **계층 1 — 세션 요약**: 정보 요약, Q&A, 결정사항 + 이유(rationale), 작업 내역, 액션 아이템
- **계층 2 — Lesson-Learned**: 사용자가 배운 것, AI가 배운 것 (관점별 분리)

기록은 JSONL 포맷으로 저장됩니다 — git 친화적, 증분 추가, 쿼리 가능.

---

## 요구사항

- [Claude Code](https://claude.ai/claude-code) CLI
- Python 3.x

---

## Permission 설정

**전역** Claude Code 설정 파일(`~/.claude/settings.json`)에 아래 내용을 추가하면 스킬 실행 중 승인 프롬프트 없이 자동으로 진행됩니다:

```json
{
  "permissions": {
    "allow": [
      "Bash(python:*)"
    ]
  }
}
```

### `python`만 등록하면 되는 이유

스킬은 Step 0·1·5에서 Python 스크립트를 총 4회 호출합니다. 그 외 사용되는 도구들(`Read`, `Glob`, `Bash(date:*)`, `Bash(pwd:*)`)은 파괴적이지 않은 읽기 전용 또는 단순 명령어로, Claude Code 기본 모드에서 자동 승인됩니다.

| Step | 도구 | 명령 |
|------|------|------|
| 0 | `Bash(python:*)` | `settings.py read / detect / write` |
| 1 | `Bash(date:*)` | 현재 시각 수집 — 자동 승인 |
| 1 | `Bash(pwd:*)` | 프로젝트 경로 수집 — 자동 승인 |
| 1 | `Bash(python:*)` | `read-stats.py` 실행 |
| 1 | `Read` / `Glob` | `~/.claude/projects/` 세션 파일 탐색 — 자동 승인 |
| 5 | `Bash(python:*)` | `python -c "importlib..."` JSONL 저장 |

> **프로젝트별 vs 전역:** 스킬 레포의 `.claude/settings.local.json`은 개발용 파일입니다. 모든 프로젝트에서 스킬이 동작하려면 `~/.claude/settings.json`(전역)에 `Bash(python:*)`를 추가하세요.

---

## 설치

```bash
# 스킬을 Claude Code 스킬 탐색 경로에 심볼릭 링크로 연결
ln -s /path/to/wrapup ~/.claude/skills/wrapup
```

링크 연결 후 Claude Code가 세션 종료 시 `/wrapup`을 자동으로 추천합니다.

---

## 사용법

### 일반 랩업
세션 랩업 시작 (Claude가 드래프트를 보여주고 확인 후 저장):
```
/wrapup
```

### 언어 변경
```
/wrapup 언어 변경
```

---

## 언어 설정

최초 실행 시 시스템 언어를 감지하여 한 번만 확인합니다.
이후 실행에서는 저장된 설정을 조용히 사용합니다.

언어를 변경하려면 스킬 호출 시 변경 키워드를 함께 입력하세요.
키워드는 완료 메시지 하단에 현재 설정 언어로 표시됩니다:

```
랩업 언어: 한국어 | 변경: /wrapup 언어 변경
```

**지원 언어:** 한국어, English, 日本語, 中文(简体), 그 외 직접 입력 가능.

설정 파일 위치: `~/.claude/skill-settings/wrapup/settings.json`

---

## 출력 파일

| 데이터 | 경로 |
|--------|------|
| 세션 요약 | `Z:\_ai\session-summaries\{project-slug}\summaries.jsonl` |
| 사용자 학습 | `Z:\_myself\lesson-learned\lessons.jsonl` |
| AI 학습 | `Z:\_ai\lesson-learned\lessons.jsonl` |

> 경로는 `scripts/save-wrapup.py`에서 수정할 수 있습니다.

---

## 워크플로우 (8단계)

```
Step 0  언어 설정 확인 (최초 이후 무음)
Step 1  세션 메타정보 수집
Step 2  대화 분석 → 2계층 드래프트 생성
Step 3  드래프트 표시 + 확인 (AskUserQuestion)
Step 4  수정 루프 (변경 요청 시)
Step 5  JSONL 저장
Step 6  액션 아이템 /atodo 등록 제안
Step 7  완료 메시지 + 누적 통계 표시
```

---

## 레포 구조

```
wrapup/
├── SKILL.md                      ← 스킬 정의 (워크플로우 + 프롬프트)
├── scripts/
│   ├── save-wrapup.py            ← JSONL 저장 로직
│   ├── read-stats.py             ← 누적 통계 조회
│   └── settings.py               ← 언어 설정 관리
├── references/
│   └── schema.md                 ← JSONL 스키마 정의
└── docs/
    ├── plans/
    │   └── 2026-02-23-wrapup-skill-design.md
    └── research/
        └── research-report-2026-02-23-lesson-learned-system-design.md
```

---

## 라이선스

MIT © 2026 [Gonnector (고영혁)](https://github.com/gonnector)
