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
  "tags": ["tag1", "tag2"]
}
```

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
- `user_question_answer` — 질문하고 답을 얻은 것
- `user_insight_feedback` — AI 제공 정보에 대한 긍정 피드백
- `user_concept_exploration` — 개념적 이해 추구

**AI 학습:**
- `ai_trial_error` — 시행착오를 통한 발견
- `ai_research_discovery` — 조사 과정에서의 새로운 발견
- `ai_strategy_pivot` — 전략 수정을 통한 해결

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
      "type": "user_question_answer",
      "category": "system-design",
      "title": "제목",
      "summary": "요약",
      "context": "맥락",
      "detail_ref": "",
      "tags": ["tag"]
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
      "tags": ["tag"]
    }
  ]
}
```
