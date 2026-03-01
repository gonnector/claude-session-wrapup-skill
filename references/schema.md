# JSONL 스키마 정의

## 파일 위치

| 데이터 | 경로 |
|--------|------|
| 세션 요약 | `Z:\_ai\session-summaries\{project-slug}\summaries.jsonl` |
| 사용자 학습 | `Z:\_myself\lesson-learned\lessons.jsonl` |
| AI 학습 | `Z:\_ai\lesson-learned\lessons.jsonl` |

## 세션 요약 스키마

```jsonl
{
  "id": "ws-20260223-001",
  "date": "2026-02-23T15:30:00",
  "session_id": "abc-123",
  "session_name": "lesson-learned 시스템 설계",
  "project": "z:/_ai/skills/lesson-learned",
  "info_summary": ["핵심 정보 불릿 1", "핵심 정보 불릿 2"],
  "qa_pairs": [
    { "q": "질문", "a": "답변" }
  ],
  "conclusions": [
    { "topic": "안건명", "decision": "결정사항", "rationale": "이유" }
  ],
  "work_done": ["구현: scripts/settings.py 언어 설정 관리", "수정: SKILL.md Step 2 언어 규칙 추가"],
  "action_items": [
    { "title": "할 일", "priority": "high|medium|low", "registered_todo": null }
  ]
}
```

## Lesson-Learned 스키마 (사용자 / AI 공통)

```jsonl
{
  "id": "ll-user-20260223-001",
  "date": "2026-02-23T15:30:00",
  "session_id": "abc-123",
  "session_name": "세션 이름",
  "project": "z:/_ai/skills/lesson-learned",
  "type": "user_question_answer",
  "category": "system-design",
  "title": "학습 제목",
  "summary": "한 줄 요약",
  "context": "발견 맥락",
  "detail_ref": "",
  "tags": ["tag1", "tag2"],
  "memory_ref": null
}
```

### memory_ref 필드

`memory_ref`는 v1.3.0에서 추가된 필드입니다. auto memory에 동일 사실이 이미 기록된 경우 해당 파일명을 참조합니다 (예: `"research-sources.md"`). auto memory에 없는 lesson은 `null`입니다. 이전 레코드에는 해당 필드가 없으며, 없는 경우 `null`로 간주합니다.

### work_done 필드 하위 호환성

`work_done`은 v1.2.0에서 추가된 필드입니다. 이전 레코드에는 해당 필드가 없으며, 없는 경우 `null`로 간주합니다.

### ID 접두사

| 데이터 | 접두사 | 예시 |
|--------|--------|------|
| 세션 요약 | `ws-` | `ws-20260223-001` |
| 사용자 학습 | `ll-user-` | `ll-user-20260223-001` |
| AI 학습 | `ll-ai-` | `ll-ai-20260223-001` |

### 학습 유형 (type)

**사용자 학습:**
- `user_fact_question` — What/Who/When/Where 사실형 질문→AI 답변
- `user_concept_question` — Why/How/비교/분석 개념형 질문→AI 답변
- `user_insight_feedback` — 통찰/깨달음 표현 ("새로 알게 됐다", "깨달았다" 등)
- `user_perspective_shift` — 기존 관점/전제가 틀렸음을 발견하는 관점 재구조화

**AI 학습:**
- `ai_trial_error` — 시행착오를 통한 발견
- `ai_research_discovery` — 조사 과정에서의 새로운 발견
- `ai_strategy_pivot` — 전략/접근 방식 전환
- `ai_user_guided` — 사용자가 AI에게 가르치거나 방향을 지정 (교정/도메인 주입/가이드라인/방식 교정)

## save-wrapup.py 입력 JSON

```json
{
  "session_id": "abc-123",
  "session_name": "세션 이름",
  "project": "z:/_ai/skills/lesson-learned",
  "date": "2026-02-23T15:30:00",
  "summary": {
    "info": ["정보 1", "정보 2"],
    "qa": [{ "q": "질문", "a": "답변" }],
    "conclusions": [{ "topic": "주제", "decision": "결정", "rationale": "이유" }],
    "done": ["구현: ...", "수정: ...", "테스트: ..."],
    "actions": [{ "title": "할 일", "priority": "high" }]
  },
  "user_lessons": [
    {
      "type": "user_fact_question",
      "category": "system-design",
      "title": "제목",
      "summary": "요약",
      "context": "맥락",
      "detail_ref": "",
      "tags": ["tag"],
      "memory_ref": null
    }
  ],
  "ai_lessons": [
    {
      "type": "ai_trial_error",
      "category": "hook-development",
      "title": "제목",
      "summary": "요약",
      "context": "맥락",
      "detail_ref": "",
      "tags": ["tag"],
      "memory_ref": "research-sources.md"
    }
  ]
}
```
