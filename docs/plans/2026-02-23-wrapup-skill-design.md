# /wrapup Skill 설계 문서

> 작성일: 2026-02-23 | 상태: 승인됨

---

## 개요

세션 종료 시 사용자와 AI 각각의 "배운 것"을 구조화된 포맷으로 자동 기록하는 `/wrapup` 스킬.
2계층 구조 — 세션 요약(프로젝트 관리) + Lesson-Learned(지적 성장) — 를 한 번의 호출로 처리.

### 핵심 차별점 (vs Claude Diary)

- 사용자 학습 / AI 학습 명시 분리
- 결정사항 + 이유(rationale) 구조화
- JSONL로 맥락 보존 (CLAUDE.md 불릿 압축 X)
- 액션 아이템 → /atodo 연동
- 세션 요약과 Lesson-Learned를 별도 계층으로 분리

---

## 결정 사항

| 항목 | 결정 | 이유 |
|------|------|------|
| MVP 범위 | 2계층 모두 | 세션 요약과 Lesson-Learned 모두 첫 버전에서 구현 |
| 설계 접근법 | B: Skill + 헬퍼 스크립트 | 관심사 분리 (분석/UI vs 저장/검증) |
| 저장 포맷 | JSONL | 텍스트 기반 증분 기록 표준, git 호환, 향후 SQLite 이관 용이 |
| 세션 요약 저장 | `{project}/.claude/session-summaries/` | 프로젝트 종속적 데이터 |
| Lesson-Learned 저장 | 사용자: `Z:\_myself\lesson-learned\`, AI: `Z:\_ai\lesson-learned\` | 프로젝트 초월 범용 지식 |
| 트리거 | Skill만 (MVP) | Stop훅/SessionEnd훅은 향후 추가 |
| /atodo 연동 | 포함 | 세션 랩업→할 일 관리 자연스러운 연결 |
| 드래프트 UI | 통합 드래프트 | 2계층을 한 번에 보여주고 한 번에 확인 |

---

## 파일 구조

```
Z:\_ai\skills\wrapup\
├── SKILL.md                    ← 핵심: 분석 + 드래프트 + UI 로직
├── README.md
├── README_ko.md
├── CHANGELOG.md
├── LICENSE
├── scripts/
│   ├── save-wrapup.py          ← 세션 요약 + Lesson-Learned JSONL 저장
│   ├── read-stats.py           ← 기존 데이터 통계 조회 (누적 건수 등)
│   └── settings.py             ← 언어 설정 관리 (v1.1.0 추가)
├── references/
│   └── schema.md               ← JSONL 스키마 정의 + 예시
└── docs/
    ├── plans/
    │   └── 2026-02-23-wrapup-skill-design.md  ← 이 문서
    └── research/
        └── research-report-2026-02-23-lesson-learned-system-design.md
```

---

## JSONL 스키마

### 세션 요약 (`{project}/.claude/session-summaries/summaries.jsonl`)

```jsonl
{
  "id": "ws-20260223-001",
  "date": "2026-02-23T15:30:00",
  "session_id": "abc-123",
  "session_name": "lesson-learned 시스템 설계",
  "project": "z:/_ai/skills/lesson-learned",
  "info_summary": [
    "Claude Code 훅은 12~14개 라이프사이클 이벤트 지원",
    "Stop 훅 prompt 타입에 버그 존재"
  ],
  "qa_pairs": [
    {
      "q": "Skill과 Command 차이는?",
      "a": "둘 다 대화 컨텍스트 접근 가능. Skill은 AI 자동 추천 + 확장 구조 지원"
    }
  ],
  "conclusions": [
    {
      "topic": "저장 포맷",
      "decision": "JSONL",
      "rationale": "텍스트 기반 증분 기록 표준, git 호환"
    }
  ],
  "action_items": [
    {
      "title": "wrapup 스킬 MVP 개발",
      "priority": "high",
      "registered_todo": null
    }
  ]
}
```

### 사용자 Lesson-Learned (`Z:\_myself\lesson-learned\lessons.jsonl`)

```jsonl
{
  "id": "ll-user-20260223-001",
  "date": "2026-02-23T15:30:00",
  "session_id": "abc-123",
  "session_name": "lesson-learned 시스템 설계",
  "project": "z:/_ai/skills/lesson-learned",
  "type": "user_question_answer",
  "category": "system-design",
  "title": "JSONL이 append 기록에 최적인 이유",
  "summary": "텍스트 기반 포맷 중 증분 기록에 업계 표준",
  "context": "저장 포맷 비교 논의 중 발견",
  "detail_ref": "",
  "tags": ["format", "jsonl"]
}
```

### AI Lesson-Learned (`Z:\_ai\lesson-learned\lessons.jsonl`)

```jsonl
{
  "id": "ll-ai-20260223-001",
  "date": "2026-02-23T15:30:00",
  "session_id": "abc-123",
  "session_name": "lesson-learned 시스템 설계",
  "project": "z:/_ai/skills/lesson-learned",
  "type": "ai_trial_error",
  "category": "hook-development",
  "title": "prompt 타입 Stop 훅은 대화 컨텍스트 접근 불가",
  "summary": "prompt 타입은 메타데이터만 수신. command/agent 타입 사용 필요.",
  "context": "훅 시스템 조사 중 발견. Issue #11786 참조.",
  "detail_ref": "research/research-report-2026-02-23-lesson-learned-system-design.md",
  "tags": ["claude-code", "hooks"]
}
```

### 학습 유형 (type 필드)

**사용자 학습**:
- `user_question_answer`: 질문하고 답을 얻은 것
- `user_insight_feedback`: AI 제공 정보에 대한 긍정 피드백 ("이건 몰랐는데")
- `user_concept_exploration`: 개념적 이해 추구 ("왜?", "차이가?")

**AI 학습**:
- `ai_trial_error`: 시행착오를 통한 발견
- `ai_research_discovery`: 조사 과정에서의 새로운 발견
- `ai_strategy_pivot`: 전략 수정을 통한 해결

---

## SKILL.md 7단계 워크플로우

### Step 1: 세션 메타정보 수집

Bash 명령 병렬 실행:
- `date +"%Y-%m-%dT%H:%M:%S"` — 현재 시각
- `pwd` — 프로젝트 경로
- 세션ID/세션명 추출 (projects 디렉토리 JSONL 파싱)
- `python scripts/read-stats.py` — 기존 데이터 누적 통계

세션명 없으면 중단 + `/rename` 안내.

### Step 2: AI 대화 컨텍스트 분석 → 2계층 드래프트 생성

Skill이 전체 대화 컨텍스트에 접근하여 추출:

**계층 1 — 세션 요약:**
- A. 정보 요약: 세션에서 조사/파악된 핵심 정보 (불릿 포인트)
- B. Q&A 정리: 사용자 질문 + AI 답변 쌍
- C. 협의 결론: 토론/비교된 안건의 결론 + 이유
- D. 액션 아이템: 후속 할 일 목록

**계층 2 — Lesson-Learned:**
- E. 사용자 학습 탐지 신호: 질문→답변, "이건 몰랐는데" 피드백, 개념 탐색
- F. AI 학습 탐지 신호: 에러→수정 패턴, 새 정보 발견, 전략 수정

양쪽 모두 해당하면 양쪽 다 기록 (같은 내용이지만 관점이 다름).

### Step 3: 통합 드래프트 표시 + AskUserQuestion

2계층을 하나의 통합 드래프트로 표시. 선택지:
- "확인 - 이대로 기록"
- "수정 필요"
- "세션 요약만 기록"
- "Lesson-Learned만 기록"

### Step 4: 수정 루프

"수정 필요" 선택 시 자유 텍스트 수정 지시 → 반영 → Step 3 반복.

### Step 5: 저장

`python scripts/save-wrapup.py`를 stdin JSON으로 호출:
- 세션 요약 → `{project}/.claude/session-summaries/summaries.jsonl`
- 사용자 학습 → `Z:\_myself\lesson-learned\lessons.jsonl`
- AI 학습 → `Z:\_ai\lesson-learned\lessons.jsonl`

### Step 6: /atodo 연동 제안

액션 아이템 1건+ 시:
- "전부 등록" → 각 항목을 /atodo Skill 호출
- "선택해서 등록" → 개별 확인
- "나중에" → 건너뜀

### Step 7: 완료 메시지

저장 결과 + 누적 통계 표시.

---

## 헬퍼 스크립트

### `scripts/save-wrapup.py`

입력: stdin JSON
```json
{
  "session_id": "...",
  "session_name": "...",
  "project": "...",
  "date": "...",
  "summary": { "info": [], "qa": [], "conclusions": [], "actions": [] },
  "user_lessons": [ { "type": "...", "category": "...", "title": "...", ... } ],
  "ai_lessons": [ { "type": "...", "category": "...", "title": "...", ... } ]
}
```

처리:
1. 디렉토리 존재 확인 → 없으면 `os.makedirs`
2. 기존 JSONL에서 마지막 ID 읽어 다음 번호 할당
3. 3개 파일에 각각 append
4. stdout으로 결과 JSON 반환

### `scripts/read-stats.py`

3개 JSONL 파일 행 수를 세어 누적 통계 반환.

---

## 에러 핸들링

| 상황 | 처리 |
|------|------|
| 세션명 미설정 | Step 1 중단 + `/rename` 안내 |
| JSONL 파일 없음 (첫 실행) | 자동 생성 |
| 저장 실패 | 드래프트 텍스트 출력 → 수동 저장 가능 |
| 대화 컨텍스트 너무 짧음 | "추출할 학습 내용이 부족합니다" 안내 |
| /atodo Skill 호출 실패 | 액션 아이템 텍스트만 표시, 수동 등록 안내 |

---

## SKILL.md description

```
description: "세션 마무리, 세션 정리, 세션 래핑, 세션 요약, 배운 점 정리, lesson learned,
wrapup, 오늘 뭘 배웠지, 세션 회고, 작업 마무리 시 자동으로 추천됩니다."
```

---

## 향후 확장 (MVP 범위 외)

1. Stop 훅 힌트 — 세션 종료 감지 시 "/wrapup 하시겠습니까?" 제안
2. SessionEnd 훅 백업 — 미수행 시 경량 자동 요약
3. 중복 탐지 — 새 lesson이 기존 JSONL 항목과 유사한지 검색
4. JSONL → SQLite 인덱스 — 대량 축적 후 복합 검색
5. /reflect 기능 — 축적된 데이터에서 패턴 학습 (Claude Diary 방식 참조, 맥락 보존 개선)
6. JSONL → 마크다운 렌더링 — 읽기 좋은 리포트 생성
