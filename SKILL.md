---
name: wrapup
description: "세션 마무리, 세션 정리, 세션 래핑, 세션 요약, 배운 점 정리, lesson learned, wrapup, 오늘 뭘 배웠지, 세션 회고, 작업 마무리 시 자동으로 추천됩니다. 세션 종료 시 사용자와 AI 각각의 '배운 것'을 구조화된 JSONL로 자동 기록합니다."
---

# /wrapup

세션 종료 시 2계층(세션 요약 + Lesson-Learned)을 한 번에 기록하는 스킬.

- 스키마 상세: `references/schema.md` 참조
- 저장 스크립트: `scripts/save-wrapup.py`
- 통계 스크립트: `scripts/read-stats.py`

## 워크플로우

아래 7단계를 순서대로 실행한다.

### Step 1: 세션 메타정보 수집

Bash 명령 병렬 실행:

```bash
date +"%Y-%m-%dT%H:%M:%S"    # 현재 시각
pwd                            # 프로젝트 경로
python scripts/read-stats.py "$(pwd)"  # 누적 통계
```

세션 ID와 세션명 확인:
- `~/.claude/projects/` 하위 JSONL 파일에서 현재 세션 정보 추출
- 세션명이 없으면 **중단** → "세션명이 설정되지 않았습니다. `/rename 세션명`으로 설정 후 다시 시도해주세요." 안내

### Step 2: 대화 컨텍스트 분석 → 2계층 드래프트 생성

전체 대화 컨텍스트에서 아래 항목을 추출한다.

**계층 1 — 세션 요약:**
- A. **정보 요약**: 세션에서 조사/파악된 핵심 정보 (불릿 포인트)
- B. **Q&A 정리**: 사용자 질문 + AI 답변 쌍
- C. **협의 결론**: 토론/비교된 안건의 결론 + 이유(rationale)
- D. **액션 아이템**: 후속 할 일 목록 (priority: high/medium/low)

**계층 2 — Lesson-Learned:**
- E. **사용자 학습** 탐지 신호:
  - 질문→답변 패턴 → type: `user_question_answer`
  - "이건 몰랐는데" 등 긍정 피드백 → type: `user_insight_feedback`
  - "왜?", "차이가?" 등 개념 탐색 → type: `user_concept_exploration`
- F. **AI 학습** 탐지 신호:
  - 에러→수정 패턴 → type: `ai_trial_error`
  - 새 정보 발견 → type: `ai_research_discovery`
  - 전략 수정 → type: `ai_strategy_pivot`

양쪽 모두 해당하면 양쪽 다 기록 (같은 내용이지만 관점이 다름).

각 lesson에 `category`와 `tags`를 부여한다.

### Step 3: 통합 드래프트 표시 + 확인

2계층을 하나의 통합 드래프트로 표시한다. 아래 포맷 사용:

```
## 📋 세션 요약 드래프트

### 정보 요약
- ...

### Q&A
| 질문 | 답변 |
|------|------|
| ... | ... |

### 협의 결론
| 주제 | 결정 | 이유 |
|------|------|------|
| ... | ... | ... |

### 액션 아이템
- [ ] [high] ...
- [ ] [medium] ...

---

## 🧠 Lesson-Learned 드래프트

### 사용자 학습
1. **[제목]** (type) — 요약

### AI 학습
1. **[제목]** (type) — 요약
```

AskUserQuestion으로 확인:
- "확인 - 이대로 기록"
- "수정 필요"
- "세션 요약만 기록"
- "Lesson-Learned만 기록"

### Step 4: 수정 루프

"수정 필요" 선택 시 사용자의 자유 텍스트 수정 지시를 받아 드래프트 반영 → Step 3 반복.

### Step 5: 저장

확인된 드래프트를 JSON으로 구성하여 `scripts/save-wrapup.py`에 stdin으로 전달:

```bash
echo '<json>' | python scripts/save-wrapup.py
```

입력 JSON 구조는 `references/schema.md`의 "save-wrapup.py 입력 JSON" 참조.

"세션 요약만" 선택 시 `user_lessons`, `ai_lessons`를 빈 배열로 전달.
"Lesson-Learned만" 선택 시 `summary` 내부를 빈 배열로 전달.

저장 실패 시: 드래프트 텍스트를 그대로 출력하여 수동 저장 가능하게 안내.

### Step 6: /atodo 연동 제안

액션 아이템이 1건 이상이면 AskUserQuestion:
- "전부 등록" → 각 항목을 `/atodo` Skill 호출
- "선택해서 등록" → 개별 AskUserQuestion으로 확인 후 등록
- "나중에" → 건너뜀

`/atodo` 호출 실패 시: 액션 아이템 텍스트만 표시, 수동 등록 안내.

### Step 7: 완료 메시지

저장 결과와 누적 통계 표시:

```
✅ 세션 랩업 완료!

저장됨:
- 세션 요약: {project}/.claude/session-summaries/summaries.jsonl
- 사용자 학습: N건
- AI 학습: N건

누적 통계:
- 사용자 학습 총 N건 | AI 학습 총 N건 | 세션 요약 총 N건
```

## 에러 핸들링

| 상황 | 처리 |
|------|------|
| 세션명 미설정 | Step 1 중단 + `/rename` 안내 |
| JSONL 파일 없음 (첫 실행) | 자동 생성 |
| 저장 실패 | 드래프트 텍스트 출력 → 수동 저장 안내 |
| 대화 컨텍스트 너무 짧음 | "추출할 학습 내용이 부족합니다" 안내 |
| /atodo 호출 실패 | 액션 아이템 텍스트만 표시, 수동 등록 안내 |
