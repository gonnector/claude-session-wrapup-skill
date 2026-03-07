[English](README.md) | [한국어](README_ko.md)

# /wrapup — Claude Code 세션 랩업 스킬

세션 종료 시 2계층 구조의 노트를 자동으로 기록하는 Claude Code 스킬:

- **계층 1 — 세션 요약**: 정보 요약, Q&A, 결정사항 + 이유(rationale), 작업 내역, 액션 아이템
- **계층 2 — Lesson-Learned**: 사용자가 배운 것, AI가 배운 것 (관점별 분리)
- **계층 3 — 세션 평가** (v1.4.0): AI 자기 진단 (5개 서브 메트릭) + 사용자 피드백 — 세션 품질 개선을 위한 메타-피드백 루프

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
| 6 | `Bash(python:*)` | `python -c "importlib..."` JSONL 저장 |

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

## 워크플로우 (10단계)

```
Step 0  언어 설정 확인 (최초 이후 무음)
Step 1  세션 메타정보 수집
Step 2  대화 분석 → 2계층 드래프트 생성 (auto memory 중복 확인 포함)
Step 3  드래프트 표시 + 확인 (AskUserQuestion)
Step 4  수정 루프 (변경 요청 시)
Step 5  세션 평가 — AI 자기 진단 + 사용자 피드백 (v1.4.0)
Step 6  JSONL 저장 (평가 데이터 포함)
Step 7  Auto Memory 동기화 — lesson을 auto memory로 승격 제안 (v1.3.0)
Step 8  액션 아이템 /atodo 등록 제안
Step 9  완료 메시지 + 평가 요약 + 누적 통계 표시
```

### 세션 평가 (v1.4.0)

세션의 **운영/흐름(process)** 자체에 대한 품질 평가를 AI와 사용자 양측에서 수행합니다:

- **AI 자기 진단**: 5개 서브 메트릭 (목표 달성, 소통 효율, 기술적 품질, 세션 흐름, 학습 가치) 각 1-5점 + 간단한 이유, 그리고 태그가 포함된 개선 사항 (반복 패턴 탐지용)
- **사용자 피드백**: 종합 점수 (1-5) + 좋았던 점/아쉬웠던 점/개선 사항 (각각 엔터로 스킵 가능)

AI가 먼저, 사용자가 나중에 평가합니다 — anchoring bias 방지.

> **정의**: "AI 만족도"는 감정적 만족이 아니라 **세션 품질에 대한 AI의 자기 진단(self-assessment)**을 의미합니다.

### Auto Memory 연동 (v1.3.0)

Claude Code의 [auto memory](https://docs.anthropic.com/en/docs/claude-code/memory) (`~/.claude/projects/{slug}/memory/`)에 이미 기록된 항목을 감지하여 lesson-learned에 중복 등록하지 않습니다. 겹치는 lesson은 `[📝 auto memory]` 태그를 붙이고 **맥락/발견 과정** 중심으로 경량화합니다.

저장 후, auto memory에 아직 없는 AI lesson 중 향후 세션에서 재활용할 만한 패턴/도구/발견은 auto memory로 **승격 등록**을 제안합니다.

---

## 레포 구조

```
wrapup/
├── SKILL.md                      ← 스킬 정의 (워크플로우 + 프롬프트)
├── scripts/
│   ├── save-wrapup.py            ← JSONL 저장 로직
│   ├── read-stats.py             ← 누적 통계 조회
│   ├── collect-meta.py           ← 세션 메타정보 수집
│   └── settings.py               ← 언어 설정 관리
├── references/
│   └── schema.md                 ← JSONL 스키마 정의
└── docs/
    ├── prd.md                    ← 제품 요구사항 정의서
    ├── plans/
    │   └── 2026-02-23-wrapup-skill-design.md
    └── research/
        └── research-report-2026-02-23-lesson-learned-system-design.md
```

---

## 라이선스

MIT © 2026 [Gonnector (고영혁)](https://github.com/gonnector)
