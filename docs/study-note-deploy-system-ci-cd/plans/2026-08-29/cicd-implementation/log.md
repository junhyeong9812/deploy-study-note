# log — cicd-implementation
| 시각 | 사건 | 결과 |
|---|---|---|
| 2026-08-29 | 명세(사용자: MODE 전환 구조 확정, 4미결은 위임 확정) | 착수 |
| 2026-08-29 | 이슈①~③(PR #5)·④(PR #6) 머지 | Go 단일 바이너리(MODE)·HMAC fail-closed·RESP XADD 로거·allowlist·태그 정규식·single-flight — go test 9건 |
| 2026-08-29 | 실기동 결함 4건 검출·수정 | ①전체 compose pull이 ollama GB 이미지로 4분 타임아웃→대상 서비스 한정(DEPLOY_SVC_*) ②image+build 병존 시 pull 스킵("No image to be pulled")→llm build 제거(PR llm#14) ③이미지만 배포하면 compose 변경이 호스트에 영원히 미전달(설계 공백)→에이전트 git fetch/reset+호스트 clone 전환 ④컨테이너 root vs 호스트 소유자→safe.directory |
| 2026-08-29 | **E2E 관통** | llm push→Actions(26s, ghcr)→www/api/deploy→master→agent(.164)→wrapper ghcr sha 이미지 재생성(9.9s)→rewrite 200. ghcr 무인증 pull 실증(가정①) |
| 2026-08-29 | 남김 | backend·front 리포 Actions 확장(다음 이슈) · 롤백(태그 이력은 /status에 축적 중) · codex 리뷰(spec ⑤ — 다음 턴) · study-note 이슈 문서+게이트 |
| 2026-08-29 | #7 git-pull 전환(PR #8, llm #15) | agent = fetch+reset <sha> → up -d --build <svc>(10분 타임아웃). E2E 재검증: push→15.4s 재빌드·재생성·health 200. Actions는 호출만(2s) |
| 2026-08-29 | study-note 문서 4건 push | backend8·front6·ci-cd1·2 — 이해 게이트 대기 |
| 2026-08-29 | 게이트(3차) 통과·요청 반영 | RESP.md(cs)·ci-cd issue2 결함 4건 전말 상세화·front 절대경로 임포트 정책(PR #14)·참조명 제거·작성법 4단 서술 규칙 |
| 2026-08-29 | Actions 확장(backend PR#19·front PR#16) + DEPLOY_SECRET 전 리포 등록 | 3서비스 전부 push→자동 배포 대상화 |
| 2026-08-29 | codex 리뷰(단독 — 사유 spec 기록) → fix PR #10 | 채택6: compose 역할 분리(master sock 미노출 — 마운트 0 검증)·sha 접수 전 검증·master 서비스별 single-flight(무음 유실 금지)·배포 후 헬스 확인(DEPLOY_HEALTH_*)·healthcheck 포트·http 타임아웃. 기각2: F1 ghcr 회귀(사용자 결정·리스크 명문화)·F2 go.mod(packet 오탐 — 2회째, packet 자기검증 필요성 확정). 이연1: F3 HMAC+타임스탬프(후속 이슈) |
| 2026-08-29 | 3대 재배치 + 전 서비스 E2E | front 자동 배포 56s(Next 빌드 포함) · backend 1차 unhealthy — **헬스체크 기능이 설계대로 오배포를 잡음**(BIND_ADDR 바인딩이라 127.0.0.1 거부 → 헬스 URL 교정) → 2차 ok 38s(gradle 증분) · llm 15s. 검색·엣지 전부 200 |
