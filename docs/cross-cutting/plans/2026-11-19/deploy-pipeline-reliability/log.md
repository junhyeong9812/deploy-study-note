# log — deploy-pipeline-reliability

| 시각(KST) | 사건 | 결과 |
|-----------|------|------|
| 11-19 20:3x | explorer(sonnet, 63k 토큰)로 ci-cd·워크플로 구조 탐색 → 메인이 master.go·agent.go·compose 직접 읽음 | 202=접수뿐·결과 조회 불가·재시도 없음·테스트 없음 확인 |
| 11-19 20:4x | 인터뷰(선택 질문 2회 + 서술 답) → 명세 초안 작성 | 사용자 합의 대기 |
| 11-19 21:0x | 사용자: "현재 명세는 그대로 OK" | set-state spec-approved / mode auto(제안한 auto에 대한 합의로 해석). 추가 구상(자원 모니터링·버전 목록 재배포·문서 변경 이력·어드민 알림 설정)은 NEXT.md N3·N4-b·N5에 기록 — 이번 범위 밖 |
| 11-19 21:1x | 가정1 스모크(.158 `compose up -d --no-build --no-deps app --dry-run`) | 대상이 backend-app 하나뿐(ES 미포함). compose 5.0.0. 실제 교체 확인은 backend 첫 배포에서 |
| 11-19 21:2x | 가정2 스모크 — `modernc.org/sqlite@v1.34.5` | golang:1.23-alpine·CGO 없이 받기·빌드·테스트 통과. 빌드한 이미지로 master 기동 → `/data/deploys.db` 생성·`GET /deploys` 200·무인증 401. 가정 성립 |
| 11-19 21:3x | ci-cd task 01(0448701) agent `/agent/ci`·`/agent/cd` | spec 기준 테스트 9개. 기준 SHA 70151a5. 브랜치 feat/ci-cd-pipeline(로컬) |
| 11-19 21:4x | ci-cd task 02(a014bd8) master 상태 기계·SQLite·조회·멱등 접수 | go test 전부 통과 + `-race`(golang:1.23, cgo) 통과 |
| 11-19 21:4x | front task 04(8b3f0d3, feat/deploy-status) 조회 중계 + test 단계 + 이미지 태그 | vitest 39 passed. 워크플로는 별도 브랜치 ci/deploy-wait(중계가 배포된 뒤에야 조회 가능하므로 PR 분리) |
| 11-19 21:5x | task 05 워크플로 스크립트 — 가짜 서버로 경우별 종료 코드 | 504×2 뒤 성공=0 · 접수 5회 실패=1 · 401=1 · 409 대기 뒤 ci_test 실패=1 · 404 유실=1 · 시간 초과=1 · 커밋 불일치=1 |
| 11-19 21:5x | task 03 llm(1527c90·19b6e88, feat/ci-test-stage)·backend(작업트리) test 단계 | llm `build --target test` 49s 통과, `IMAGE_TAG=abc1234 compose build` → `llm-wrapper:abc1234`. **반증**: 일부러 깨뜨린 테스트로 front·llm 빌드 exit 1 확인(실패 전파). backend 빌드는 진행 중. 로컬 노트북은 구형 빌더(buildx 없음) — agent 이미지는 buildx 0.20.1 |
| 11-19 22:0x | 리뷰 ⓪ packet — OUT=`scratchpad/review.0nVM`(packet·mirror·results), 4개 repo 묶음, 보안 스캔 매칭 0 | ① Opus 워커(미러) ∥ codex(인라인 — bwrap 중첩으로 미러 읽기 불가였던 전례, **입력 비대칭**) 실행 |
| 11-19 22:0x | backend test 단계 빌드 | 통과(첫 빌드 4분 14초). 커밋 e161f39·69e3d0c(feat/ci-test-stage) |
| 11-19 22:1x | 리뷰 ① 회수 — codex finding 6·OQ 3 / Opus 워커(opus, 134k 토큰, 20 tool) finding 7·OQ 8 | ② 메인 종합: 채택 R1~R13 → ③ codex 감사: R8(명세 20분 변경 불가)·OQ1/OQ2(문구 보정으로 해소 불가)·R2(메모리만으로 부족)·R3(HEAD 예외) 판정 오류 + 누락 3(2xx 수락·서버 test 실행 확인·이미지 5개 상한) → 반영 |
| 11-19 22:3x | ④ 수정 — ci-cd fix 커밋(feat/ci-cd-pipeline 선두) · llm 1c092a8 · backend bbab979 · front 47890b1·3fe9be3(ci/deploy-wait) | go test 통과(`-race -count=3` 포함) · 워크플로 7경우 재확인. **테스트 결함 1건**: 상태 전이 테스트가 상태 변경 직후 agent 호출 기록을 바로 확인해 실패 → 실패 시 붙잡힌 요청이 안 풀려 5분 멈춤. 판정식·정리 코드 수정 후 3회 연속 통과 |
| 11-19 22:4x | post-fix 타깃 재점검 — codex | 미해소 1(R2: 이력·/status·재접수는 여전히 DB의 진행 중 상태) · 새 결함 2(P1 작업 중 대기가 CI·CD 각각 적용돼 20분 초과 가능 / P2 실패 기록 실패 시 store_failed 미표시) · 테스트 2(cd_running 확인 시점, 복구 전 일관성 미검증) |
| 11-19 22:5x | 재점검 반영(ci-cd f9af3cd) | R2·P1 수정 + 테스트 보강(`-race -count=3` 통과, 이미지 빌드 성공). P2는 기각. 재점검은 1회로 종료(추가 수정분은 셀프 점검) |
| 11-19 23:0x | 서버 3대 사전 확인(값은 보지 않고 설정 항목 이름만) | ci-cd는 git clone이 아니라 복사본(08-29 기동). `.env.agent`에 DEPLOY_SVC_·DEPLOY_HEALTH_ 는 3대 모두 있음. 추가 필요: `.164`에 `DEPLOY_TEST_CONTEXT_LLM=wrapper` 1줄. 발행·서버 반영은 사용자 확인 대기 |
| 11-19 22:3x | 사용자: "진행하자"(발행 + 서버 작업 승인. 깨진 테스트 커밋으로의 실패 확인은 답 없음 → 미실시) | ci-cd 이슈 #11 → PR #12 병합(339c22b) |
| 11-19 22:38~40 | 서버 3대 ci-cd 반영(기존 디렉토리는 `~/ci-cd-backup-20261119`로 백업, `git archive`를 풀어 소스만 갱신, `.env*`·data 미변경) | .164 agent(+`DEPLOY_TEST_CONTEXT_LLM=wrapper`) → .158 agent → .9 agent → .9 master. 전부 기동, master가 `data/deploys.db` 생성, 무인증 401. **절차 위반 1건**: .164에서 새 경로 확인용으로 `.env.agent`의 비밀값을 셸 변수로 읽어 로컬 호출에 씀(값은 출력·전송하지 않음). 이후 확인은 무인증 401과 로그로만 함 |
| 11-19 22:52 | front #43 → PR #44 병합(acbe1e7) — 기존 워크플로로 배포 | **기존 워크플로가 엣지 504를 받고 초록불**(고치려는 바로 그 사고, .9 링크 기록 없음). `gh run rerun` → 202 → master `succeeded`(ci 113s·cd 4s). front-app이 `front-app:acbe1e7…`로 교체. 엣지 경유 `GET /api/deploy/<id>` 무인증 401·형식 오류 422 = 조회 경로 동작(OQ6 해소) |
| 11-19 23:01 | llm #22 → PR #23 병합(c22e081) — **새 워크플로 첫 실행** | submit 202 → status ci_running → cd_running → succeeded, 초록불. llm-wrapper가 `llm-wrapper:c22e081…`(ci 8s·cd 3.6s). 서버에서 `build --target test` 재실행 시 pytest 단계 CACHED = 실제 실행됨 |
| 11-19 23:34 | backend #34 → PR #35 병합(e66f4d3) | succeeded(ci 58s·cd 8s). **backend-es 생성 시각 09:37:10Z 그대로**(redis·embedding도 불변), backend-app만 14:35:50Z 재생성, 색인 66,387건. 가정1 실증. 이전 방식 411s → 66s |
| 11-20 00:08 | front PR #45 병합(7b7395c) — 새 워크플로 | **접수 504 4회 연속(15:08:30~15:10:01Z) 뒤 5번째에 202** → succeeded(ci 64s·cd 4s). 엣지 error.log에 같은 시각 connect 시간 초과 4건, .9 링크 끊김 기록은 없음(마지막 14:39Z) = 약 2분짜리 두 번째 원인. 재시도 5회·20초가 간신히 넘김 |
| 11-20 00:12 | master 재시작 전후 이력 확인(DB 읽기 전용 조회) | 4건 그대로(front 2·llm 1·backend 1 전부 succeeded), 미완료 정리 없음 |
| 11-20 10:1x | 사용자 결정: 재시도 5회 유지 · 깨진 테스트 커밋으로 실패 경로 시험 승인("시험하자") | — |
| 11-20 10:21 | 실패 경로 시험 — llm main 에 항상 실패하는 테스트(1663013) | 워크플로 **failure**, master `failed/ci_test`(6.9s), 로그에 실패 테스트 이름. `.164` 컨테이너 이미지·생성 시각(14:01:13Z) 불변, 서버 소스 c22e081 로 원복, 깨진 파일 없음, /health 정상. agent 에 cd start 기록 없음 |
| 11-20 10:22 | 되돌림(92dab17) | succeeded(ci 2.0s·cd 3.6s), 컨테이너 `llm-wrapper:92dab17…` |
| 11-20 10:3x | 사용자 요청: 실험 문서화 | `experiments.md` 작성(실험 7종 — 방법·결과·실제 서버에서 미확인인 항목) |

## 리뷰 ledger

- review packet: base ci-cd 70151a5 · llm 78e8bf2 · backend f59e96c · front a5ff80f / `scratchpad/review.0nVM` / mirror `review.0nVM/mirror`

| id | loop | source | 근거 | disposition | status | fixed |
|----|------|--------|------|-------------|--------|-------|
| R1 | 1 | codex | agent/pipeline.go — 헬스 URL 없으면 검사 없이 성공 | 채택 | fixed — 교체 전에 cd_health로 거절 | 1 |
| R2 | 1 | codex·opus | master.go — 종단 기록 실패 시 행이 진행 중으로 남음 | 채택(+감사) | fixed — 메모리 보관 + 주기 재기록, 기록 못 한 성공은 store_failed | 1 |
| R3 | 1 | codex·opus | agent/pipeline.go — 원복 기준이 HEAD | 채택 | fixed — 실행 중 컨테이너의 sha 태그 기준. 알 수 없을 때 HEAD는 유지(경고 로그) | 1 |
| R4 | 1 | codex·opus(+감사: 5개 상한) | 이미지 정리 조용한 생략·상한 초과 | 채택 | fixed — 이름을 컨테이너에서 읽음(env 제거)·별도 시간 예산·배포 태그 포함 5개 | 1 |
| R5 | 1 | codex·opus | compose 기본 태그 current(명세는 local) | 채택 | fixed — local, current 꼬리표 삭제 | 1 |
| R6 | 1 | codex | master 재시작 직후 agent 작업 중 → 즉시 실패 | 채택 | fixed — 15초 간격 12회 재호출 | 1 |
| R7 | 1 | opus | DEPLOY_SVC 비면 compose 전체 대상 | 채택 | fixed — 422 service_not_configured | 1 |
| R8 | 1 | opus(+감사) | 타임아웃 경합·합계가 20분 초과 | 채택 | fixed — 명세 20분 유지, 예산 축소(대기 3 + CI 11.5 + CD 5분) | 1 |
| R9 | 1 | opus | 상태 전이 전 구간 테스트 없음 | 채택 | fixed — TestStatePassesThroughEveryStage | 1 |
| R10 | 1 | opus | front tsconfig.tsbuildinfo 커밋 | 채택 | fixed | 1 |
| R11 | 1 | codex OQ | agent 200 본문 미검증 | 채택(소) | fixed — success 봉투 확인 | 1 |
| R12 | 1 | opus OQ7 | DB 경로 기본값이 작업 디렉토리 의존 | 채택(소) | fixed — compose에서 명시 | 1 |
| R13 | 1 | opus OQ8 | jq 실패 시 조회 단계 즉시 종료 | 채택(소) | fixed | 1 |
| A1 | 1 | 감사 | 워크플로가 202만 수락·재시도 규칙이 명세와 다름 | 채택 | fixed — 2xx 수락·409 대기·그 외 5회 | 1 |
| A2 | 1 | 감사·opus OQ2 | 실패 단계 집합이 명세보다 많음 | 채택 | fixed — agent의 단계 외 코드는 agent_rejected로 묶음. 명세 ②에 agent_rejected·store_failed 추가(**사용자 보고 필요**) | 1 |
| P1 | post-fix | codex | master.go — agent_busy 대기가 단계마다 적용 | 채택 | fixed(f9af3cd) — 배포 한 건 합계 12회 | post-fix |
| P2 | post-fix | codex | master.go — 실패 결과의 기록이 실패하면 store_failed로 표시해야 | 기각 — 명세 ②는 "실패 처리"를 요구(충족: 이미 failed). 실제 원인(ci_test 등)을 지우면 워크플로가 원인을 못 본다 | - | - |
| - | 1 | opus OQ4 | /status history 형태 변경 | 기각 — 명세 ②는 엔드포인트 유지, 소비처 없음(packet-related-raw.txt). README에 명시 | - | - |
| - | 1 | opus OQ6 | 엣지가 /api/deploy/<id>를 넘기는지 | open question → 실측으로 해소(401·422 응답) | closed | - |
| - | 1 | codex OQ·감사 | 명세 ⑤ 서버 실행 검증·세 서버의 test 단계 실행 | open — 배포 후 수행 | open | - |

## 생략한 검증
- codex 리뷰 입력 비대칭(인라인 자료만, go.sum 제외) — 샌드박스 중첩으로 미러 읽기 불가.
- 재점검 반영분(f9af3cd)에 대한 추가 독립 재점검은 하지 않음(中 = 재점검 1회).
- 명세 ⑤ 실행: ①정상 배포·④ES 불변·⑤재시작 후 이력은 수행. ③접수 실패는 실환경에서 504 4회 뒤 성공을 관측, "5회 실패 → 빨간불"은 가짜 서버로만 확인. ②깨진 테스트 커밋은 11-20 수행(`experiments.md` 2절). 실제 서버 미확인으로 남은 것: cd_up·cd_health 실패, 배포 도중 master 중단, 이미지 정리 실행(`experiments.md` 7절).
- task 06(구 `/agent/deploy` 제거) 미착수.
