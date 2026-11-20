# 설계 — agent의 blue/green 전환 계약 (task 02의 기준)

명세 ②의 불변식을 agent가 어떤 명령·파일로 지키는지 정한다. 테스트는 이 계약과 명세에서 출발한다.

## 용어
- **자리(slot)**: `blue` 또는 `green`. compose 서비스 이름은 `<기준>-blue`·`<기준>-green`(기준 = env `DEPLOY_SVC_<SVC>`, 예: `app`).
- **활성 파일**: `<배포 디렉토리>/deploy/active/upstream.conf`. nginx가 include 하는 파일이고 git에 넣지 않는다. 첫 줄이 `# slot: blue` 또는 `# slot: green`. 이 첫 줄이 활성 자리의 정본이다.
- **자리 템플릿**: `<배포 디렉토리>/deploy/nginx/upstream-blue.conf`·`upstream-green.conf`(repo가 소유, 첫 줄에 같은 표식).
- **프록시**: compose 서비스 `nginx`.
- **활성 디렉토리**: `<배포 디렉토리>/deploy/active/`. nginx가 읽는 것은 이 디렉토리뿐이다 — `nginx.conf`(본 설정의 운영 사본)와 `upstream.conf`(활성 파일). git에 넣지 않는다. repo의 `deploy/nginx/nginx.conf`는 원본이고, agent가 전환할 때 사본을 갱신한다(리뷰 반영: nginx가 git 작업 트리를 직접 읽으면 CI의 소스 갱신만으로 운영 설정이 바뀌고, 전환 실패 때 되돌릴 수 없다).

## 설정(env, 서비스마다)
| 키 | 뜻 | 없을 때 |
|---|---|---|
| `DEPLOY_DIR_<SVC>` · `DEPLOY_SVC_<SVC>` | 배포 디렉토리 · 기준 서비스 이름 | 요청 거절(기존) |
| `DEPLOY_MODE_<SVC>` | `bluegreen`이면 이 문서의 전환 방식. 서비스를 하나씩 옮기는 동안 나머지는 기존 단일 컨테이너 방식으로 둔다 | 기존 방식 |
| `DEPLOY_HEALTH_<SVC>` | 외부 포트(nginx 경유) 헬스 URL | CD 거절(기존) |
| `DEPLOY_HEALTH_<SVC>_BLUE` · `_GREEN` | 자리별 헬스 URL(127.0.0.1 포트) | CD 거절 `cd_health` — 운영 무변경 |
| `DEPLOY_DRAIN_<SVC>_BLUE` · `_GREEN` | 구 버전에 정리 시작을 알리는 URL(POST) | 알리지 않음(선택) |

## CI (변경점만)
- 이미지 빌드: `docker compose build <기준>-blue` (두 자리는 같은 이미지를 쓴다).
- 운영 중인 버전 = nginx가 실제로 보내는 자리(probe)의 컨테이너 이미지 태그. 외부 포트가 응답하지 않으면(서비스가 죽어 있어 고치는 배포일 수 있다) 활성 파일의 표식을 차선으로 쓰고, 그것도 없으면 HEAD(경고 로그).

## 실제 활성 자리 확인 (선검증 반영)
활성 파일만 믿으면 "파일은 B인데 nginx는 A로 보내는" 상태(파일을 바꾼 직후 agent가 죽었거나, reload가 조용히 적용되지 않은 경우)를 구분하지 못한다. 그래서 **nginx가 실제로 어느 자리로 보내는지**를 응답으로 확인한다.
- 자리 템플릿은 자리 표식(`$deploy_slot`)과 앱 주소(`$deploy_upstream`) 두 변수를 정의하고, nginx `server`는 모든 응답에 `X-Deploy-Slot: <자리>` 헤더를 붙인다.
- **자리 확인(probe)** = 외부 헬스 URL을 호출해 상태와 `X-Deploy-Slot` 값을 읽는 것. "nginx가 어느 자리로 보내는가"는 표식만으로 판정한다 — 운영 중인 앱이 죽어 502가 나와도 표식은 붙으므로 고치는 배포를 진행할 수 있다. nginx 자체가 응답하지 않거나 표식이 없을 때만 "모름"이다(3회 재확인). "새 자리가 정상인가"(8단계)는 200과 표식을 함께 본다.
- 활성 파일은 nginx에 원하는 자리를 전하는 수단이고, 판정은 probe 결과로 한다. 파일은 임시 파일에 쓴 뒤 이름을 바꿔 한 번에 교체한다.

## CD — 명령 순서 (실제 활성 = A, 대상 = B)
0. 같은 서비스의 정리(뒷일)가 진행 중이면 끝날 때까지 기다린다. 정리 상한 + 70초를 넘겨도 끝나지 않으면 `cd_up`으로 거절한다(무한 대기 금지). 다음 CD가 기다리는 것은 자리 정지까지이고, 이미지 정리는 기다리지 않는다.
1. 활성 파일의 첫 줄(`# slot: …`)과 probe 결과를 읽는다.
   - 파일이 없거나 표식이 없으면 **`cd_switch`로 거절**, 아무 명령도 실행하지 않는다.
   - 자리를 알 수 없으면(nginx 무응답 또는 표식 없음) **`cd_switch`로 거절**(운영 상태를 모르는 채 전환하지 않는다). 502라도 표식이 있으면 진행한다.
   - 파일과 probe가 다르면 probe를 따른다: 파일을 probe 자리의 템플릿으로 고쳐 쓰고 경고 로그를 남긴 뒤 진행한다.
2. `docker compose stop <기준>-B` — 남아 있을 수 있는 대상을 내린다. **실패하면 `cd_up`으로 중단**(자리를 비우지 못한 채 진행하지 않는다).
3. `IMAGE_TAG=<sha> docker compose up -d --no-build --no-deps <기준>-B` — 실패 `cd_up`.
4. B의 자리별 헬스 URL 200 대기(90초) — 실패 `cd_health`.
5. 본 설정 사본을 repo 원본 내용으로, 활성 파일을 B의 템플릿 내용으로 교체(둘 다 이전 내용 보관).
6. `docker compose exec -T nginx nginx -t` — 실패 `cd_switch`.
7. `docker compose exec -T nginx nginx -s reload` — 실패 `cd_switch`.
8. probe가 **B**를 돌려줄 때까지 대기(30초, 1초 간격) — 200이어도 자리가 A면 통과가 아니다. 실패 `cd_switch`.
9. 성공 응답. 그 뒤 **뒷일(비동기)**: A를 정리한다(아래).

### 자리 정리 (뒷일 — 대상 자리 X)
X의 정리 알림 URL이 있으면 POST → `docker compose exec -T nginx ps` 출력에 `shutting down`이 없어질 때까지 2초 간격 확인(상한 3분) → **probe로 nginx가 X로 보내고 있지 않음을 확인** → `docker compose stop <기준>-X` → (성공한 배포 뒤라면) 오래된 이미지 정리.
- probe가 X를 돌려주거나 실패하면 X를 내리지 않고 error 로그만 남긴다(응답 중이거나 상태를 모르는 자리는 내리지 않는다 — 리뷰 반영).
- 알림 실패·`stop` 실패는 경고 로그만 남긴다. 다음 CD의 2번이 다시 내리고, 거기서도 실패하면 CD가 중단된다.

### 실패 시 되돌림
| 실패 지점 | 하는 일 | 운영 |
|---|---|---|
| 1 | 없음 | 그대로 |
| 2 | 없음 | A 그대로 |
| 3·4 | `docker compose stop <기준>-B` | A 그대로(nginx 무변경) |
| 6 | 활성 파일·본 설정 사본 복원 → `stop B` | A 그대로(reload 안 함) |
| 복원 자체가 실패 | B를 내리지 않는다. 실패 출력에 남긴다 | 파일이 B를 가리킨 채일 수 있다 — B를 내리면 nginx가 다시 뜰 때 갈 곳이 없다 |
| 7·8 | 활성 파일·본 설정 사본 복원 → `nginx -s reload`(되돌림) → **표식이 A인지 확인(200이 아니어도 됨)** → 확인되면 B를 "자리 정리"로 넘긴다 | A로 복귀. reload를 시도한 뒤에는 B에 연결이 들어갔을 수 있어 끝날 때까지 둔다 |
| 7·8의 되돌림을 확인하지 못함 | 어느 자리도 내리지 않는다. 실패 출력에 "되돌림 미확인"을 남긴다 | nginx가 A·B 중 어디로 보내는지 모름 — 두 자리 모두 살아 있으므로 요청은 처리된다. 다음 CD의 1단계가 실제 자리를 보고 정리 |

- 되돌림 자체가 실패하면 그 사실을 실패 출력에 덧붙인다(조용히 넘기지 않는다).
- 3분 뒤에도 남은 연결은 nginx의 `worker_shutdown_timeout 180s`가 끊는다(repo의 nginx 설정이 소유). 3분을 넘는 스트림은 끊긴다 — 명세 ②의 사용자 결정(최대 3분).

## agent 기동 시 정리
agent가 뜰 때 설정된 서비스마다 probe로 실제 활성 자리를 확인해, 활성 파일이 다르면 실제에 맞추고 반대쪽 자리를 "자리 정리"로 넘긴다(배포 성공 직후 agent가 죽었거나 서버가 재부팅돼 두 벌이 남은 경우). probe가 실패하면 아무것도 내리지 않고, **확인될 때까지 30초 간격으로 다시 시도한다** — 서버가 막 부팅했으면 앱과 nginx가 뜨는 데 1~2분이 걸린다(리뷰 반영).

## compose 쪽 약속 (repo가 지킨다)
- 두 자리 서비스에는 `profiles`를 붙인다. 이름을 지정한 명령(`up <자리>`·`stop <자리>`)에만 반응하고, 이름 없는 `docker compose up -d`는 두 자리를 띄우지 않는다(평소 한 벌).
- nginx는 앱 주소를 설정을 읽을 때가 아니라 요청 때 도커 내부 DNS로 찾는다(`resolver 127.0.0.11`, 변수 `proxy_pass`). 앱 컨테이너가 재시작돼 주소가 바뀌어도 reload 없이 따라가고, 앱이 아직 없어도 nginx가 뜬다(502 + 자리 표식).
- nginx 컨테이너에는 활성 디렉토리 하나만 붙인다(`./deploy/active:/etc/nginx:ro`). 디렉토리째 붙이므로 파일이 새로 만들어져도 컨테이너가 새 내용을 본다.
- 기동 시 정리는 배포가 진행 중이면 그 회차를 건너뛴다(같은 잠금, 기다리지 않음).

## 테스트 접점 (구현이 제공하는 것 — 테스트는 이것만 쓴다)
- `Agent.run`: 명령 실행 함수(기존). 시그니처 `func(ctx context.Context, directory string, environment []string, arguments ...string) (string, error)`.
- `Agent.waitHealthy`: `func(healthURL string, budget time.Duration) error`(기존).
- `Agent.probeSlot`: `func(healthURL string) (slot string, err error)` — 외부 헬스 URL의 200과 `X-Deploy-Slot` 값.
- `Agent.notifyDrain`: `func(drainURL string) error`.
- `Agent.drainPollInterval`·`Agent.drainLimit`·`Agent.probeInterval`·`Agent.probeBudget`: `time.Duration`(테스트가 줄여 쓴다).
- `Agent.waitBackground()`: 진행 중인 뒷일이 끝날 때까지 기다린다.
- `Agent.ReconcileSlots()`(1회)·`Agent.ReconcileSlotsUntil(budget, interval)`(재시도)·`Agent.drainWaitMargin`.
- 파일은 실제 파일 시스템을 쓴다: `DEPLOY_DIR_<SVC>` 아래 `deploy/active/upstream.conf`, `deploy/nginx/upstream-{blue,green}.conf`.
- HTTP: `POST /agent/cd`(본문 `{service, commit_sha, request_id}`), 실패는 500 + `error.code`=단계.

## 시간 예산
기동 2분 + 자리 헬스 90초 + 전환·자리 확인 30초 = 4분(+되돌림 여유 30초), 앞선 정리 대기 최대 4분 10초. master의 CD 호출 제한 9분. 워크플로 합계 = 작업 중 대기 3 + CI 11.5 + CD 9 = 23.5분(상한 25분).
