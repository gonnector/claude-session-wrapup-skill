# /wrapup — Product Requirements Document

> Version: 1.4.0-draft | Last Updated: 2026-03-02

---

## 1. 개요

### 1.1 제품 정의

Claude Code 세션 종료 시 **2계층 구조화 기록**(세션 요약 + Lesson-Learned)과 **세션 평가**를 한 번의 호출로 처리하는 스킬.

### 1.2 핵심 가치

- **지적 성장 추적**: 사용자와 AI 각각이 세션에서 무엇을 배웠는지 구분하여 기록
- **프로젝트 관리**: 세션별 핵심 정보, Q&A, 결정사항, 작업 내역, 액션 아이템 구조화
- **세션 품질 개선**: AI 자기 진단 + 사용자 피드백의 이중 평가로 세션 운영의 메타-피드백 루프 형성
- **데이터 축적**: JSONL 기반 증분 기록으로 향후 분석·패턴 발견·시각화 가능

### 1.3 주요 차별점 (vs 기존 도구)

| 차별점 | 설명 |
|--------|------|
| 학습 관점 분리 | 사용자 학습 / AI 학습을 명시적으로 구분 (기존 도구는 혼합) |
| 결정사항 + 근거 | `decision + rationale` 구조화 (회의록 베스트 프랙티스 적용) |
| JSONL 맥락 보존 | CLAUDE.md 불릿 압축 대비 전체 맥락 유지 |
| 세션 이중 평가 | AI 자기 진단 + 사용자 평가의 상호보완적 피드백 |
| Auto Memory 연동 | 중복 방지 + 양방향 동기화 |
| /atodo 연동 | 액션 아이템 → 할 일 관리 자연스러운 연결 |

---

## 2. 아키텍처

### 2.1 파일 구조

```
Z:\_ai\skills\wrapup\
├── SKILL.md                    ← 실행 워크플로우 (AI가 따르는 단계별 지시)
├── README.md / README_ko.md    ← 사용자 문서
├── CHANGELOG.md                ← 버전별 변경 이력
├── LICENSE                     ← MIT © 2026 Gonnector
├── scripts/
│   ├── save-wrapup.py          ← JSONL 저장 로직
│   ├── read-stats.py           ← 누적 통계 조회
│   ├── collect-meta.py         ← 세션 메타정보 수집
│   └── settings.py             ← 언어 설정 관리
├── references/
│   └── schema.md               ← JSONL 스키마 정의 + 예시
└── docs/
    ├── prd.md                  ← 이 문서
    ├── plans/
    │   └── 2026-02-23-wrapup-skill-design.md  ← 초기 설계 결정 로그
    └── research/
        ├── ...lesson-learned-system-design.md  ← 시스템 설계 리서치
        └── ...knowledge-acquisition-patterns.md ← 학습 패턴 분류 리서치
```

### 2.2 저장소 경로

| 데이터 | 경로 | 성격 |
|--------|------|------|
| 세션 요약 | `Z:\_ai\session-summaries\{project-slug}\summaries.jsonl` | 프로젝트별 |
| 사용자 학습 | `Z:\_myself\lesson-learned\lessons.jsonl` | 프로젝트 초월 |
| AI 학습 | `Z:\_ai\lesson-learned\lessons.jsonl` | 프로젝트 초월 |

`{project-slug}`: 프로젝트 경로에서 `\`, `/`, `:`를 `-`로 치환한 값.

### 2.3 데이터 흐름

```
세션 대화 → [Step 2: AI 분석] → 2계층 드래프트
                                    ↓
                             [Step 3-4: 확인/수정]
                                    ↓
                             [Step 5: 세션 평가]
                                    ↓
                             [Step 6: JSONL 저장] → 3개 파일
                                    ↓
                             [Step 7: Auto Memory 동기화]
                                    ↓
                             [Step 8: /atodo 연동]
                                    ↓
                             [Step 9: 완료 메시지]
```

---

## 3. 기능 명세

### 3.1 2계층 구조화 기록

**계층 1 — 세션 요약 (프로젝트 관리)**

| 항목 | 설명 |
|------|------|
| 정보 요약 | 세션에서 조사/파악된 핵심 정보 (불릿 포인트) |
| Q&A 정리 | 사용자 질문 + AI 답변 쌍 |
| 협의 결론 | 토론된 안건의 결론 + 근거(rationale) |
| 작업 내역 | 실제 수행한 작업 (구현, 수정, 테스트, 문서 등) |
| 액션 아이템 | 후속 할 일 (priority: high/medium/low) |

**계층 2 — Lesson-Learned (지적 성장)**

사용자와 AI 각각의 학습을 명시적으로 분리하여 기록.
학습 유형 분류 체계는 §4.3 참조.

### 3.2 세션 평가 (v1.4.0)

> **정의**: 세션 평가란 세션의 **주제(content)**가 아니라 세션의 **운영과 흐름(process)** 자체에 대한 품질 평가이다.

#### AI 만족도 (세션 품질에 대한 AI의 자기 진단)

AI는 감정적 만족을 느끼지 않는다. 여기서 "AI 만족도"는 **세션 품질에 대한 AI의 자기 진단(self-assessment)** 을 의미한다. AI가 스스로 세션을 돌아보며 "효율적으로 도움을 주었는가?"를 객관적 시그널 기반으로 평가하는 것이다.

**서브 메트릭 (각 1-5점):**

| 메트릭 | 평가 기준 | 높은 점수 (5) | 낮은 점수 (1) |
|--------|-----------|---------------|---------------|
| 목표 달성 | 사용자 요청의 완수도 | 모든 요청 완수 | 미완 작업, 중단된 시도 다수 |
| 소통 효율 | 의도 파악 속도, 오해 빈도 | 한 번에 이해, 최소 clarification | 잦은 오해, 반복 설명 |
| 기술적 품질 | 코드/출력물 정확도 | 첫 시도에 동작, 깔끔한 결과 | 여러 번 수정, 버그 발생 |
| 세션 흐름 | 진행의 매끄러움 | 순차적 진행, 막힘 없음 | 삽질, 우회, 데드엔드 |
| 학습 가치 | 의미 있는 학습 도출 여부 | 양측 모두 의미 있는 lesson | 기계적 작업만, 배움 없음 |

서브 메트릭 5개가 곧 AI 평가 자체이며, 별도의 종합 점수(overall_score)는 없다. 각 서브 메트릭에 점수(1-5)와 간단한 이유를 함께 기록한다.

**개선 사항(improvements)**: 서브 메트릭 분석을 종합하여 도출한 구체적 개선 포인트. 각 개선점에는 정규화된 `tag`를 부여하여 향후 반복 탐지에 활용한다.

#### 사용자 평가

**종합 점수**: 1-5점 (필수, AskUserQuestion 단일 선택)

**텍스트 피드백**: 점수와 무관하게 좋았던 점, 아쉬웠던 점, 개선 사항을 각각 질문. 각 항목은 스킵 가능.
- "좋았던 점이 있다면?" → 자유 텍스트 또는 스킵
- "아쉬웠던 점이 있다면?" → 자유 텍스트 또는 스킵
- "개선 사항이 있다면?" → 자유 텍스트 또는 스킵

#### 평가 순서

**AI가 먼저 평가 → 사용자가 후에 평가**

이유: 사용자가 먼저 평가하면 AI가 사용자 기대에 맞추려는 경향이 생길 수 있다. AI가 먼저 솔직하게 자기 진단을 제시하면:
- 사용자가 미처 인식하지 못한 관점을 환기
- AI의 자기 인식이 정확한지 사용자가 교정 가능
- 양쪽의 독립적 평가로 보다 풍부한 피드백

#### 드래프트 표시 형식 (화면)

AI 서브 메트릭은 시각적 별(★/☆) 형태로 표시하되, JSONL에는 1-5 정수로 저장:

```
▸ AI 만족도 (세션 품질에 대한 AI의 자기 진단)
────────────────────────────────────────────────────────────────────────────────────────

  목표 달성     ★★★★★  5/5  사용자 요청 모두 완수
  소통 효율     ★★★★☆  4/5  1회 clarification으로 의도 파악
  기술적 품질   ★★★☆☆  3/5  2번의 수정 필요
  세션 흐름     ★★★☆☆  3/5  중간에 방향 전환 1회
  학습 가치     ★★★★☆  4/5  양측 모두 의미 있는 lesson 도출

  개선 사항
  • [technical-verification] 코드 제시 전 검증 단계 추가 필요
  • [scope-management] 요청 범위 내에서 작업 집중
```

### 3.3 다국어 지원

지원 언어: ko, en, ja, zh-cn, de, fr, es
- 최초 실행 시 시스템 언어 자동 감지 → 사용자 확인
- 설정 저장 후 이후 세션에서 무음 적용
- 키워드로 언어 변경 가능 (`/wrapup 언어 변경`)

### 3.4 Auto Memory 연동 (v1.3.0)

- **Lesson → Auto Memory**: 새 AI lesson 중 auto memory에 없는 항목을 승격 등록 제안
- **Auto Memory → Lesson**: 이미 기록된 사실은 `[📝 auto memory]` 태그로 중복 표시, lesson은 맥락 중심으로 경량화
- `memory_ref` 필드로 auto memory 파일 참조 추적

### 3.5 /atodo 연동

액션 아이템이 있으면 `/atodo` 스킬로 할 일 등록을 제안.
전부 등록 / 선택 등록 / 나중에 3가지 옵션.

### 3.6 Improvement Lifecycle — 졸업 시스템 (v1.4.1+)

AI 개선점이 반복 발생하는 것을 탐지하고, 심각도에 따라 auto memory에 자동 승격하는 시스템.

#### 졸업 단계

```
[1회 발생] JSONL에만 기록 — 일회성일 수 있음
     ↓ (같은 tag 재발생)
[2회 발생] memory/session-quality.md 토픽 파일에 등록 (Watch)
     ↓ (또 재발생)
[3회 이상] MEMORY.md "Active Improvements" 섹션으로 승격 (매 세션 자동 로드)
     ↓ (5회 연속 미발생)
[해결됨] MEMORY.md에서 제거, 토픽 파일에 "Resolved" 표시
```

#### 매칭 키

AI improvement의 `tag` 필드 (kebab-case)로 매칭. 같은 tag = 같은 유형의 개선점.

#### Auto Memory 구조

**MEMORY.md** (최소한으로, 3-5줄):
```markdown
## Session Quality — Active Improvements
- **technical-verification** (4회): 코드 제시 전 검증 단계 필수
- **assumption-avoidance** (3회): 가정 대신 질문으로 시작
상세: [session-quality.md](session-quality.md)
```

**memory/session-quality.md** (상세 추적):
```markdown
# Session Quality Improvements
## Active (MEMORY.md에 승격됨)
| tag | count | last_seen | description |
|-----|-------|-----------|-------------|
| technical-verification | 4 | 2026-03-02 | 코드 제시 전 검증 단계 필수 |

## Watch (2회 — 재발 시 승격)
| tag | count | last_seen | description |
|-----|-------|-----------|-------------|
| scope-creep | 2 | 2026-02-28 | 요청 범위 외 작업 자제 |

## Resolved (5회 연속 미발생)
| tag | resolved_date | peak_count | description |
|-----|---------------|------------|-------------|
| path-separator | 2026-02-28 | 3 | Windows 경로 구분자 통일 |
```

#### 프루닝 규칙

Active 항목이 15개를 초과하면, count가 가장 낮은 항목부터 Watch로 강등.
MEMORY.md에는 상위 10개만 유지.

#### 반복 탐지 표시

Step 5에서 AI 개선점 생성 시, 기존 JSONL에서 같은 tag를 발견하면:

```
  개선 사항
  • [technical-verification] 코드 제시 전 검증 단계 추가 필요
    ⚠️ 반복 발생 (4회째) — 이전: 2026-03-01, 2026-02-28, 2026-02-25
  • [error-context] 에러 메시지 해석 시 원문 포함
    (신규)
```

#### 구현 일정

- **v1.4.0**: improvement에 tag 필드 포함 (스키마 준비)
- **v1.4.1**: 반복 탐지 + 졸업 시스템 + auto memory 관리
- **v1.5.0**: 자동 해결 판정 + 프루닝 + 트렌드 리포트

---

## 4. 데이터 스키마

### 4.1 세션 요약 (summaries.jsonl)

```jsonl
{
  "id": "ws-20260302-001",
  "date": "2026-03-02T15:30:00",
  "session_id": "abc-123",
  "session_name": "wrapup 스킬에 세션 평가 기능 추가",
  "project": "z:/_ai/skills/wrapup",
  "info_summary": ["핵심 정보 1", "핵심 정보 2"],
  "qa_pairs": [
    { "q": "질문", "a": "답변" }
  ],
  "conclusions": [
    { "topic": "안건명", "decision": "결정사항", "rationale": "이유" }
  ],
  "work_done": ["구현: ...", "수정: ..."],
  "action_items": [
    { "title": "할 일", "priority": "high", "registered_todo": null }
  ],
  "evaluation": {
    "ai": {
      "sub_scores": {
        "goal_achievement": { "score": 5, "reason": "사용자 요청 모두 완수" },
        "communication_efficiency": { "score": 4, "reason": "1회 clarification으로 의도 파악" },
        "technical_quality": { "score": 3, "reason": "2번의 수정 필요" },
        "session_flow": { "score": 3, "reason": "중간에 방향 전환 1회" },
        "learning_value": { "score": 4, "reason": "양측 모두 의미 있는 lesson 도출" }
      },
      "improvements": [
        { "tag": "technical-verification", "text": "코드 제시 전 검증 단계 추가 필요" },
        { "tag": "scope-management", "text": "요청 범위 내에서 작업 집중" }
      ]
    },
    "user": {
      "score": 5,
      "good_points": ["AI의 자기 진단이 흥미로웠음"],
      "bad_points": [],
      "improvements": ["평가 항목 세분화 검토"]
    }
  }
}
```

#### evaluation 필드 상세

**ai 객체:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `sub_scores` | object | 5개 서브 메트릭 |
| `sub_scores.{metric}` | object | `{ "score": integer(1-5), "reason": string }` |
| `sub_scores.goal_achievement` | object | 목표 달성도 |
| `sub_scores.communication_efficiency` | object | 소통 효율성 |
| `sub_scores.technical_quality` | object | 기술적 품질 |
| `sub_scores.session_flow` | object | 세션 흐름 매끄러움 |
| `sub_scores.learning_value` | object | 학습 가치 |
| `improvements` | array | `[{ "tag": string, "text": string }]` — 개선 사항 (0개 이상) |

`tag`: 정규화된 kebab-case 식별자 (예: `technical-verification`). 반복 탐지 및 졸업 시스템(§3.6)에서 매칭 키로 사용.

**user 객체:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `score` | integer (1-5) | 사용자 종합 만족도 |
| `good_points` | string[] | 좋았던 점 (0개 이상, 스킵 시 빈 배열) |
| `bad_points` | string[] | 아쉬웠던 점 (0개 이상, 스킵 시 빈 배열) |
| `improvements` | string[] | 개선 사항 (0개 이상, 스킵 시 빈 배열) |

#### 하위 호환성

`evaluation`은 v1.4.0에서 추가된 필드. 이전 레코드에는 해당 필드가 없으며, 없는 경우 `null`로 간주한다.

#### 점수 척도 정의

| 점수 | 라벨 | 의미 |
|------|------|------|
| 5 | 매우 만족 | 흠잡을 데 없이 원활한 세션 |
| 4 | 만족 | 전반적으로 좋았으나 소소한 아쉬움 |
| 3 | 보통 | 괜찮았으나 개선 여지가 뚜렷함 |
| 2 | 불만족 | 상당한 비효율이나 문제가 있었음 |
| 1 | 매우 불만족 | 목표 달성 실패 또는 심각한 문제 |

### 4.2 Lesson-Learned (lessons.jsonl)

```jsonl
{
  "id": "ll-user-20260302-001",
  "date": "2026-03-02T15:30:00",
  "session_id": "abc-123",
  "session_name": "세션 이름",
  "project": "z:/_ai/skills/wrapup",
  "type": "user_fact_question",
  "category": "system-design",
  "title": "학습 제목",
  "summary": "한 줄 요약",
  "context": "발견 맥락",
  "detail_ref": "",
  "tags": ["tag1", "tag2"],
  "memory_ref": null
}
```

### 4.3 학습 유형 분류 체계

**사용자 학습 유형:**

| type | 탐지 신호 |
|------|-----------|
| `user_fact_question` | What/Who/When/Where 사실형 질문 → AI 답변 |
| `user_concept_question` | Why/How/비교/분석 개념형 질문 → AI 답변 |
| `user_insight_feedback` | 통찰/깨달음 표현 ("새로 알게 됐다", "깨달았다" 등) |
| `user_perspective_shift` | 기존 관점/전제 재구조화 ("이렇게 생각하면 안 되겠다") |

**AI 학습 유형:**

| type | 탐지 신호 |
|------|-----------|
| `ai_trial_error` | 에러/오답 → 수정 패턴 |
| `ai_research_discovery` | 조사 과정에서 새로운 정보/맥락 발견 |
| `ai_strategy_pivot` | 접근 방식/전략 전환 |
| `ai_user_guided` | 사용자가 AI에게 가르치거나 방향 지정 (교정/도메인 주입/가이드라인/방식 교정) |

### 4.4 ID 체계

| 데이터 | 접두사 | 형식 | 예시 |
|--------|--------|------|------|
| 세션 요약 | `ws-` | `ws-YYYYMMDD-NNN` | `ws-20260302-001` |
| 사용자 학습 | `ll-user-` | `ll-user-YYYYMMDD-NNN` | `ll-user-20260302-001` |
| AI 학습 | `ll-ai-` | `ll-ai-YYYYMMDD-NNN` | `ll-ai-20260302-001` |

NNN: 해당 일자 내 순번 (001부터 시작, 기존 JSONL의 마지막 ID 기준 증분).

---

## 5. 워크플로우 개요

v1.4.0 기준 10단계 (Step 0 ~ Step 9).
각 단계의 상세 실행 지시는 `SKILL.md` 참조.

| Step | 이름 | 유형 | 설명 |
|------|------|------|------|
| 0 | 언어 설정 | 자동/대화 | 기존 설정 읽기 또는 최초/변경 시 언어 선택 |
| 1 | 메타정보 수집 | 자동 | collect-meta.py로 날짜, 프로젝트, 세션ID/명, 통계 수집 |
| 2 | 드래프트 생성 | 자동 | 대화 분석 → 2계층 드래프트 + auto memory 중복 확인 |
| 3 | 드래프트 확인 | 대화 | 통합 드래프트 표시 → 확인/수정/부분기록 선택 |
| 4 | 수정 루프 | 대화 | "수정 필요" 시 반영 → Step 3 반복 |
| **5** | **세션 평가** | **자동+대화** | **AI 자기 진단 표시 → 사용자 평가 입력** |
| 6 | 저장 | 자동 | save-wrapup.py로 3개 JSONL에 저장 (evaluation 포함) |
| 7 | Auto Memory 동기화 | 대화 | lesson → auto memory 승격 제안 |
| 8 | /atodo 연동 | 대화 | 액션 아이템 → 할 일 등록 제안 |
| 9 | 완료 메시지 | 자동 | 저장 결과 + 평가 요약 + 누적 통계 표시 |

### Step 5 세션 평가 흐름 상세

```
Step 5 시작
    │
    ├─ 5a: AI 자기 진단 생성 (자동)
    │   └─ 대화 컨텍스트 기반으로 5개 서브 메트릭 (각 score + reason) + improvements (tag + text)
    │
    ├─ 5b: AI 평가 표시 (★/☆ 시각 + reason 한 줄)
    │
    ├─ 5c: 사용자 점수 (AskUserQuestion)
    │   └─ 1-5 단일 선택
    │
    ├─ 5d: 사용자 좋았던 점 (자유 텍스트, 스킵 가능)
    │
    ├─ 5e: 사용자 아쉬웠던 점 (자유 텍스트, 스킵 가능)
    │
    ├─ 5f: 사용자 개선 사항 (자유 텍스트, 스킵 가능)
    │
    └─ Step 6으로 진행
```

---

## 6. 에러 핸들링

| 상황 | 처리 |
|------|------|
| 세션명 미설정 | Step 1 중단 + `/rename` 안내 |
| JSONL 파일 없음 (첫 실행) | 자동 생성 |
| 저장 실패 | 드래프트 텍스트 출력 → 수동 저장 안내 |
| 대화 컨텍스트 너무 짧음 | "추출할 학습 내용이 부족합니다" 안내 |
| /atodo 호출 실패 | 액션 아이템 텍스트만 표시, 수동 등록 안내 |
| 사용자 평가 스킵 | evaluation.user를 `null`로 저장 |

---

## 7. 설계 결정 로그

주요 설계 결정과 근거. 상세 초기 결정은 `docs/plans/2026-02-23-wrapup-skill-design.md` 참조.

| 결정 | 선택 | 근거 |
|------|------|------|
| 저장 포맷 | JSONL | 텍스트 기반 증분 기록, git 호환, 향후 SQLite 이관 용이 |
| 아키텍처 | Skill + 헬퍼 스크립트 | 관심사 분리 (분석/UI = SKILL.md, 저장/검증 = Python) |
| 학습 관점 분리 | 사용자/AI 별도 파일 | 다른 관점의 같은 사건을 독립적으로 추적 |
| 평가 순서 | AI 먼저 → 사용자 후 | anchoring bias 방지, AI 자기 인식 교정 가능 |
| 평가 위치 | Save 전 (Step 5) | JSONL append-only 특성상 한 번에 원자적 저장 |
| AI 평가 구조 | 5개 서브 메트릭 (score+reason) + improvements (tag+text) | overall_score 없음 — 서브 메트릭이 곧 평가 자체. tag로 반복 탐지 가능 |
| 사용자 평가 구조 | 종합 점수 + good/bad/improvements 각각 | 점수와 무관하게 3가지 모두 질문, 각각 스킵 가능 |
| 드래프트 포맷 | 가로선 + 들여쓰기 | CJK 문자 double-width로 좌우 세로선 정렬 불가 |
| 다국어 | 자동 감지 + 저장 설정 | 최초 1회 선택 후 매번 무음 적용 |

---

## 8. 향후 로드맵

| 우선순위 | 버전 | 항목 | 설명 |
|----------|------|------|------|
| ★★★ | v1.4.0 | 세션 평가 기능 | AI 서브 메트릭 + 사용자 평가 + tag 포함 improvements |
| ★★★ | v1.4.1 | Improvement Lifecycle | 반복 탐지 + 졸업 시스템 + auto memory 관리 |
| ★★☆ | v1.5.0 | 평가 고도화 | 자동 해결 판정 + 프루닝 + 개선 트렌드 리포트 |
| ★★☆ | — | 평가 데이터 대시보드 | 축적된 평가 데이터로 세션 품질 트렌드 시각화 |
| ★★☆ | — | Stop 훅 힌트 | 세션 종료 감지 시 "/wrapup 하시겠습니까?" 자동 제안 |
| ★★☆ | — | JSONL → SQLite 인덱스 | 대량 축적 후 복합 검색 성능 개선 |
| ★☆☆ | — | /reflect 기능 | 축적된 데이터에서 패턴 발견 + 성장 리포트 생성 |
| ★☆☆ | — | SessionEnd 훅 백업 | wrapup 미수행 시 경량 자동 요약 |
| ★☆☆ | — | JSONL → 마크다운 렌더링 | 읽기 좋은 주간/월간 리포트 생성 |

---

## 9. 버전 이력 요약

| 버전 | 날짜 | 핵심 변경 |
|------|------|-----------|
| v1.0.0 | 2026-02-23 | 초기 MVP: 2계층 구조, JSONL 포맷, /atodo 연동 |
| v1.1.0 | 2026-02-24 | 다국어 지원 (자동 감지 + 변경 가능) |
| v1.2.0 | 2026-02-24 | `work_done` 필드 추가, 학습 유형 분류 체계 개편 |
| v1.3.0 | 2026-03-01 | Auto Memory 연동 (중복 방지 + 양방향 동기화) |
| **v1.4.0** | **TBD** | **세션 평가 기능 (AI 서브 메트릭 + 사용자 평가 + improvement tag)** |
| v1.4.1 | TBD | Improvement Lifecycle (반복 탐지 + 졸업 시스템) |

상세 변경 이력은 `CHANGELOG.md` 참조.
