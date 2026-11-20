# measurement-log
| 날짜 | 작업 | stakes | 리뷰 | 워커 모델 | 결과 |
|---|---|---|---|---|---|
| 2026-08-24 | llm wrapper 구현(이슈3·PR3) | 중간 | 듀얼1패스(Opus∥codex)+감사+재점검 | opus·codex(medium) | 테스트25·스모크 통과, 실결함 1(thinking 폭주) 스모크에서 검출 |
| 2026-08-24 | llm 응답정규화+문서화(이슈1·PR2) | 낮음~중간 | 셀프체크+테스트 | — | 28건 green·스모크 통과. study-note 이슈기록 체계 신설 |
| 2026-08-24 | backend 1차(이슈5·PR5) | 중간 | 듀얼1패스+감사+재점검 | opus·codex(medium) | 테스트22·full색인 950청크·실기동 결함 9건 검출(리뷰6+실측3) |
| 2026-08-25 | study-note 재구조화·증분 sync 실검증·backend 이슈 문서 5건 | 낮음 | 셀프체크 | — | 증분 경로 실증(1224/796·6/35) |
| 2026-08-28 | front 1차(이슈4·PR5) | 중간 | codex1회+셀프(사유기록) | codex(medium) | vitest6·E2E 관통(push-Actions-색인) |
| 2026-08-28 | 도메인-우선/features 재편(이슈2·PR3) | 낮음 | 셀프체크(동작보존·실기동) | — | backend 24·front 6 green, 계약 diff 0 |
| 2026-08-29 | ci-cd 1차(이슈4·PR2+연계PR3) | 중간~높음 | go test9+E2E (codex 리뷰 예정) | — | E2E 관통·실결함4 실기동 검출 |
| 2026-08-29 | ci-cd 완결(Actions 3리포·codex 반영·E2E 3서비스) | 중간~높음 | codex1회+go test10+실E2E | codex(medium) | 채택6·기각2(오탐)·이연1, F7 헬스가 실제 오배포 검출 |
| 2026-09-01 | 레이아웃·자동완성·prev·suggest 라운드(이슈6·PR6) | 중간 | 셀프체크+실기동·엣지 | — | 배포401 실사고 검출, portfolio 재구조화 |
| 2026-09-01 | 채팅 4이슈+리뷰(llm/backend/front/bridge) | 중간~높음 | codex1회+실E2E | codex(medium) | 채택7(브리지보안)·기각1(packet오탐), 스트림·세션·에스컬레이션 관통 |
| 2026-09-23 | cs·workflow 지식 study-note 이관(작업1) | 중간 | 셀프체크+스모크(파일·구조·시크릿) | — | semaphore·resp 1/2/3 승격·backoff 병합·workflow 8건 이관, deploy docs 원본 삭제. 동시성 이벤트(사용자 react 병행커밋) 손실없이 정리 |
| 2026-09-23 | cs/issue 패턴 아카이브 Phase1 cross-cutting(작업2) | 중간 | 셀프+스모크(구조·링크·시크릿·커버리지)+워커결과 교차확인 | opus 워커 3(reliability/network/infra 병렬) | 12패턴 36파일+가이드+README6, 19이슈 커버, 커밋 c9a8768. 동시성 인터리브는 파일선작성·단일커밋으로 회피 |
| 2026-09-24 | cs/issue 아카이브 Phase2 언어버킷(작업2) | 중간 | 셀프+스모크(구조·전깊이링크·시크릿·커버리지)+워커 교차확인 | opus 워커 3(kotlin/typescript/python 병렬) | 14패턴 50파일, 누적 26패턴. 커밋 dcfbe72. 워커 파일작성·메인 README/커밋 단일화로 동시성 회피 |
| 2026-10-01 | 트리/색인 denylist(docs·templates 완전제외, 작업A) | 중간 | 듀얼1패스(codex 인라인 ∥ Opus 미러)+PathGuardTest+라이브검증 | opus 워커·codex(medium, bwrap로 인라인) | 28 tests·finding0. 이슈#30·PR#31 머지·배포, 라이브 트리/doc 필터 확인. full 재색인은 시크릿 필요로 사용자 대기 |
| 2026-10-01 | history 다중-post 리스트업(A 프론트+B 폴더규약) | 중간 | 듀얼1패스(codex 인라인∥Opus 미러)+tsc+vitest6+라이브 | opus 워커·codex(medium) | A: SubjectView 목록렌더, 이슈#27·PR#28 배포, 라이브 history/java 29항목·workflow 7항목 목록 확인. B: history 83개 폴더/post.md 커밋(d8b9653b, 사용자 push). finding0 |
| 2026-10-01 | 컨텐츠 분할 2-pane 리더(front) | 중간 | Opus 적대적 1패스(codex 사용량한도 user-override)+vitest12+next build+라이브 | opus 워커 | paneStack+ClientMarkdown+PaneReader+/api/doc BFF, 이슈#29·PR#30 배포. Opus finding 7→6수정(전폭·모바일·fetch·에러재시도·폴더폴백·토글). SSR 렌더 확인 |
| 2026-10-01 | subject 페이지 fetch 최적화(front, #3-a) | 중간 | Opus 적대적 1패스+vitest12+next build | opus 워커 | 다중목록 N fetch→README만. 이슈#31·PR#32 배포. F1(README-only 리프 비동등) 수정. 렌더 동등 |
| 2026-10-01 | workflow·reference 폴더규약화(#3-b) | 낮음~중간 | 셀프+구조검증+링크분석(resolveHref) | — | git mv 17개 → post.md, 커밋 5c741169(사용자 push). 링크 재작성 불필요(URL 안정) |
| 2026-10-04 | 반응형 1단계: 토큰+다크모드 토글+죽은코드(front) | 중간 | 듀얼1패스(codex 인라인 ∥ Opus)+vitest14+build+라이브 | opus 워커·codex(medium) | codex 범위 finding 1·Opus 경미 3 반영, 차단0. 이슈#33·PR#34 배포. 화면확인 대기 |
| 2026-10-04 | 반응형 2단계: LayoutShell+트리/챗 토글+단축키(front) | 중간 | 듀얼1패스(codex∥Opus)+post-fix 재점검(codex)+vitest21+build+라이브 | opus 워커·codex(medium) | 채택 7 + 재점검 1(모바일 닫기버튼, 기존결함) 반영. 이슈#35·PR#36 배포. 화면확인 대기 |
| 2026-10-04 | 반응형 3단계: 드로어(햄버거)+모바일 챗 시트(front) | 중간 | 듀얼1패스(codex∥Opus)+post-fix 재점검 clean+vitest22+build+라이브 | opus 워커·codex(medium) | 채택 6 반영, 범위 이탈 1(헤더·nav 조기 이전 — 사후 확인 요청). 이슈#37·PR#38 배포 |
| 2026-10-06 | 반응형 4단계: 리더 CSS 미디어쿼리+본문 폭 토큰(front) | 중간 | 듀얼1패스(codex∥Opus)+vitest22+build+라이브 | opus 워커·codex(medium) | 차단0, 기록 정정·설계 정본 동기화. 모바일 링크 push 정정. 이슈#39·PR#40 배포 |
| 2026-10-06 | 반응형 4단계 배포 사고 대응(엣지 504 silent green) | 중간 | run 로그·master/agent 로그·라이브 대조 | — | 재실행으로 반영 확인. 4개 워크플로 실패 미검출·agent 좀비 14 발견 → 별도 작업 제안 |
| 2026-11-19 | 채팅 대기열 표시+가상 스레드(llm·backend·front, PR #19·#21·#33·#42) | 중간 | 듀얼1패스(Opus∥codex 인라인)+감사+재점검 4회+라이브 E2E | opus 워커 127k·codex(medium) | 채택 14+재점검 3. 배포 후 E2E에서 결함 1(연결 끊김 미감지) 검출·수정. 화면 확인·구 경로 정리 미완 |
| 2026-11-20 | 배포 신뢰성: CI/CD 분리·상태 조회·이력 DB(ci-cd·llm·backend·front, PR #12·#23·#35·#44·#45) | 중간 | 듀얼1패스(Opus∥codex 인라인)+감사+재점검 1회+실서버 실험 7종 | explorer sonnet 63k·opus 134k+99k·codex(medium) | 채택 15+재점검 2(기각 1). 실패 경로 실서버 확인. 절차 위반 2(서버·로컬 비밀값 파일 읽기). 구 경로 제거 미완 |
| 2026-11-20 | 무중단 배포: blue/green + 서버별 nginx + llm 대기열 인계(ci-cd·backend·front·llm, PR 9건) | 높음 | 설계 선검증 + blind 테스트 + 듀얼 루프 3회(02·03) + 듀얼 1회·재점검(04·05) + 로컬 통합 실험 + 서버 실측 14종 | opus 91k(blind)+612k(리뷰 4회)·codex(medium) 8회 | 채택 38(선검증 5·루프 24+2·04/05 8·실측 1). 매 루프 신규 채택 — 상한 종료. 서버 실측이 리뷰가 놓친 결함 1건 검출. 배포 중 요청 실패 0건, 실제 채팅 12/12 완료. 서버 재부팅·되돌림 서버 실측 미완 |
