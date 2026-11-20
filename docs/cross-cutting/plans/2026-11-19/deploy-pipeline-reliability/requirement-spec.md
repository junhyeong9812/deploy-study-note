# requirement-spec — 배포 신뢰성 (CI/CD 분리 · 상태 조회 · 이력 DB)

> 2026-11-19. 대상 repo 5개: `ci-cd`(master·agent) · `front`(중계) · `llm` · `backend` · `front`(워크플로·Dockerfile·compose). repo마다 이슈→브랜치→PR.
> 로드맵 전체는 `docs/cross-cutting/plans/NEXT.md`. 이 작업은 그 1번이다.

## 0. 요구사항 원문
- 계기: 11-19 llm PR #21 배포 호출이 엣지에서 504를 받았는데 Actions는 초록불. 서버는 이전 커밋 그대로였다(10-04에도 같은 기록).
- 사용자: "ci 즉 테스트 검사 및 빌드검사를 하고 … 러너의 역할이 필요 … 엣지에서 실제로 배포가 안되는 케이스는 fail처리 후 재시도 … 관리 시스템"
- 사용자: "A가 요청을 받아 대기시키고, B가 빌드랑 테스트를 돌려보고 문제 없으면 A에게 OK사인 … 이후 배포에서는 그대로 배포만" · "처리 이력은 별도 DB에 저장"
- 선택 답: 결과 확인 = 상태 조회 API + 폴링 / 실패 시 = 빨간불만, 수동 조치 / GitHub 기본 러너를 못 쓰는 환경 가정 → agent가 러너 역할 / 무중단·로그 중앙화·알림은 별도 작업.

## ① 목표·대상
main에 병합하면 **master가 CI(받기→테스트→이미지 빌드) → CD(이미지 교체→헬스체크)를 차례로 진행**하고, GitHub 워크플로는 그 결과를 끝까지 조회해 **실제로 배포된 경우에만 초록불**이 된다. 모든 배포의 단계별 결과가 DB에 남는다.

## ② 경계·불변식
- **초록불 = 배포됨.** 워크플로 성공 ⇔ master 상태가 `succeeded`(요청한 sha로 CD 완료 + 헬스 통과). 접수 실패·CI 실패·CD 실패·시간 초과·상태 조회 불가는 전부 빨간불.
- **CI가 실패하면 운영은 그대로.** 테스트나 빌드가 실패하면 실행 중인 컨테이너를 건드리지 않고, 배포 디렉토리의 소스도 직전 커밋으로 되돌린다.
- **CD는 빌드하지 않는다.** CI가 만든 `sha` 태그 이미지로 교체만 한다(`up -d --no-build --no-deps <대상>`). 대상 외 컨테이너(ES·Redis·Ollama 등)는 재생성되지 않는다.
- **진행 주체 = master.** 워크플로는 접수 1회 + 조회만. CI→CD 전환은 master가 한다(워크플로와 엣지 사이가 끊겨도 배포는 끝까지 간다).
- **접수는 멱등.** 같은 `request_id`로 다시 접수하면 새 배포를 만들지 않고 기존 건의 상태를 돌려준다(재시도가 이중 배포가 되지 않게).
- **상태**: `accepted → ci_running → cd_running → succeeded | failed`. `failed`에는 실패 단계(`ci_fetch`·`ci_test`·`ci_build`·`cd_up`·`cd_health`·`agent_unreachable`·`interrupted` + 리뷰 반영 11-19: `agent_rejected`(agent가 단계 전에 거절 — 설정 누락·계속 작업 중)·`store_failed`(이력 기록 실패))와 출력 끝부분(≤2000자)이 붙는다. master가 재시작하면 진행 중이던 건은 `failed(interrupted)`로 닫는다(영원한 진행 중 금지).
- **API**
  - master `POST /deploy`(기존, 멱등 추가) · `GET /deploys/{request_id}`(신설) · `GET /deploys?service=&limit=`(신설, 이력) · 기존 `GET /status`는 유지.
  - agent `POST /agent/ci` · `POST /agent/cd`(신설, 동기 응답). 기존 `/agent/deploy`는 전환 기간 유지 후 정리 커밋에서 제거.
  - front 중계 `GET /api/deploy/[requestId]`(신설, 비밀값 패스스루 — 기존 POST 중계와 같은 방식).
  - 인증은 전부 기존 `X-Deploy-Secret`. 인증 실패는 조회도 401.
- **같은 서비스 동시 요청**: 기존대로 409. 워크플로는 409를 "잠시 뒤 재시도"로 다룬다(상한 있음).
- **워크플로(3개 동일)**: 접수 = 2xx·409 외에는 재시도(5회·간격 20초 — `.9` 링크 끊김이 약 20초라는 실측 기준). 조회 = 10초 간격, 일시 실패는 넘기고, 전체 20분 상한. 끝나면 상태·실패 단계·출력을 로그에 출력.
- **테스트 계약**: 각 repo Dockerfile에 `test` 단계를 두고 agent는 `docker build --target test`를 실행한다. 테스트 명령은 repo가 소유하고 agent는 모른다. 네트워크·GPU가 필요한 테스트는 `test` 단계에 넣지 않는다.
- **이미지 태그**: 대상 compose 서비스에 `image: <이름>:${IMAGE_TAG:-local}`. agent가 `IMAGE_TAG=<sha>`로 빌드·기동. 서비스별 최근 5개 태그만 남기고 지운다(디스크 상한).
- **이력 DB**: master가 SQLite 파일 하나(`data/deploys.db`, 호스트 볼륨)에 건별 1행으로 기록. 쓰는 주체는 master뿐. 어드민은 나중에 API(`GET /deploys`)로 읽는다. DB 쓰기 실패는 배포를 실패 처리(조용한 유실 금지).
- **되돌리기(수동)**: 이전 sha로 접수를 다시 보내면 CI가 이미지 캐시로 끝나고 CD가 교체한다. 자동 롤백 없음.
- 비밀값·IP는 repo에 넣지 않는다(기존 env 방식 유지).

## ③ 기준소스
ci-cd `internal/master/master.go`·`internal/agent/agent.go`·`internal/shared/*`·`docker-compose.yml`(main 70151a5) · front `src/app/api/deploy/route.ts`·`src/features/deploy/lib/relay.ts` · 3개 repo `.github/workflows/deploy.yml`·Dockerfile·`docker-compose.yml` · 엣지 `project-deploy-data/edge/nginx/conf.d/www.junproject.xyz.conf`(connect 10s·read 60s) · 실측(11-19 chat-queue log: backend 배포 411s·ES 재생성, `.9` 링크 끊김 약 20초).

## ④ 금지영역
무중단(blue/green)·프록시 도입 금지 · 자동 롤백 금지 · PR 단계 검사·웹훅 수신·GitHub 토큰 사용 금지 · 로그 중앙 수집·알림 금지 · 어드민 화면 금지 · 엣지 nginx conf 변경 금지 · 각 서비스의 앱 코드 변경 금지(Dockerfile `test` 단계·compose `image` 줄·워크플로만) · GitHub 자체 호스팅 러너 설치 금지.

## ⑤ 검증 방법
- 단위(ci-cd `go test`): 상태 전이 전 구간 · CI 실패 시 CD 미호출 · 같은 request_id 재접수 = 기존 건 반환 · 재시작 시 진행 건 `interrupted` · DB 쓰기 실패 = failed · 조회 401/404 · agent CI 실패 시 소스 원복 명령 실행. front: 조회 중계 테스트.
- 실행(서버): ① 정상 배포 — 워크플로가 succeeded까지 기다려 초록불, 서버 커밋·이미지 태그 일치 ② **테스트를 일부러 깨뜨린 커밋** — 빨간불 + `ci_test` + 운영 컨테이너 생성 시각 불변 ③ **접수 실패 재현**(잘못된 주소 또는 master 정지) — 재시도 후 빨간불 ④ backend 배포 중 `backend-es` 컨테이너 생성 시각 불변 ⑤ master 재시작 후 이력 조회됨.
- 반증: 상태 조회가 끊긴 20초 동안 워크플로가 성급히 실패하지 않나? 202 응답이 유실된 뒤 재시도가 이중 배포를 만들지 않나? CI 성공 후 CD 전에 master가 죽으면 무엇이 남나? 테스트 단계가 실제로 실패를 전파하나(`|| true`류 없음)?
- 리뷰: 중간 — 듀얼 1패스 + post-fix 재점검.

## ⑥ stakes: 중간
외부 호출·재시도·타임아웃·부분 실패를 다루고 4개 repo의 배포 계약이 바뀐다. 데이터 변경 없음. 깨져도 서버에서 수동 `compose up`으로 배포 가능하고 repo별 revert로 복구된다.

## 자율성
auto 제안. 이슈·push·PR·병합, 그리고 **서버 3대의 ci-cd 재기동**(자동 배포 대상이 아니라 SSH로 직접)은 각각 확인.

## load-bearing 가정 (착수 직후 실증)
1. `compose build <대상>` 후 `up -d --no-build --no-deps <대상>`이 `IMAGE_TAG` 이미지로 대상만 교체하고 ES를 재생성하지 않는다(.158에서 실측).
2. 순수 Go SQLite 드라이버(`modernc.org/sqlite`)가 현재 빌드 이미지(golang 1.23-alpine, CGO 없음)에서 빌드·동작한다.

## task 분해
| task | repo | 목표 | 의존 | acceptance |
|------|------|------|------|-----------|
| 01 | ci-cd | agent `/agent/ci`·`/agent/cd` + 이미지 태그·정리 | 가정1 | 단위 + .164에서 수동 호출 |
| 02 | ci-cd | master 상태 기계 + SQLite + 조회 API + 멱등 접수 | 01, 가정2 | 단위 + .9에서 조회 |
| 03 | llm·backend·front | Dockerfile `test` 단계 + compose `image` 태그 | 01 | 각 서버에서 `build --target test` 통과 |
| 04 | front | 조회 중계 라우트 | 02 | 엣지 경유 조회 |
| 05 | llm·backend·front | 워크플로: 접수 재시도 + 폴링 + 실패 처리 | 02·04 | ⑤ 실행 ①~⑤ |
| 06 | ci-cd | 구 `/agent/deploy` 제거(정리 커밋) | 05 확인 후 | 테스트 통과 |
- 배포 순서: agent(3대) → master → repo별 03 → front 04 → 워크플로 05. 05 이전까지는 기존 워크플로가 구 경로로 계속 동작한다.
