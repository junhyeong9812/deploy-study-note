# log — 이슈1: cs·workflow 지식을 study-note로 이전

## 진행 기록 (발생 시점 append)

- 2026-09-23 | 명세 합의(auto) + set-state spec-approved·mode auto | SPEC=1·MODE=auto·DEBT=0
- 2026-09-23 | 가정① 실증(착수 직후) | TreeBuilder.build(paths)가 폴더 경로만으로 트리 생성 — 최상위 탭 하드코딩 없음. front page.tsx는 백엔드 트리 그대로 렌더. → 새 최상위 `workflow/` 자동 노출 확인
- 2026-09-23 | 시크릿 스캔(이전 전·후 2회) | 매치는 헤더 이름(X-Bridge-Secret 등)뿐, 값·IP 없음 — 클린
- 2026-09-23 | workflow 7개 cp 이관 | study-note/workflow/ (바이트 동일)
- 2026-09-23 | semaphore·resp-protocol 1/2/3 승격 | cs/systems/ 하위, 기존 리프 헤더 포맷·Claude 초안 표시 준수
- 2026-09-23 | backoff 병합 | cs/ops-patterns/01-retry-backoff/3-answer.md 끝에 「실사용 사례」절 append (기존 Q/A 1:1 구조 무손상)
- 2026-09-23 | 원본 삭제 | deploy-study-note/docs/cs/·workflow/ 제거, process 문서(plans·secrets·TODO·logging.md) 잔존
- 2026-09-23 | 커밋 | 브랜치 docs/migrate-cs-workflow-from-deploy · a8292f1 · 14파일만(무관 WIP 85건 미스테이징) · AI attribution 없음(사용자 규칙)

## 리뷰 ledger

- 셀프 리뷰(diff self-review): 스테이징이 의도한 4경로뿐인지 `git status`로 확인 — OK(무관 WIP 85건 제외됨).
- 산출물 유형 판정: 실행물 아님(순수 문서·이관+study 콘텐츠). 실효 stakes 낮음~중간 — 트리 렌더 표면은 가정① 실증으로 닫음. codex 듀얼 리뷰는 실행물/설계문서가 아니어서 부적용, 셀프체크+스모크로 비례.

## 최소 안전선 점검

- ① 스모크: 이관 파일 존재·구조·backoff 절 삽입 확인 — OK
- ② 불변식: 기존 리프 훼손 없음(backoff는 append만), process 문서 잔존 — OK
- ③ diff self-review: 4경로만 커밋 — OK
- ④ rollback: 브랜치 커밋이라 되돌리기 쉬움(main 미변경)
- ⑤ public contract: 문서 전용 — API/스키마 영향 없음. 단 새 최상위 `workflow/`는 **머지→sync 리인덱스 시** 위키 사이드바 최상위 탭에 노출(트리 파생) — is_subject=true 주제 리프로 렌더
- ⑥ 반증: 시크릿 재유입 없음(스캔 2회), workflow/ 정렬 흔듦 없음(이름순 삽입)

## 생략한 검증 (빚 아님 — 사후 육안)

- **위키 실제 렌더 확인**: workflow/ 최상위 탭·드릴다운·1/2/3 탭 렌더는 study-note **main 머지 + Actions sync 리인덱스 후**에만 가능. 머지는 사용자 결정 사항이므로 그 시점 육안 확인 대기(코드 변경 없이 자동 노출됨을 가정①로 실증했으므로 빚이 아닌 확인 절차).

- 2026-09-23 | logging.md 추가 이관 | 사용자 지시로 workflow/logging.md 이관 + README 등재, 원본 삭제 (2번째 커밋 13c5e96)
- 2026-09-23 | ⚠️ 동시성 이벤트 | 작업 중 사용자가 같은 study-note 작업트리에서 react hydration 7커밋을 동시 진행 → 공유 HEAD/브랜치라 임시 브랜치에 함께 쌓임. main ff 정리로 전부 선형 반영(a8292f1 보존 확인, 손실 없음). 교훈: 한 repo 동시 커밋 세션은 git 얽힘 유발 — 이후 study-note git 미조작.
- 2026-09-23 | 커밋을 main으로 정리 | 사용자 "한 번에 push" 방침에 맞춰 격리 브랜치 대신 main 반영, 임시 브랜치 삭제. push는 사용자 몫.

## 완료

- **이슈1 완료** (커밋=마무리, 사용자 별도 push). 산출: cs/systems/semaphore·resp-protocol(1/2/3), ops-patterns/01-retry-backoff(실사용 사례 병합), workflow/ 7+logging.md. deploy docs 원본 삭제. 시크릿 0.
- 위키 실제 렌더 확인은 사용자 push→리인덱스 후 사용자 몫(가정①로 자동 노출 실증됨).

## 후속

- 작업2: 이번 배포 이슈들을 CS 패턴으로 추상화해 `cs/issue/` 아카이브 — **별도 작업 폴더**(신규 명세).
- 이슈2(결정문서 신규 작성 — BFF 패스스루·쿠키 3금기 등)도 별도 — 작업2와 통합할지 사용자 확인.
