# 요구사항 명세 — ci-cd (Go 배포 서버, master/agent 단일 바이너리)
| 칸 | 내용 |
|----|------|
| ① 목표 | study-note-deploy-system-ci-cd(Go): **MODE=master|agent 단일 바이너리**. master(.9:15000) — 배포 접수(공유 시크릿·상수시간 — HMAC+타임스탬프는 후속 이슈)·서비스 allowlist(front/backend/llm)·에이전트 라우팅·상태. agent(각 호스트 :15001, 컨테이너+docker.sock) — `docker compose pull/up` 실행(고정 디렉토리 allowlist)·결과 보고. 흐름(2026-08-29 개정 — 사용자 결정): 리포 Actions(**호출만**) → www/api/deploy(front 중계) → master → agent **git fetch/reset <sha> + compose up -d --build <svc>** + 배포 후 헬스 확인. 수용 리스크: 저장소 커밋이 compose를 바꿀 수 있음(main은 PR 게이트·자기 소유 repo 전제 — 명문화) |
| ② 불변식 | 봉투·로그 규약(requestId·Redis XADD) 준수 · 시크릿/IP repo 0(.env — DEPLOY_SECRET 신설, docs/secrets.md 대장) · 서비스·디렉토리 allowlist 고정 열거(임의 경로·명령 불가) · sudo 불요(에이전트=컨테이너) · 기존 jun-bank(13000대) 무접촉 — **15000번대 사용** |
| ③ 기준소스 | docs/logging.md · front relay 패턴 · jun-bank 구조(참고만 — 코드 미복사) |
| ④ 금지 | main 직접 push · 에이전트에서 allowlist 밖 실행 · 오라클 conf 변경(www 재활용) |
| ⑤ 검증 | 단위(HMAC·allowlist·모드 분기 — 거절 경로 우선) → 3대 실기동 → **E2E: llm 리포 push → 자동 배포(git-pull 재빌드) → wrapper 헬스 확인** → 中 codex 1회(사유: 신규 Go·보안 표면) |
| ⑥ stakes | 중간~높음(원격 실행 표면) |
- auto · 이슈: ①스캐폴드(MODE·HMAC·봉투·로그) ②master ③agent ④배선+llm Actions E2E. 롤백은 태그 기록만(후속 이슈)
- load-bearing 가정: ⑴ ghcr public 이미지는 호스트에서 무인증 pull 가능 ⑵ 에이전트 컨테이너가 docker.sock+프로젝트 디렉토리 마운트로 형제 compose 제어 가능 — 이슈③에서 스모크
