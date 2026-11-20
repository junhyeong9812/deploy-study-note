# log — history 다중-post 리스트업 (A 프론트 + B 폴더규약)

## 진행 기록

- 2026-10-01 | 근본원인 실증 | page.tsx:39-41 docsByKind=Map<doc_kind> → 다중 post 덮어써짐. page.tsx:48-55 else 분기가 doc경로(`<path>.md`) 렌더 → A 목록링크 동작 가능
- 2026-10-01 | 명세 합의(auto, A+B) + set-state | SPEC=1
- 2026-10-01 | A 구현 | WikiView.tsx SubjectView !isChapter에 다중 content-post→목록 분기 추가(chapter·단일 불변)
- 2026-10-01 | A 검증 | tsc: WikiView 타입클린(에러는 기존 tree.test.ts prev누락 2건 — e07402f도 가진 채 배포성공 → next build가 test파일 미차단, 내 배포 안전). vitest 6 pass(Node20; Node18은 styleText로 기동실패)
- 2026-10-01 | A 리뷰 | packet BASE=e07402f, codex(인라인 bg)∥Opus 워커(a06cbcdb…) — 회수 중
- 2026-10-01 | B 실행 | study-note `git mv` 83개 → <name>/post.md (README·접두 유지). ⚠️ 브랜치가 main 아닌 `docs/db-writing`(사용자 동시작업) — history/만 격리 스테이징(사용자 cs/ WIP 57개 무겹침 확인) → 선택 커밋 d8b9653b. push는 사용자 몫
- 2026-10-01 | 동시조작 관측 | study-note=docs/db-writing·front repo도 HEAD 깜빡임(24bbca6↔e07402f) — 브랜치 조작 회피·선택 커밋 원칙 유지([[studynote-concurrent-git]])

## 리뷰 ledger (A — 듀얼 1패스)

- codex(인라인): PLAUSIBLE 1 — WikiView 목록조건이 readme/index만 제외라 spec "post"보다 넓음. 단 !isChapter 리프에서 non-readme/index kind는 DocClassifier상 post뿐이라 실현성 확인 필요(Opus 대기).
- Opus 워커: 회수 중.

## 리뷰 ledger (A — 듀얼 1패스, 종결)

- codex(인라인): PLAUSIBLE 1(목록조건 post보다 넓음) → DocClassifier(README→readme·index→index·나머지→post) 상 !isChapter 리프의 non-readme/index=post → **실현 안 됨, 기각**.
- Opus 워커(미러): 차단 결함 0, spec 불변식 5개 verified. open question 3: ①page.tsx 낭비 fetch(A범위 밖→NEXT) ②index 드롭(spec 합치·현재 데이터 없음→NEXT 관찰) ③README 판별(DocClassifier 확인→비이슈).
- **채택 finding 0 → 수정 없음, 종료 clean.**

## A 배포·검증 (2026-10-01)

- 이슈 #27 → 브랜치 fix/multipost-listup-27 커밋 d381b7a → PR #28 머지(main 1f28c14). 배포 run 36796378629.
- **라이브 확인**(front 재빌드 ~1분 후): `/wiki/history/java` 29개 항목 목록 렌더 ✓ · `java-11`·`99-그-뒤`(한글) 문서 200 ✓ · **workflow 7개 흐름문서도 목록화**(A가 다른 다중-post 리프도 해결) ✓.

## 완료 / 남은 것

- **A 완료**(배포·검증). **B 완료**(커밋 d8b9653b, study-note docs/db-writing — 사용자 push 몫).
- B 반영 검증: 사용자 push 후 **full 재색인** 시 history/<lang> 폴더 드릴다운화 + 구 평면경로 orphan 제거. Task A(denylist) 재색인과 **1회로** 처리.
- NEXT 후보: page.tsx 낭비 fetch 최적화 · workflow·reference/writing 폴더규약화 · index 드롭 대비.
