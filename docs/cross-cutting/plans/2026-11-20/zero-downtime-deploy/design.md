# 설계 — agent의 blue/green 전환 계약 (task 02의 기준)

명세 ②의 불변식을 agent가 어떤 명령·파일로 지키는지 정한다. 테스트는 이 계약과 명세에서 출발한다.

## 용어
- **자리(slot)**: `blue` 또는 `green`. compose 서비스 이름은 `<기준>-blue`·`<기준>-green`(기준 = env `DEPLOY_SVC_<SVC>`, 예: `app`).
- **활성 파일**: `<배포 디렉토리>/deploy/active/upstream.conf`. nginx가 include 하는 파일이고 git에 넣지 않는다. 첫 줄이 `# slot: blue` 또는 `# slot: green`. 이 첫 줄이 활성 자리의 정본이다.
- **자리 템플릿**: `<배포 디렉토리>/deploy/nginx/upstream-blue.conf`·`upstream-green.conf`(repo가 소유, 첫 줄에 같은 표식).
- **프록시**: compose 서비스 `nginx`.

## 설정(env, 서비스마다)
| 키 | 뜻 | 없을 때 |
|---|---|---|
| `DEPLOY_DIR_<SVC>` · `DEPLOY_SVC_<SVC>` | 배포 디렉토리 · 기준 서비스 이름 | 요청 거절(기존) |
| `DEPLOY_HEALTH_<SVC>` | 외부 포트(nginx 경유) 헬스 URL | CD 거절(기존) |
| `DEPLOY_HEALTH_<SVC>_BLUE` · `_GREEN` | 자리별 헬스 URL(127.0.0.1 포트) | CD 거절 `cd_health` — 운영 무변경 |
| `DEPLOY_DRAIN_<SVC>_BLUE` · `_GREEN` | 구 버전에 정리 시작을 알리는 URL(POST) | 알리지 않음(선택) |

## CI (변경점만)
- 이미지 빌드: `docker compose build <기준>-blue` (두 자리는 같은 이미지를 쓴다).
- 운영 중인 버전 = 활성 자리(`<기준>-<활성>`) 컨테이너의 이미지 태그. 활성 파일이 없으면 HEAD(경고 로그).

## 실제 활성 자리 확인 (선검증 반영)
활성 파일만 믿으면 "파일은 B인데 nginx는 A로 보내는" 상태(파일을 바꾼 직후 agent가 죽었거나, reload가 조용히 적용되지 않은 경우)를 구분하지 못한다. 그래서 **nginx가 실제로 어느 자리로 보내는지**를 응답으로 확인한다.
- 자리 템플릿은 `upstream`과 함께 자리 표식 변수(`$deploy_slot`)를 정의하고, nginx `server`는 모든 응답에 `X-Deploy-Slot: <자리>` 헤더를 붙인다.
- **자리 확인(probe)** = 외부 헬스 URL을 호출해 상태 200과 `X-Deploy-Slot` 값을 읽는 것.
- 활성 파일은 nginx에 원하는 자리를 전하는 수단이고, 판정은 probe 결과로 한다. 파일은 임시 파일에 쓴 뒤 이름을 바꿔 한 번에 교체한다.

## CD — 명령 순서 (실제 활성 = A, 대상 = B)
0. 같은 서비스의 정리(뒷일)가 진행 중이면 끝날 때까지 기다린다.
1. 활성 파일의 첫 줄(`# slot: …`)과 probe 결과를 읽는다.
   - 파일이 없거나 표식이 없으면 **`cd_switch`로 거절**, 아무 명령도 실행하지 않는다.
   - probe가 실패하면(외부 포트가 응답하지 않음) **`cd_switch`로 거절**(운영 상태를 모르는 채 전환하지 않는다).
   - 파일과 probe가 다르면 probe를 따른다: 파일을 probe 자리의 템플릿으로 고쳐 쓰고 경고 로그를 남긴 뒤 진행한다.
2. `docker compose stop <기준>-B` — 남아 있을 수 있는 대상을 내린다. **실패하면 `cd_up`으로 중단**(자리를 비우지 못한 채 진행하지 않는다).
3. `IMAGE_TAG=<sha> docker compose up -d --no-build --no-deps <기준>-B` — 실패 `cd_up`.
4. B의 자리별 헬스 URL 200 대기(90초) — 실패 `cd_health`.
5. 활성 파일을 B의 템플릿 내용으로 교체(이전 내용 보관).
6. `docker compose exec -T nginx nginx -t` — 실패 `cd_switch`.
7. `docker compose exec -T nginx nginx -s reload` — 실패 `cd_switch`.
8. probe가 **B**를 돌려줄 때까지 대기(30초, 1초 간격) — 200이어도 자리가 A면 통과가 아니다. 실패 `cd_switch`.
9. 성공 응답. 그 뒤 **뒷일(비동기)**: A를 정리한다(아래).

### 자리 정리 (뒷일 — 대상 자리 X)
X의 정리 알림 URL이 있으면 POST → `docker compose exec -T nginx ps` 출력에 `shutting down`이 없어질 때까지 2초 간격 확인(상한 3분) → `docker compose stop <기준>-X` → (성공한 배포 뒤라면) 오래된 이미지 정리.
- 알림 실패·`stop` 실패는 경고 로그만 남긴다. 다음 CD의 2번이 다시 내리고, 거기서도 실패하면 CD가 중단된다.

### 실패 시 되돌림
| 실패 지점 | 하는 일 | 운영 |
|---|---|---|
| 1 | 없음 | 그대로 |
| 2 | 없음 | A 그대로 |
| 3·4 | `docker compose stop <기준>-B` | A 그대로(nginx 무변경) |
| 6 | 활성 파일 복원 → `stop B` | A 그대로(reload 안 함) |
| 7·8 | 활성 파일 복원 → `nginx -s reload`(되돌림) → **B를 바로 내리지 않고 "자리 정리"로 넘긴다** | A로 복귀. reload를 시도한 뒤에는 B에 연결이 들어갔을 수 있어 끝날 때까지 둔다 |

- 되돌림 자체가 실패하면 그 사실을 실패 출력에 덧붙인다(조용히 넘기지 않는다).
- 3분 뒤에도 남은 연결은 nginx의 `worker_shutdown_timeout 180s`가 끊는다(repo의 nginx 설정이 소유). 3분을 넘는 스트림은 끊긴다 — 명세 ②의 사용자 결정(최대 3분).

## agent 기동 시 정리
agent가 뜰 때 설정된 서비스마다 probe로 실제 활성 자리를 확인하고, 반대쪽 자리를 "자리 정리"로 넘긴다(배포 성공 직후 agent가 죽어 두 벌이 남은 경우). probe가 실패하면 아무것도 내리지 않고 경고만 남긴다.

## 테스트 접점 (구현이 제공하는 것 — 테스트는 이것만 쓴다)
- `Agent.run`: 명령 실행 함수(기존). 시그니처 `func(ctx context.Context, directory string, environment []string, arguments ...string) (string, error)`.
- `Agent.waitHealthy`: `func(healthURL string, budget time.Duration) error`(기존).
- `Agent.probeSlot`: `func(healthURL string) (slot string, err error)` — 외부 헬스 URL의 200과 `X-Deploy-Slot` 값.
- `Agent.notifyDrain`: `func(drainURL string) error`.
- `Agent.drainPollInterval`·`Agent.drainLimit`·`Agent.probeInterval`·`Agent.probeBudget`: `time.Duration`(테스트가 줄여 쓴다).
- `Agent.waitBackground()`: 진행 중인 뒷일이 끝날 때까지 기다린다.
- 파일은 실제 파일 시스템을 쓴다: `DEPLOY_DIR_<SVC>` 아래 `deploy/active/upstream.conf`, `deploy/nginx/upstream-{blue,green}.conf`.
- HTTP: `POST /agent/cd`(본문 `{service, commit_sha, request_id}`), 실패는 500 + `error.code`=단계.

## 시간 예산
기동 2분 + 자리 헬스 90초 + 전환·자리 확인 30초 = 4분, 앞선 정리 대기 최대 3분 10초. master의 CD 호출 제한 8분.
