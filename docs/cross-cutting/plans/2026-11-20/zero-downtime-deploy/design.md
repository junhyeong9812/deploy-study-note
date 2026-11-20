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

## CD — 명령 순서 (활성 = A, 대상 = B)
0. 같은 서비스의 구 버전 정리가 진행 중이면 끝날 때까지 기다린다.
1. 활성 파일의 첫 줄에서 A를 읽는다. 파일이 없거나 표식이 없으면 **`cd_switch`로 거절**하고 아무 명령도 실행하지 않는다.
2. `docker compose stop <기준>-B` — 지난 정리가 실패해 남아 있을 수 있는 대상을 내린다.
3. `IMAGE_TAG=<sha> docker compose up -d --no-build --no-deps <기준>-B` — 실패 `cd_up`.
4. B의 자리별 헬스 URL이 200이 될 때까지 대기(90초) — 실패 `cd_health`.
5. 활성 파일을 B의 템플릿 내용으로 바꾼다(이전 내용 보관).
6. `docker compose exec -T nginx nginx -t` — 실패 `cd_switch`.
7. `docker compose exec -T nginx nginx -s reload` — 실패 `cd_switch`.
8. 외부 헬스 URL 200 대기(30초) — 실패 `cd_switch`.
9. 성공 응답. 그 뒤 **뒷일(비동기)**: A의 정리 알림 URL이 있으면 POST → `docker compose exec -T nginx ps`에 `shutting down`이 없어질 때까지 2초 간격으로 확인(상한 3분) → `docker compose stop <기준>-A` → 오래된 이미지 정리.

### 실패 시 되돌림
| 실패 지점 | 하는 일 | 운영 |
|---|---|---|
| 1 | 없음 | A 그대로 |
| 3·4 | `docker compose stop <기준>-B` | A 그대로(nginx 무변경) |
| 6 | 활성 파일을 이전 내용으로 복원 → `stop B` | A 그대로(reload 안 함) |
| 7·8 | 활성 파일 복원 → `nginx -s reload`(되돌림) → `stop B` | A로 복귀 |

- 되돌림 자체가 실패하면 그 사실을 실패 출력에 덧붙인다(조용히 넘기지 않는다).
- 3분 뒤에도 남은 연결은 nginx의 `worker_shutdown_timeout 180s`가 끊는다(repo의 nginx 설정이 소유). agent의 상한은 그 뒤에 구 버전 컨테이너를 내리는 시점을 정한다.
- 정리 중 실패(알림 실패·`stop` 실패)는 경고 로그만 남긴다. 다음 CD의 2번이 다시 내린다.

## 시간 예산
기동 2분 + 자리 헬스 90초 + 전환·외부 헬스 30초 = 4분, 앞선 정리 대기 최대 3분 10초. master의 CD 호출 제한 8분.
