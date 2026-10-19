# 채움 자료

긴 컨텍스트 조건에서 컨텍스트를 키우기 위해 에이전트가 읽는 자료. 작업(요청 3개)과는 관련 없는 실제 개발 문서·코드다.

## 구성

| 항목 | 값 |
|---|---|
| 출처 | 공개 저장소 8개 (`rubilisa08/`): Saju_Tarot, calorie-tracker, finance-rag-chatbot, my-service-agent, my_open_space, pose-image-tool, quest_PoC, to-do-list |
| 파일 수 | 158개 (md, ts, tsx, py, js, css, html, sql, json 등) |
| 분량 | part-01 ~ part-13 (각 약 110KB, 합계 약 1.2MB) |
| 추정 토큰 | 약 35만 ~ 50만 (한글 비중이 커서 범위가 넓음). 실제 값은 실행 시 응답의 `usage`로 확인한다. |
| 파일 형식 | 각 part는 `===== 저장소/경로 =====` 헤더 뒤에 파일 내용이 이어짐 |

## 제외한 파일

민감정보 패턴(API 키, JWT, 이메일, supabase 프로젝트 URL, 비밀번호 대입 등)에 걸린 9개 파일은 넣지 않았다.

- Saju_Tarot: `backend/tests/test_scaffold.py`, `frontend/index.html`
- calorie-tracker: `PRD.md`, `supabaseClient.js`
- finance-rag-chatbot: `app/index.html`, `app/src/rag.ts`
- my_open_space: `index.html`
- to-do-list: `config.js`, `docs/PRD.md`

## 검사 결과

- 만든 뒤 별도 패턴(키, JWT, 이메일, 비밀번호·토큰 대입)으로 한 번 더 검사했고 해당 사항이 없었다.
- `supabase.co`는 자리표시자(`xxxxx.supabase.co`)와 안내 링크만 남아 있다.
- 패턴 검사이므로 모든 민감정보가 없다는 보증은 아니다. 공개 저장소에서 가져온 자료다.

## 한계

- 작업과 무관한 자료라서, 원 사례처럼 작업 중에 쌓인 도구 출력으로 커진 컨텍스트와는 다르다.
- 토큰 수는 추정치다.
