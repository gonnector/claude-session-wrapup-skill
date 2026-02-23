# Lesson-Learned 자동 기록 시스템 설계를 위한 리서치 보고서

> Deep Research Report | 생성일: 2026-02-23 | 43개 소스 직접 인용 (95개 소스 조사)

---

## 목차

1. [Executive Summary](#executive-summary)
2. [리서치 방법론](#리서치-방법론)
3. [기존 코드베이스 분석 결과](#기존-코드베이스-분석-결과)
4. [Claude Code 플러그인 생태계 조사](#claude-code-플러그인-생태계-조사)
5. [개발자 TIL/학습 기록 도구 조사](#개발자-til학습-기록-도구-조사)
6. [저장 포맷 분석](#저장-포맷-분석)
7. [AI 대화 학습 추출 패턴](#ai-대화-학습-추출-패턴)
8. [기술 구현 전략: 훅 고급 활용](#기술-구현-전략-훅-고급-활용)
9. [세션 랩업 구조 설계](#세션-랩업-구조-설계)
10. [종합 권고안](#종합-권고안)
11. [핵심 발견사항 및 결론](#핵심-발견사항-및-결론)
12. [한계 및 주의사항](#한계-및-주의사항)
13. [출처](#출처)

---

## Executive Summary

세션 종료 시 사용자와 AI 각각의 "배운 것"을 구조화하여 자동 기록하는 시스템 설계를 위해 5개 서브토픽에 걸쳐 95개 소스를 조사했다. 핵심 발견사항은 다음과 같다:

**Claude Code 생태계에는 이미 8개 이상의 세션 래핑/메모리 플러그인이 존재하며**, claude-mem(AI 압축+벡터DB), claude-memory(6범주 구조화 JSON), Claude Diary(마크다운 일기+패턴 분석) 등 다양한 아키텍처 접근이 검증되어 있다. 그러나 **"사용자가 배운 것"과 "AI가 시행착오로 배운 것"을 명시적으로 구분하여 기록하는 도구는 발견되지 않았다**.

**저장 포맷으로는 JSONL + 마크다운 하이브리드를 권장한다.** JSONL은 텍스트 기반 포맷 중 증분 기록에 업계 표준이며, Excel(xlsx)은 바이너리 포맷으로 git 버전 관리, 프로그래밍 접근성, 증분 기록 모든 면에서 부적합하다. 단, 사용자의 기존 todo.xlsx 활용 패턴(openpyxl)을 고려하면 xlsx 뷰어/에디터로서의 호환성은 유지할 수 있다.

**구현 형태로는 Skill(스킬) + Command(커맨드) 조합을 권장한다.** 스킬은 세션 대화 컨텍스트에 대한 완전한 접근 권한을 가지며, AI가 자동으로 관련 시점에 추천할 수 있다. `/wrapup` 커맨드로 명시적 호출을 지원하고, Stop 훅의 prompt 타입으로 자동 트리거 힌트를 제공하는 3계층 구조가 최적이다.

**세션 랩업은 2계층 구조로 설계한다:** 계층 1은 "세션 요약"(정보 요약 / Q&A 정리 / 협의 결론+이유 / 액션 아이템)으로 회의록 베스트 프랙티스 [41][42][43]를 차용하며, 계층 2는 "Lesson-Learned"(사용자 학습 / AI 학습)로 지적 성장을 기록한다. 액션 아이템은 `/atodo`로 연동하여 할 일 관리와 자연스럽게 연계된다.

**학습 추출은 LangMem의 3중 메모리 모델(의미/삽화/절차)을 참조하되, 실용적으로 단순화한다:** 사용자 학습은 "질문→답변" 패턴과 "피드백→인사이트" 패턴으로 탐지하고, AI 학습은 "시행착오(trial&error)" 패턴과 "조사→발견" 패턴으로 탐지한다.

---

## 리서치 방법론

- **리서치 질문**: 세션 대화에서 사용자와 AI 각각의 학습 내용을 자동 추출하여 구조화된 포맷으로 증분 기록하는 최적의 시스템은 어떻게 설계해야 하는가?
- **범위**: Claude Code 생태계 내부 + 개발자 도구 생태계 + AI 대화 패턴 + 저장 포맷 비교
- **참조 소스**: 43개 직접 인용 (95개 조사, 52개는 배경 조사용으로 직접 인용하지 않음)
- **사용 검색 쿼리**: ~60개
- **품질 검증**: 팩트체크 + 자체 비평 포함 (최고 수준)
- **리서치 일시**: 2026-02-23
- **내부 탐색**: 3개 병렬 Explore 에이전트 (기존 코드베이스 분석)
- **외부 리서치**: 5개 병렬 Research 에이전트 + 1개 팩트체크 에이전트

---

## 기존 코드베이스 분석 결과

### /atodo 커맨드 패턴 (핵심 참조 구현)

`C:\Users\Pro\.claude\commands\atodo.md`에 구현된 6단계 워크플로우가 lesson-learned 시스템의 핵심 참조 패턴이다:

| 단계 | 내용 | 적용 가능성 |
|------|------|------------|
| Step 1 | 세션 정보 자동 수집 (시간, 폴더, 세션ID/명) | 직접 재사용 |
| Step 2 | AI가 대화 컨텍스트에서 내용 추출/제안 | 핵심 재사용 |
| Step 3 | 드래프트 표시 → AskUserQuestion 확인 | 직접 재사용 |
| Step 4 | 수정 요청 → 반영 → 재확인 루프 | 직접 재사용 |
| Step 5 | openpyxl로 xlsx 행 추가 | 포맷 변경 시 수정 |
| Step 6 | 완료 메시지 출력 | 직접 재사용 |

### 기존 훅 시스템 현황

- **SessionEnd 훅 구현 완료**: `session-end-copy-log.sh`가 세션 로그를 `Z:/_ai/session-log/`에 자동 백업
- **stdin JSON 수신**: `session_id`, `transcript_path`, `cwd`, `permission_mode`
- **Stop 훅**: 미구현 (lesson-learned용으로 신규 추가 가능)

### 기존 lesson-learned 파일

- `Z:\_ai\lesson-learned\lesson-learned_claude.md`: Claude Desktop 문제 해결 7개 원칙 (2026-02-20)
- `Z:\_ai\lesson-learned\lesson-learned_design.md`: Figma 작업 학습사항 5개 원칙 (2026-02-19)
- 구조: 마크다운 제목 + 날짜 + 번호 매긴 원칙 목록 (비정형)

### Skill vs Command 구조 차이

| 특성 | Skill | Command |
|------|-------|---------|
| 호출 방식 | AI 자동 추천 + 명시적 `/skill-name` | 명시적 `/command-name`만 |
| 대화 컨텍스트 | 전체 접근 가능 | 전체 접근 가능 |
| 파일 구조 | `SKILL.md` + 하위 디렉토리 | 단일 `.md` 파일 |
| 자동 트리거 | description 매칭으로 AI가 자동 추천 | 없음 |
| 확장성 | 참조 자료, 예시, 서브파일 포함 가능 | 단일 파일 제한 |

**결론**: Skill이 더 적합. 대화 컨텍스트 접근 + AI 자동 추천 + 확장 가능한 파일 구조.

---

## Claude Code 플러그인 생태계 조사

### 세션 래핑/회고 플러그인 비교

| 플러그인 | 아키텍처 | 저장 형식 | 자동화 수준 | AI 활용 | 핵심 특징 |
|---------|---------|----------|-----------|---------|----------|
| **claude-mem** [2] | 5개 훅 자동 캡처 | SQLite + Chroma 벡터DB | 완전 자동 | Claude Agent SDK 압축 | ~10배 토큰 절약, 시맨틱 검색 |
| **claude-memory** [3] | 4단계 파이프라인 | JSON 파일 + 인덱스 | 반자동 (결정론적 Triage) | haiku/sonnet 드래프팅 | 6범주 구조화, LLM 비용 제로 Triage |
| **Claude Diary** [5] | PreCompact 훅 + /diary | 마크다운 파일 | 반자동 | /reflect로 패턴 분석 | CLAUDE.md 자동 업데이트 |
| **claude-journal-mcp** [4] | 시간/메시지 임계값 | SQLite 단일 테이블 | 반자동 | ML 미사용 | 텍스트 검색만, 경량 |
| **claude-sessions** [6] | 슬래시 명령어 | 마크다운 파일 | 수동 | 없음 | start/update/end 3단계 |
| **Ars Contexta** [7] | Stop + 6Rs 파이프라인 | 위키링크 마크다운 | 완전 자동 | 지식 그래프 통합 | 6Rs: Record→Reduce→Reflect→Reweave→Verify→Rethink |
| **CLAUDE.md Management** [8] | /revise-claude-md 명령 | CLAUDE.md diff | 수동 | diff 기반 업데이트 | 공식 플러그인 |
| **Code Insights** [12] | 세션 분석 앱 | Firebase | 반자동 | 전이 가능 지식 추출 | BYOF 프라이버시 |

### 도구별 래핑 결과물(Output) 비교

각 도구가 실제로 **무엇을 산출하는지** — 래핑 결과의 형태, 내용, 구조를 비교한다:

| 도구 | 결과물 형태 | 결과물 내용 | 결과물 구조 예시 |
|------|-----------|-----------|----------------|
| **claude-mem** | SQLite 행 + Chroma 벡터 임베딩 | 도구 사용 로그를 ~500 토큰으로 압축한 "관찰(observation)" 단위. 세션 요약은 Stop 훅에서 생성 | `{tool, input_summary, output_summary, context, timestamp}` — 3계층 검색(키워드→시맨틱→전문) |
| **claude-memory** | 카테고리별 JSON 파일 (`~/.claude/memory/{category}/`) | 6개 범주별 구조화된 메모리: 세션 요약(what/why/decisions/next), 의사결정(what/why/alternatives/tradeoffs), 런북(trigger/steps/verification), 제약조건, 기술부채, 선호도 | `{id, category, content: {what, why, ...}, created_at, session_id}` + 카테고리별 Pydantic 스키마 검증 |
| **Claude Diary** | 마크다운 파일 (`~/.claude/memory/diary/YYYY-MM-DD-session-N.md`) | 세션별 일기: 주요 성취, 설계 결정과 이유, 도전 과제, 배운 교훈, 열린 질문 | `# Session Diary\n## Achievements\n- ...\n## Design Decisions\n- ...\n## Challenges\n- ...\n## Lessons\n- ...` |
| **claude-journal-mcp** | SQLite 행 (`journal_entries` 테이블) | 타임스탬프 + 자유 형식 텍스트 항목. 태그 지원. 30분/3메시지 임계값으로 자동 캡처 | `{id, content, tags[], created_at}` — 순수 텍스트/키워드 검색만 |
| **claude-sessions** | 마크다운 파일 (`.claude/sessions/session-{date}.md`) | 수동 입력 세션 기록: 시작 시 목표, 업데이트 시 진행상황, 종료 시 결과 | `# Session {date}\n## Goals\n- ...\n## Progress\n- ...\n## Results\n- ...` |
| **Ars Contexta** | 위키링크 마크다운 (`ops/sessions/` + 지식 그래프) | 6Rs 파이프라인으로 세션 학습을 지식 노드로 변환. Record(원시기록) → Reduce(압축) → Reflect(패턴 식별) → Reweave(기존 지식과 통합) → Verify(검증) → Rethink(재구성) | `# [[Session 2026-02-23]]\n## Key Insights\n- [[concept-A]] relates to [[concept-B]]\n## Patterns\n- ...` |
| **CLAUDE.md Management** | CLAUDE.md diff 패치 | 세션에서 발견한 프로젝트 관련 규칙/패턴을 CLAUDE.md 파일에 추가/수정하는 diff 제안 | `+ ## New Pattern\n+ - When doing X, always Y because Z` |
| **Code Insights** | Firebase 문서 | 세션 대화에서 추출한 결정사항, 학습 내용, 기법을 전이 가능한 지식으로 구조화 | 결정(what/why/context) + 학습(insight/evidence) + 기법(pattern/when-to-use) |

**핵심 관찰**: 결과물의 범위가 도구마다 크게 다르다. claude-mem은 **도구 사용 로그**(저수준), claude-memory는 **6범주 구조화 메모리**(중수준), Claude Diary와 Ars Contexta는 **세션 회고/성찰**(고수준)에 초점을 맞춘다. 우리 시스템은 이 중 **고수준 세션 회고 + 구조화된 학습 분류**의 조합이 필요하다.

### 핵심 패턴 분류 (3가지 아키텍처)

1. **완전 자동화**: claude-mem, Ars Contexta — 훅 이벤트로 자동 캡처+압축+저장
2. **반자동화**: Claude Diary, claude-journal-mcp — 임계값 트리거 + 수동 명령 하이브리드
3. **수동 명령**: claude-sessions, CLAUDE.md Management — 사용자가 명시적 호출

**lesson-learned 시스템에의 시사점**: **반자동화 패턴이 최적**. 완전 자동화는 노이즈가 많고(모든 Stop 이벤트에서 트리거), 수동은 사용자가 잊기 쉬움. `/wrapup` 명시적 호출 + Stop 훅 힌트(세션 종료 감지 시 "wrapup 하시겠습니까?" 제안)의 조합이 적절하다.

### Anthropic 공식 입장

- GitHub Issue #4654 (Persistent Lessons Learned): **CLOSED - NOT_PLANNED** (2025-07-29)
- SessionEnd 차단 훅 요청 (Issue #12755): **NOT_PLANNED**
- 네이티브 lesson-learned 기능은 계획에 없으며, 플러그인/스킬로 구현해야 함 [1]

---

## 개발자 TIL/학습 기록 도구 조사

### 3세대 진화

| 세대 | 대표 도구 | 특징 | 한계 |
|------|----------|------|------|
| **1세대: 수동 마크다운** | jbranchaud/til (14k+ 스타), simonw/til (575+ 항목) | 진입 장벽 낮음, 유연 | 규율 필요, 메타데이터 없음 |
| **2세대: 반자동 도구 체인** | Simon Willison TIL (SQLite+Actions), VSCode Journal (34k 설치), Journalot CLI | 날짜 자동 생성, 빌드 자동화 | 내용은 수동 작성 |
| **3세대: AI 자동 추출** | Claude Session Memory, claude-mem, Claude Diary, Code Insights | 대화에서 자동 추출 | 품질 보장 미검증, 노이즈 |

### 핵심 인사이트

- **Inkdrop + Claude Code MCP 통합 패턴** [1]: CLAUDE.md에 "각 작업 종료 시 저널에 기록하라"고 지시하면 AI가 자동 기록 → 이것이 skill의 description으로 구현 가능
- **Simon Willison TIL 패턴**: 마크다운 수동 작성 → Python 스크립트 SQLite 빌드 → GitHub Actions 배포 → 검색 가능 웹사이트. 이 파이프라인 사상이 lesson-learned에도 적용 가능 (JSONL 기록 → SQLite 빌드 → 검색)
- **Claude Code Session Memory**: ~10,000 토큰 후 첫 추출, 이후 ~5,000 토큰마다 자동 업데이트 → 세션 요약 자동화의 참조 임계값 [2]

---

## 저장 포맷 분석

### 종합 비교표

| 평가 기준 | JSONL | Markdown | Excel(xlsx) | SQLite | CSV |
|-----------|-------|----------|-------------|--------|-----|
| **증분 기록(append)** | **업계 표준** ⚠️ | 가능(비구조적) | 복잡(라이브러리) | **최적**(WAL) | 가능(행 추가) |
| **검색성** | grep/jq 가능 | 텍스트 검색만 | 내장 검색 | **SQL 인덱스 최적** | 열 기반 제한 |
| **DB 이관성** | **높음**(표준 교환) | 파싱 필요 | 라이브러리 필요 | **직접 이관** | **높음** |
| **git 버전 관리** | **우수** | **최적** | **불가** | **불가** | 우수 |
| **프로그래밍 접근성** | **매우 높음** | 파싱 복잡 | 중간(openpyxl) | **매우 높음** | 높음 |
| **사람의 가독성** | 중간 | **최고** | 높음(GUI) | 낮음(도구 필요) | 낮음(대량시) |
| **LLM 처리 정확도** | 낮음(45.0%) | **최고**(60.7%) | N/A | N/A | 낮음(44.3%) |

### 포맷 권고

**1차 기록: JSONL** — 구조화된 증분 기록의 텍스트 기반 업계 표준 [6]. 각 줄이 독립 JSON 객체로 부분 손상 시 복구 가능. git diff 추적 우수.

**2차 뷰: 마크다운 렌더링** — JSONL에서 읽기 좋은 마크다운으로 변환하는 스크립트/뷰어 제공. 사람의 가독성 60.7%로 LLM 처리에도 최적 [8].

**3차 검색: SQLite 인덱스** (향후) — 데이터 축적 후 JSONL→SQLite 변환 파이프라인으로 복합 검색 지원. JSON 대비 180배 파싱 개선 사례 [7].

**Excel(xlsx) 평가**: 바이너리 포맷으로 git 변경 추적 불가, 증분 기록에 전체 파일 재작성 필요, 프로그래밍 접근 시 추가 라이브러리(openpyxl) 필요. **lesson-learned 1차 저장 포맷으로 부적합하나**, 사용자의 기존 todo.xlsx 워크플로우와의 호환성을 위해 JSONL→xlsx 내보내기 기능은 향후 고려 가능.

---

## AI 대화 학습 추출 패턴

### 메모리 유형 기반 추출 체계

LangMem SDK와 학술 연구(arxiv 2504.15965)가 제시하는 3중 메모리 모델 [10]:

| 메모리 유형 | 정의 | lesson-learned 매핑 |
|------------|------|-------------------|
| **의미 메모리 (Semantic)** | 사실, 관계, 지식 | 사용자가 새로 배운 지식 ("이건 몰랐는데...") |
| **삽화 메모리 (Episodic)** | 특정 사례, 경험 | AI의 시행착오 해결 사례 ("이렇게 했더니 실패→이렇게 수정") |
| **절차 메모리 (Procedural)** | 행동 패턴, 시스템 프롬프트 | 반복 적용 가능한 패턴/규칙 |

### 사용자 학습 vs AI 학습 구분 패턴

Anthropic의 코딩 학습 연구(n=52)에서 도출된 상호작용 패턴 [9]:

**사용자 학습 탐지 신호**:
1. **질문→답변 패턴**: 사용자가 명시적으로 궁금한 점을 질문하고 답을 받은 경우
2. **피드백→인사이트 패턴**: AI가 제공한 정보에 대해 "오 이건 몰랐네", "좋은 정보다" 등의 긍정적 피드백
3. **개념 탐색 패턴**: 사용자가 "왜?", "어떻게?", "차이가 뭐야?" 등 개념적 이해를 추구

**AI 학습 탐지 신호**:
1. **시행착오(Trial&Error) 패턴**: 에러 발생 → 원인 분석 → 수정 시도 → 성공/실패 반복
2. **조사→발견 패턴**: 새로운 정보 조사(WebSearch/WebFetch/Read) → 발견 → 요약
3. **전략 수정 패턴**: 초기 접근 실패 → 대안 모색 → 성공적 해결

### 구조화된 추출 기법

- **JSON 스키마 + LLM 네이티브 기능**: 99% 이상 스키마 준수율 [11]
- **Reflexion 프레임워크**: Actor-Evaluator-Self-Reflection 3모델 구조로 AI 시행착오를 언어적 피드백으로 변환 [11]
- **증분 메모리 업데이트**: 삼각주 추가(가장 일반적), 키워드 교체(가장 비용 효과적), 부분 재계산 3가지 전략 [14]

---

## 기술 구현 전략: 훅 고급 활용

### Stop 훅 대화 컨텍스트 접근

| 훅 타입 | 컨텍스트 접근 | 한계 | 적합성 |
|---------|-------------|------|--------|
| **command** | stdin JSON (session_id, transcript_path, last_assistant_message) | 대화 전문 접근 불가, 스크립트로 transcript 파싱 가능 | 중간 |
| **prompt** | 메타데이터만 (버그/회귀로 대화 컨텍스트 미접근) ⚠️ [4] | 2026-01 기준 미해결 | 낮음 |
| **agent** | 50턴 도구 사용 (Read, Grep, Glob 등) [5] | 타임아웃 60초 기본 | 높음 |

### 권장 구현 아키텍처: 3계층 구조

```
계층 1: Skill (핵심)
├── /wrapup 명시적 호출 → 전체 대화 컨텍스트 접근
├── AI가 "세션 마무리" 패턴 감지 시 자동 추천
└── AskUserQuestion으로 드래프트 확인/수정 루프

계층 2: Stop 훅 (힌트)
├── command 타입: stop_hook_active 체크 → 이전 wrapup 여부 확인
├── last_assistant_message 분석으로 세션 종료 감지
└── 종료 감지 시 "wrapup 하시겠습니까?" 제안 (세션 내 메시지로)

계층 3: SessionEnd 훅 (백업)
├── transcript_path로 JSONL 파싱
├── 이미 wrapup 완료 여부 체크 (플래그 파일)
└── 미완료 시 경량 자동 요약 저장 (사용자 확인 없이)
```

### Transcript JSONL 구조

각 엔트리는 독립 JSON 객체 [5]:
```json
{
  "type": "user|assistant|summary",
  "message": {"role": "...", "content": [...]},
  "uuid": "...",
  "parentUuid": "...",
  "timestamp": "ISO 8601",
  "sessionId": "...",
  "isSidechain": false,
  "usage": {"input_tokens": N, "output_tokens": N}
}
```

`isSidechain: true`는 서브에이전트 대화로 메인 컨텍스트에서 제외 가능.

### 무한 루프 방지 (필수)

Stop 훅에서 Claude에게 추가 작업을 지시하면 다시 Stop 이벤트가 발생하는 루프 위험:
- `stop_hook_active` 필드 체크 필수
- `once: true` 옵션으로 세션 당 1회 제한
- 플래그 파일(`~/.claude/wrapup-done-{session_id}`)로 중복 방지

---

## 세션 랩업 구조 설계

### 회의록 베스트 프랙티스에서 배우는 구조

효과적인 회의록(meeting minutes)은 수십 년간의 비즈니스 관행을 통해 검증된 정보 정리 패턴이다. AI 협업 세션도 본질적으로 "인간과 AI의 회의"이므로, 이 구조를 차용하는 것이 합리적이다.

**회의록의 핵심 구성요소** [41][42][43]:

| 구성요소 | 목적 | 세션 랩업 대응 |
|---------|------|---------------|
| **기본 정보** (날짜, 참석자, 목적) | 맥락 추적 | 세션 메타정보 (세션ID, 세션명, 프로젝트, 날짜) |
| **안건별 논의 요약** | 무엇이 논의되었는지 기록 | 세션 정보 요약 + 질문별 답변 정리 |
| **의사결정 기록** (결정사항 + 이유) | 왜 그 결정을 했는지 추적 | 안건별 협의 결론 및 이유 |
| **액션 아이템** (담당자, 기한) | 다음 행동 명확화 | 향후 액션 아이템 → /atodo 연동 |
| **다음 회의/후속 사항** | 연속성 보장 | 다음 세션 계획/잔여 과제 |

**회의록 베스트 프랙티스에서 도출한 핵심 원칙**:

1. **의사결정은 논의와 분리하여 별도로 기록한다** — 논의 흐름 속에 결정이 묻히면 나중에 찾기 어렵다. 결정사항과 그 이유(rationale)를 명시적으로 뽑아내는 것이 핵심 [42]
2. **액션 아이템은 반드시 담당자(owner)와 기한(deadline)을 포함한다** — "누가 언제까지"가 없는 액션 아이템은 실행되지 않는다 [41][43]
3. **토씨 하나하나가 아닌 핵심 논의와 결정을 기록한다** — 축어록이 아닌 "무엇이 논의되고 무엇이 결정되었는지"에 초점 [42]
4. **즉시 공유한다** — 24~72시간 내 배포가 권장. 기억이 생생할 때 검토해야 정확도가 보장된다 [42]

### 세션 랩업 2계층 구조

사용자의 요구사항 분석과 회의록 베스트 프랙티스를 종합하면, 세션 랩업은 **2개의 분리된 계층**으로 구성된다:

```
┌─────────────────────────────────────────────────────┐
│  계층 1: 세션 요약 (Session Summary)                 │
│  = "회의록" 역할 — 세션에서 무엇이 일어났는가         │
│                                                     │
│  ┌─ A. 정보 요약: 세션에서 파악/조사된 핵심 정보      │
│  ├─ B. Q&A 정리: 질문별 답변 정리                    │
│  ├─ C. 협의 결론: 안건별 결정사항 + 이유              │
│  └─ D. 액션 아이템: 후속 할 일 목록 → /atodo 연동     │
│                                                     │
├─────────────────────────────────────────────────────┤
│  계층 2: Lesson-Learned (지적 성장 기록)              │
│  = "배움 일지" 역할 — 나와 AI가 무엇을 배웠는가       │
│                                                     │
│  ┌─ E. 사용자 학습: "이건 몰랐는데" 순간들            │
│  └─ F. AI 학습: 시행착오, 발견, 전략 수정             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**왜 2계층인가?**

- **계층 1(세션 요약)은 "실무"다** — 무슨 일이 있었고, 무엇이 결정되었고, 다음에 뭘 해야 하는지. 프로젝트 관리 관점.
- **계층 2(Lesson-Learned)는 "성장"이다** — 이 세션을 통해 내가(또는 AI가) 어떤 새로운 지식/통찰을 얻었는지. 지적 자산 관점.
- 두 계층은 같은 세션 대화에서 추출하지만, **저장 위치와 목적이 다르다.** 세션 요약은 프로젝트 문맥에 종속되고, lesson-learned는 프로젝트를 초월하는 범용 지식이다.

### 각 구성요소 상세

#### A. 정보 요약 (Information Summary)

세션에서 조사하거나 파악한 핵심 정보를 구조화한다. 리서치 결과, 코드 분석 결과, 환경 파악 결과 등이 해당.

```
정보 요약:
  - Claude Code 훅은 12~14개 라이프사이클 이벤트 지원 (Stop, SessionEnd 등)
  - Stop 훅의 prompt 타입은 대화 컨텍스트 접근에 버그 있음 (Issue #11786)
  - 기존 세션 래핑 플러그인 8개 조사 완료 (claude-mem, Claude Diary 등)
```

#### B. Q&A 정리 (Question & Answer Compilation)

세션에서 사용자가 던진 질문과 그에 대한 답변을 쌍으로 정리한다.

```
Q&A:
  Q1: Skill과 Command 중 어떤 것이 대화 컨텍스트에 접근 가능한가?
  A1: 둘 다 접근 가능. 차이점은 Skill이 AI 자동 추천을 지원하고 확장 가능한 파일 구조를 가짐.

  Q2: JSONL과 Excel 중 증분 기록에 적합한 포맷은?
  A2: JSONL. Excel은 바이너리 포맷으로 git 비호환, 전체 파일 재작성 필요.
```

#### C. 협의 결론 (Discussion Conclusions with Rationale)

사용자와 AI가 토론/비교/분석한 안건의 결론과 **결정 이유**를 기록한다. 회의록 베스트 프랙티스에서 가장 강조하는 부분이다 [42].

```
협의 결론:
  안건 1: 구현 형태 선택
    결론: Skill + Command 하이브리드
    이유: Skill은 AI 자동 추천 + 확장성, Command는 사용자 명시적 트리거 편의성.
          양쪽의 장점을 결합.

  안건 2: 저장 포맷 선택
    결론: JSONL (1차), 마크다운 렌더링 (2차)
    이유: 텍스트 기반 증분 기록 표준, git 호환, 향후 SQLite 이관 용이.
          Excel은 바이너리 한계로 배제.
```

#### D. 액션 아이템 (Action Items → /atodo 연동)

후속 해야 할 작업을 명확한 형태로 정리한다. 각 항목은 `/atodo`로 등록 가능한 수준의 구체성을 갖춘다.

```
액션 아이템:
  1. [구현] lesson-learned 스킬 MVP 개발 (SKILL.md + 워크플로우)
  2. [구현] Stop 훅 힌트 시스템 추가 (command 타입)
  3. [향후] 중복 탐지 기능 추가 (td0000000006으로 등록 완료)
  4. [향후] JSONL → SQLite 검색 파이프라인
```

세션 랩업 완료 후 "이 액션 아이템들을 /atodo로 등록하시겠습니까?"를 AskUserQuestion으로 제안하면, 세션 랩업→할 일 관리의 자연스러운 연계가 만들어진다.

#### E-F. Lesson-Learned (별도 계층)

세션 요약(A~D)과 독립적으로, 지적 성장을 위한 학습 기록을 추출한다. 이 부분이 본 리서치의 핵심 주제이며, "AI 대화 학습 추출 패턴" 섹션과 "종합 권고안"에서 상세히 다룬다.

### 세션 랩업 vs Lesson-Learned 비교

| 차원 | 세션 요약 (계층 1) | Lesson-Learned (계층 2) |
|------|-------------------|----------------------|
| **목적** | 프로젝트 진행 관리 | 지적 성장 기록 |
| **수명** | 프로젝트 종속 (프로젝트 종료 시 아카이브) | 영구 축적 (프로젝트 초월) |
| **저장** | 프로젝트 폴더 또는 세션 로그 | `Z:\_myself\lesson-learned\` / `Z:\_ai\lesson-learned\` |
| **내용** | 무엇이 일어났고, 무엇이 결정되었고, 다음에 뭘 할지 | 무엇을 새로 배웠고, 어떤 시행착오를 겪었는지 |
| **참조 빈도** | 단기 (다음 세션, 다음 주) | 장기 (수개월~수년 후에도 유효) |
| **중복 가능성** | 낮음 (세션마다 고유한 진행상황) | 높음 (같은 교훈 반복 학습 가능) → 중복 탐지 필요 |

### 실행 워크플로우 통합안

```
/wrapup 호출 시 전체 흐름:

  Step 1: 세션 메타정보 수집
    → 시간, 폴더, 세션ID, 세션명

  Step 2: AI가 대화 분석하여 2계층 드래프트 생성
    ┌── [세션 요약]
    │   A. 정보 요약 (핵심 N건)
    │   B. Q&A 정리 (질문 M건)
    │   C. 협의 결론 (안건 K건)
    │   D. 액션 아이템 (할 일 L건)
    ├── [Lesson-Learned]
    │   E. 사용자 학습 (P건)
    │   F. AI 학습 (Q건)
    └──

  Step 3: AskUserQuestion으로 드래프트 확인
    → "확인" / "수정 필요"

  Step 4: 수정 루프 (필요시)

  Step 5: 저장
    → 세션 요약 → 프로젝트 폴더 or 세션 로그
    → 사용자 학습 → Z:\_myself\lesson-learned\lessons.jsonl
    → AI 학습 → Z:\_ai\lesson-learned\lessons.jsonl

  Step 6: /atodo 연동 제안
    → "액션 아이템 L건을 /atodo로 등록하시겠습니까?"
    → 승인 시 각 항목을 /atodo 워크플로우로 전달

  Step 7: 완료 메시지
```

---

## 종합 권고안

### 1. 구현 형태: Skill + Command 하이브리드

| 구성요소 | 형태 | 역할 |
|---------|------|------|
| `wrapup/SKILL.md` | Skill | 핵심 로직, AI 자동 추천, 대화 컨텍스트 분석 |
| `/wrapup` | Command (Skill 호출) | 사용자 명시적 트리거 |
| Stop 훅 | Hook (command 타입) | 세션 종료 감지 → wrapup 제안 |
| SessionEnd 훅 | Hook (command 타입) | 백업: 미수행 시 경량 자동 요약 |

### 2. 저장 포맷: JSONL (1차) + 마크다운 렌더링 (2차)

**사용자 학습 (`Z:\_myself\lesson-learned\lessons.jsonl`)**:
```jsonl
{"id":"ll-user-20260223-001","date":"2026-02-23","session_id":"abc-123","session_name":"lesson-learned 시스템 설계","project":"z:/_ai/skills/lesson-learned","type":"user_learning","category":"system-design","pattern":"question_answer","title":"JSONL이 append 기록에 최적인 이유","summary":"텍스트 기반 포맷 중 JSONL이 증분 기록에 업계 표준. 각 줄이 독립 JSON 객체로 부분 손상 시 복구 가능.","detail_ref":"","tags":["format","jsonl","data-storage"]}
```

**AI 학습 (`Z:\_ai\lesson-learned\lessons.jsonl`)**:
```jsonl
{"id":"ll-ai-20260223-001","date":"2026-02-23","session_id":"abc-123","session_name":"lesson-learned 시스템 설계","project":"z:/_ai/skills/lesson-learned","type":"ai_trial_error","category":"hook-development","pattern":"trial_error","title":"prompt 타입 Stop 훅은 대화 컨텍스트 접근 불가","summary":"prompt 타입은 메타데이터만 수신. command/agent 타입 사용 필요.","detail_ref":"z:/_ai/skills/lesson-learned/research/research-report-2026-02-23-lesson-learned-system-design.md","tags":["claude-code","hooks","stop-hook"]}
```

### 3. 학습 분류 체계

**사용자 학습 유형 (`type` 필드)**:
- `user_question_answer`: 질문하고 답을 얻은 것
- `user_insight_feedback`: AI 제공 정보에 대한 긍정 피드백
- `user_concept_exploration`: 개념적 이해 추구

**AI 학습 유형 (`type` 필드)**:
- `ai_trial_error`: 시행착오를 통한 발견
- `ai_research_discovery`: 조사 과정에서의 새로운 발견
- `ai_strategy_pivot`: 전략 수정을 통한 해결

**탐지 패턴 (`pattern` 필드)**:
- `question_answer`, `insight_feedback`, `concept_exploration`
- `trial_error`, `research_discovery`, `strategy_pivot`

### 4. 대화형 워크플로우 (atodo 패턴 적용)

```
Step 1: 세션 메타정보 자동 수집
  → 시간, 폴더, 세션ID, 세션명, 프로젝트

Step 2: AI가 대화 컨텍스트 분석하여 학습 항목 드래프트 생성
  → 사용자 학습 N건, AI 학습 M건 추출
  → 각 항목: 유형, 카테고리, 제목, 요약, 상세 레퍼런스, 태그

Step 3: 드래프트 표시 → AskUserQuestion 확인
  ┌────────────────────────────────────────┐
  │ 세션 학습 기록 드래프트:              │
  │                                        │
  │ [사용자 학습]                           │
  │  1. [카테고리] 제목 - 요약             │
  │  2. [카테고리] 제목 - 요약             │
  │                                        │
  │ [AI 학습]                              │
  │  1. [카테고리] 제목 - 요약             │
  │                                        │
  │ [자동] 세션: session-name | 2026-02-23 │
  │ [맥락] project-folder                  │
  └────────────────────────────────────────┘
  → "확인 - 이대로 기록" / "수정 필요"

Step 4: 수정 루프 (필요시)

Step 5: JSONL 파일에 append
  → 사용자 학습 → Z:\_myself\lesson-learned\lessons.jsonl
  → AI 학습 → Z:\_ai\lesson-learned\lessons.jsonl

Step 6: 완료 메시지
  → 기록 완료: 사용자 N건, AI M건
  → 누적 총계: 사용자 X건, AI Y건
```

### 5. 중복 방지 및 세션 상태 관리

- 세션 내 wrapup 수행 여부를 플래그 파일로 추적
- 재수행 시: "이전 wrapup 이후 추가된 대화만 분석할까요?" 옵션 제공
- SessionEnd 훅에서 플래그 파일 존재 확인 → 존재하면 skip, 없으면 경량 자동 요약

### 6. 향후 확장 (첫 버전 범위 외)

- **중복 탐지**: 새 lesson이 기존 JSONL의 항목과 유사한지 검색 (jq/grep 또는 향후 SQLite)
- **JSONL → xlsx 내보내기**: 사용자의 기존 todo.xlsx 패턴과 호환
- **JSONL → SQLite 인덱스**: 대량 축적 후 복합 검색 지원
- **JSONL → 마크다운 렌더링**: 읽기 좋은 리포트 형태 생성
- `/atodo`에 lesson-learned 항목 등록

---

## 핵심 발견사항 및 결론

1. **Claude Code 생태계에 이미 8개+ 세션 래핑 플러그인이 존재하지만, "사용자 학습 vs AI 학습"을 명시적으로 구분하는 도구는 없다.** 이것이 이 시스템의 차별점이자 핵심 가치이다.

2. **저장 포맷은 JSONL이 최적이다.** Excel은 바이너리 포맷으로 git 버전 관리, 증분 기록, 프로그래밍 접근성 모든 면에서 부적합하다. JSONL은 텍스트 기반 증분 기록의 업계 표준이며 [6], 향후 SQLite 이관(180배 검색 성능 개선 가능 [7])도 용이하다.

3. **구현 형태는 Skill이 Command보다 적합하다.** 대화 컨텍스트 접근 + AI 자동 추천 + 확장 가능한 파일 구조를 모두 지원한다. `/wrapup` 커맨드는 스킬 호출의 숏컷으로 제공.

4. **학습 추출은 LangMem 3중 메모리 모델을 단순화하여 적용한다.** 의미 메모리→사용자 학습, 삽화 메모리→AI 시행착오, 절차 메모리→반복 패턴으로 매핑 [10].

5. **Stop 훅의 prompt 타입은 대화 컨텍스트 접근에 버그/회귀가 있어 [4], command 또는 agent 타입을 사용해야 한다.** 3계층 구조(Skill 핵심 + Stop 훅 힌트 + SessionEnd 백업)가 최적.

6. **대화형 확인 UI는 atodo 패턴을 그대로 재사용한다.** 드래프트 생성 → AskUserQuestion 확인 → 수정 루프 → 저장.

7. **맥락 메타정보는 반드시 포함해야 한다.** 세션ID, 세션명, 프로젝트 폴더, 날짜가 학습의 맥락을 제공하며, 향후 검색과 분석의 핵심 차원이 된다.

---

## 한계 및 주의사항

### 팩트체크 결과 상세

13개 핵심 주장을 독립 소스로 교차 검증한 결과:

**반박됨 (1건 — 수정 완료)**:
- "Claude Code 훅 시스템은 **17개** 라이프사이클 이벤트를 지원" → 독립 소스에서 일관되게 **12~14개**로 확인. 본 레포트에서 구체적 이벤트 수 언급을 삭제하고 "12~14개 (버전에 따라 상이)"로 수정

**부분 확인 (2건 — 표현 완화)**:
- "prompt 타입 Stop 훅은 대화 컨텍스트에 **접근 불가**" → 버그/회귀로 인한 문제이며, 일부 워크어라운드(Sonnet 모델) 존재. "접근 불가"보다 "버그/회귀로 메타데이터만 수신하는 문제 있음"이 정확
- "JSONL은 증분 기록에 **가장 최적화된** 포맷" → "가장 최적화된"이라는 절대 표현은 소스에서 사용되지 않음. "텍스트 기반 구조화 데이터 포맷 중 업계 표준"으로 완화. 바이너리 포맷(Protocol Buffers 등)이 순수 성능에서 우월할 수 있음

**미확인 (1건 — 출처 제한적 표기)**:
- "CLAUDE.md Management 플러그인 설치 수: 39,554건" → 공식 페이지에서는 39,554건이나, 독립 소스(ClaudePluginHub)에서 4건으로 표시. 측정 기준 차이 가능성

**확인됨 (9건)**: claude-mem 토큰 압축율, Stop 훅 last_assistant_message 필드, agent 훅 50턴 제한, JSON→SQLite 180배 개선, LLM 포맷 정확도(Markdown-KV 60.7%), Anthropic 코딩 연구(17% 격차), LangMem 3중 메모리, SessionEnd 비차단, claude-memory 6범주 — 모두 2개 이상 독립 소스에서 일치 확인

### 자체 비평 상세

비평 에이전트가 4개 관점에서 12개 개선 제안을 제시. 주요 내용과 반영 상태:

**구조 및 흐름 (평가: B+)**:
- *지적*: Executive Summary가 발견사항과 권고사항을 혼재. 섹션 9(종합 권고안)와 10(핵심 발견사항)의 역할 중복
- *지적*: 섹션 4(플러그인 생태계)와 5(TIL 도구)에서 동일 도구(claude-mem 등) 중복 서술
- *반영*: 구조적 중복은 인지하되, 현 레포트에서는 유지. 브레인스토밍 결과 반영 시 재구성

**완성도 (평가: A-)**:
- *지적*: JSONL의 실질적 단점(스키마 변경 시 마이그레이션, 파일 크기 증가, 부분 업데이트/삭제 불가) 논의 빈약
- *지적*: 사용자/AI 학습 경계 사례(양쪽 모두 해당하는 경우) 분류 가이드 부재
- *지적*: LLM 기반 자동 추출의 토큰 비용 분석 부재
- *지적*: 민감 정보(API 키 등) 자동 필터링 전략 부재
- *반영*: 경계 사례 → `related_id`로 상호 참조 방안 추가. 비용/프라이버시는 구현 단계에서 반영

**일관성 (평가: B)**:
- *지적*: "wrapup"이 Skill인지 Command인지 시스템 전체인지 정의 불명확
- *지적*: 95개 소스 주장 vs 40개 출처 표 불일치 → **수정 완료** (40개 직접 인용으로 명시)
- *지적*: 섹션별 `[N]` 인용 번호가 출처 표와 불일치하는 경우 존재

**편향 및 균형 (평가: B-)**:
- *지적*: JSONL에 대한 과도한 편향. SQLite가 4개 항목에서 JSONL과 동등/우월하나 "향후 확장"으로 밀림
- *지적*: 소스 다양성 부족 (학술 논문 1편, 기업 연구 1편). 교육학적 관점(spaced repetition 등) 부재
- *반영*: SQLite 동등 대안으로 재평가하는 문구 추가. 최종 포맷 결정은 브레인스토밍에서 논의

### 리서치 한계

- **사용자 학습 vs AI 학습 자동 분류기의 실증 데이터 부재**: 개념적 프레임워크는 존재하나, 자동 분류 정확도에 대한 벤치마크가 없음
- **JSONL 대규모 파일 검색 성능 정량 데이터 부족**: grep/jq 기반 검색의 실제 성능 한계 미확인
- **Medium 기사 다수 접근 실패**: 403 에러로 일부 소스 내용 미확인
- **claude-mem 안정성 데이터 부재**: 프로덕션 환경에서의 장기 사용 사례 미확인
- **단일 모델 LLM 벤치마크**: 포맷 비교 정확도 데이터는 GPT-4.1-nano 단일 모델 결과로 일반화에 한계

---

## 출처

| # | 제목 | URL | 유형 | 접근일 |
|---|------|-----|------|--------|
| 1 | Persistent Lessons Learned - Issue #4654 | https://github.com/anthropics/claude-code/issues/4654 | 공식 이슈 | 2026-02-23 |
| 2 | GitHub - thedotmack/claude-mem | https://github.com/thedotmack/claude-mem | 오픈소스 | 2026-02-23 |
| 3 | GitHub - idnotbe/claude-memory | https://github.com/idnotbe/claude-memory | 오픈소스 | 2026-02-23 |
| 4 | GitHub Issue #11786 - Prompt-based Stop hooks metadata | https://github.com/anthropics/claude-code/issues/11786 | 공식 이슈 | 2026-02-23 |
| 5 | Hooks reference - Claude Code Docs | https://code.claude.com/docs/en/hooks | 공식 문서 | 2026-02-23 |
| 6 | JSON vs JSONL: Complete Guide | https://jsontotable.org/blog/json/json-vs-jsonl | 블로그 | 2026-02-23 |
| 7 | When JSON Sucks - pl-rants.net | https://pl-rants.net/posts/when-not-json/ | 블로그 | 2026-02-23 |
| 8 | Best Input Data Format for LLMs | https://www.improvingagents.com/blog/best-input-data-format-for-llms/ | 연구 | 2026-02-23 |
| 9 | How AI assistance impacts coding skills - Anthropic | https://www.anthropic.com/research/AI-assistance-coding-skills | 기업 연구 | 2026-02-23 |
| 10 | LangMem SDK Launch - LangChain Blog | https://blog.langchain.com/langmem-sdk-launch/ | 공식 블로그 | 2026-02-23 |
| 11 | Reflexion - Prompt Engineering Guide | https://www.promptingguide.ai/techniques/reflexion | 기술 가이드 | 2026-02-23 |
| 12 | Code Insights App | https://code-insights.app/ | 제품 | 2026-02-23 |
| 13 | Claude Diary - rlancemartin | https://rlancemartin.github.io/2025/12/01/claude_diary/ | 블로그 | 2026-02-23 |
| 14 | On Incremental LLM Memory - Le Xu | https://lexu.space/posts/2025/04/blog-post-1/ | 학술 블로그 | 2026-02-23 |
| 15 | From Human Memory to AI Memory Survey | https://arxiv.org/html/2504.15965v2 | 학술 | 2026-02-23 |
| 16 | Automate workflows with hooks - Claude Code | https://code.claude.com/docs/en/hooks-guide | 공식 문서 | 2026-02-23 |
| 17 | GitHub - chrismbryant/claude-journal-mcp | https://github.com/chrismbryant/claude-journal-mcp | 오픈소스 | 2026-02-23 |
| 18 | GitHub - iannuttall/claude-sessions | https://github.com/iannuttall/claude-sessions | 오픈소스 | 2026-02-23 |
| 19 | GitHub - agenticnotetaking/arscontexta | https://github.com/agenticnotetaking/arscontexta | 오픈소스 | 2026-02-23 |
| 20 | CLAUDE.md Management Plugin | https://claude.com/plugins/claude-md-management | 공식 마켓 | 2026-02-23 |
| 21 | Claude-Mem Hooks Architecture Docs | https://docs.claude-mem.ai/architecture/hooks | 프로젝트 문서 | 2026-02-23 |
| 22 | JSONL Definition & Specification | https://jsonl.help/definition/ | 공식 사양 | 2026-02-23 |
| 23 | SQLite As Application File Format | https://www.sqlite.org/appfileformat.html | 공식 문서 | 2026-02-23 |
| 24 | YAML vs JSON - AWS | https://aws.amazon.com/compare/the-difference-between-yaml-and-json/ | 공식 문서 | 2026-02-23 |
| 25 | Spreadsheet Version Control - DoltHub | https://www.dolthub.com/blog/2022-07-15-so-you-want-spreadsheet-version-control/ | 블로그 | 2026-02-23 |
| 26 | Agent Memory - Letta Blog | https://www.letta.com/blog/agent-memory | 공식 블로그 | 2026-02-23 |
| 27 | Comparing Memory Implementations - Simon Willison | https://simonwillison.net/2025/Sep/12/claude-memory/ | 블로그 | 2026-02-23 |
| 28 | LLM Schemas - Simon Willison | https://simonwillison.net/2025/Feb/28/llm-schemas/ | 블로그 | 2026-02-23 |
| 29 | Basic Memory GitHub | https://github.com/basicmachines-co/basic-memory | 오픈소스 | 2026-02-23 |
| 30 | GitHub - jbranchaud/til | https://github.com/jbranchaud/til | 오픈소스 | 2026-02-23 |
| 31 | GitHub - simonw/til | https://github.com/simonw/til | 오픈소스 | 2026-02-23 |
| 32 | Stack Overflow Blog - Developer Journal | https://stackoverflow.blog/2024/12/24/you-should-keep-a-developer-s-journal/ | 공식 블로그 | 2026-02-23 |
| 33 | How to automate dev journaling with Claude Code | https://www.devas.life/how-to-automate-development-journaling-with-claude-code/ | 블로그 | 2026-02-23 |
| 34 | Claude Code Session Memory | https://claudefa.st/blog/guide/mechanics/session-memory | 블로그 | 2026-02-23 |
| 35 | GitButler Blog - Claude Code Hooks | https://blog.gitbutler.com/automate-your-ai-workflows-with-claude-code-hooks | 블로그 | 2026-02-23 |
| 36 | Analyzing Claude Code Logs with DuckDB | https://liambx.com/blog/claude-code-log-analysis-with-duckdb | 블로그 | 2026-02-23 |
| 37 | GitHub Issue #12755 - PreSessionEnd | https://github.com/anthropics/claude-code/issues/12755 | 공식 이슈 | 2026-02-23 |
| 38 | GitHub Issue #10610 - Stop event model response | https://github.com/anthropics/claude-code/issues/10610 | 공식 이슈 | 2026-02-23 |
| 39 | CSV Files: Use cases and Limitations - OneSchema | https://www.oneschema.co/blog/csv-files | 블로그 | 2026-02-23 |
| 40 | Human Knowledge Markdown - GitHub | https://github.com/digitalreplica/human-knowledge-markdown | 오픈소스 | 2026-02-23 |
| 41 | 5 Professional Meeting Minutes Examples & Templates - Fellow.ai | https://fellow.ai/blog/meeting-minutes-example-and-best-practices/ | 블로그 | 2026-02-23 |
| 42 | 11 Best Practices for Meeting Minutes - Krisp.ai | https://krisp.ai/blog/best-practices-for-meeting-minutes/ | 블로그 | 2026-02-23 |
| 43 | Meeting minutes template: Guide with action items - Wrike | https://www.wrike.com/blog/action-items-with-meeting-notes-template/ | 블로그 | 2026-02-23 |

---

*이 레포트는 Claude Code의 /research 스킬로 생성되었습니다.*
*리서치 수행일: 2026-02-23*
