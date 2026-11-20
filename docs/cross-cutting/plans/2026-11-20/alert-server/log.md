# log — alert-server

| 시각(KST) | 사건 | 결과 |
|-----------|------|------|
| 11-20 20:5x | 사전 조사 — explorer(sonnet, 73k 토큰, 38 tool)로 기존 로그·지표·알림 흔적 탐색 + 서버 3대 실측 | 로그 규약·Redis 스트림 전송은 4개 서비스에 구현돼 있고 읽는 쪽 없음(XLEN 10037). 지표·알림은 8월 철거 뒤 없음. 규약 문서는 9월에 study-note로 이관돼 이 트리에 없음 |
| 11-20 21:0x | 인터뷰(선택 질문 3회 + 서술 답) | 직접 구현·PostgreSQL(관측)·채널 3종·어드민 동시 시작 → Kotlin · 관측/알림 2서버 · 어드민 백엔드 없음 · 로그인 ID/PW · 메시지 통로 Redis Stream · 알림 서버 이중화 대신 엣지 감시자 + 하루 한 번 요약. 알림 서버 세부 4문항 답 수신 → 명세 초안, 합의 대기 |
| 11-20 21:2x | 사용자: "웹훅주소들은 전부 모킹해서 진행 … 추후 해줄게. 우선 진행" | 명세 합의로 해석, set-state spec-approved / mode auto. **채널 실주소 없음** — 발송은 가짜 수신 서버로 검증하고, 실제 디스코드·슬랙·Gmail 발송 확인은 주소를 받은 뒤로 미룬다(생략한 검증에 기재). 기준 SHA: ci-cd d5a779d · backend 470593b · front 48a01b5 |
| 11-20 21:1x(UTC 12:10~12:17) | 가정1 실증 중 **실제 장애 관측** — 엣지에서 집 front 포트로 직접 `curl`이 3회 연속 시간 초과, 노트북→공개 주소도 시간 초과 | `.9`는 정상(로컬 200, front-nginx 2시간 가동, 마지막 엣지 요청 12:07:29Z). 집 공인 IP는 엣지 설정과 동일. 12:16Z에 다시 연결됨 — 끊김은 12:07:44Z 전후부터 수 분(트래픽이 적어 nginx 로그로는 길이를 못 잼 = 엣지 감시자가 필요한 이유). 오늘 엣지 로그: front 포트 시간 초과 65건이 00:11Z부터 종일 분포(무중단 전환 이전부터) → 오늘 변경과 무관. "연결 거부" 472건은 전부 14000 포트(bank 도메인의 죽은 서비스) — 별개 |
| 11-20 21:2x | 가정1 판정 | 연결이 정상일 때 엣지 → 집 front 포트 직접 호출이 200 + `X-Deploy-Slot`으로 응답 = 감시 스크립트의 전제 성립. 엣지에 crontab·curl·bash 있음, 여유 메모리 211MB |
| 11-20 21:3x | 장애 길이 추정 | `.9` front-nginx가 받은 엣지 요청: 12:07Z 6건 뒤 12:08~12:14Z 0건, 12:15Z 재개 = **약 7~8분 끊김**. 같은 구간에 `.9` 링크 끊김·컨테이너 변동 없음 |
| 11-20 21:3x | 가정2 — 설계 변경 | backend에 `HealthIndicator` 빈을 더하면 기본 `/actuator/health` 합산에도 들어가 ES·임베딩이 죽을 때 배포의 헬스 판정이 바뀐다(명세 ④ 위반). 헬스 그룹 대신 **별도 경로 `GET /api/health/dependencies`**(자체 컨트롤러, 대상별 시간 제한)로 구현 — 기본 헬스는 구조상 무변경. 명세 ②·task 05의 경로 표기를 이에 맞춤 |
| 11-20 21:3x | task 02·03 — alert 저장소 본체(로컬 커밋 7a79e0b) | 단위 36개 통과(판정 8·폴백 5·한 바퀴 7·설정 파일 4·HTTP 확인 6·접수 2·API 4). 도중 실패 2건: ①테스트 컨텍스트가 채널 0개로 기동 실패 → 테스트에 가짜 채널 주입 ②`starter-jdbc`의 DataSource 자동 구성이 드라이버를 못 찾음 → `spring-jdbc`만 쓰고 연결은 직접 연다 |
| 11-20 21:3x | 로컬 실행(가짜 수신 서버 + 가짜 감시 대상, 주기 2초) | 1차: 가짜 서버의 결함(204에 본문·경로 해석)으로 디스코드가 매번 실패한 것처럼 보임 → 가짜 서버 수정. 2차: 1회 실패 무알림 · 3회 연속 실패 DOWN · 복구(끊긴 시간) · 같은 바퀴 2개 묶음 · 디스코드 거절 시 슬랙 · 같은 key 억제 · 두 채널 모두 거절 → 보관 후 복구 뒤 재발송 · 인증 없는 접수 401 확인 |
| 11-20 21:4x | task 05 — backend `GET /api/health/dependencies`(브랜치 feat/dependency-health, 5a567d4) | 단위 3개 + 전체 통과. `.158`에서 임베딩 `/health`·ES `/_cluster/health`가 200인 것 실확인 |
| 11-20 21:4x | task 06·04(ci-cd 쪽) — 사건 발송 + 서비스 목록에 alert(브랜치 feat/alert-events, 1d1d71b) | `go vet` + `go test -race` 통과(발송 내용·미설정 시 무동작·호출 측 비차단·실패/성공/알림 서버 불통 3경로) |
| 11-20 21:4x | task 07 — front 중계 2종(브랜치 feat/ops-alert-relay, f2c3a31) · 엣지 감시 스크립트(alert 저장소 `edge/watchdog.sh`) | vitest 45개 통과. 스크립트는 가짜 대상으로 단발 실패 무알림 · 3회 연속 실패 알림 · 복구 알림+사건 전달 · 알림 서버만 장애 · 끊김 기록 확인 |
| 11-20 21:4x | 듀얼 리뷰 1패스 시작 — Opus 워커 ∥ codex(인라인 입력) | 22:0x 회수: codex 지적 8·질문 3, Opus 지적 7·질문 8(163k 토큰, 19 tool). 종합 → codex 감사 → 수정 |
| 11-20 22:0x | 리뷰 반영 수정 — alert 5f9e8ec · ci-cd 4cb50ab · backend b4d98e0 | alert 단위 69개(2회 연속 통과) · ci-cd vet+race 통과 · backend 통과. 수정 중 실측 2건: ①한 SQLite 연결을 여러 스레드가 섞어 쓰면 `SQLITE_BUSY_SNAPSHOT`(읽는 도중 같은 연결의 쓰기) → 저장소 접근을 한 번에 하나씩으로 묶고 WAL ②억제된 접수가 억제 시각을 새로 적어 창이 늘어남 → 발송을 맡길 때만 적음 |
| 11-20 22:1x | 통합 실행(실제 nginx + blue·green 두 자리 + 가짜 수신 서버, 주기 2초) | 두 자리가 겹친 12초 동안 중복 알림 0 · 전환 뒤 6초 안에 green 이 이어받음(DOWN 1건 승계, 재알림 없음) · 전환 뒤 같은 key 사건 억제 · 복구 알림 1회(끊긴 시간은 처음 장애부터 30초) · 활성 자리에 정리 알림만 간 경우 4초 안에 다시 맡음 · 구 자리 정지 뒤 단독 감시 정상. 전환 직후 한 바퀴 동안은 프록시 경유 헬스가 `standby`(실운영 최대 30초 — 엣지 기준 3분에 못 미침) |
| 11-20 22:1x | 엣지 감시 스크립트 수정본 시나리오 6종(가짜 대상) | 단발 실패 무알림 · 집 전체 끊김에 알림 1건(사이트) · 알림 서버만 503 · standby 로만 보임 · 디스코드 거절 중 재시도 뒤 발송 · 사이트 복구 뒤에도 알림 서버가 안 보이면 알림 — 모두 기대대로 |
| 11-20 22:1x | **명세 ② 문구 수정**(배포 중 조항) — 구 자리 판정 기준을 "정리 알림"에서 "프록시가 보내는 자리"로 | 불변식의 목적(중복 없음)은 그대로, 수단이 바뀜. 사용자 확인 대기 |
| 11-20 22:2x | post-fix 재점검(codex) | 미해소 3 · 새 결함 3 · 테스트 2. 고침(alert dca2850): ①자리 교대 때 미발송 알림 소유권 — 대기로 내려가는 자리는 보관함을 내려놓고, 이어받은 자리가 기록에서 되살림(기록 60초 뒤부터, 읽기 실패 시 다음 바퀴 재시도) ②발송 대기열 상한 500(넘치면 보관함으로) ③요약의 끊긴 시간은 24시간 안의 몫만 ④기록에 심각도 저장 ⑤엣지 복구 알림 실패 시 다음 실행에 재발송 ⑥본문 지연 테스트·경계 테스트 추가. 받지 않음: 엣지 웹훅 미설정을 실패로 볼 것(보낼 곳이 없는데 매분 재시도·로그만 쌓임 — 로그 1줄로 남김). 단위 75개 2회 연속 통과, 건너뜀 0 |
| 11-20 22:3x | 재점검 반영 중 그린 위장 1건 발견·수정 | 기록 읽기 실패 테스트가 WAL 에서 잠금이 읽기를 막지 않아 통째로 건너뛰어짐(skipped 1) → 실패하는 연결을 주입하는 방식으로 바꿔 실제 검증 |
| 11-21 01:0x | 사용자: "이대로 가자" — 공개·PR·`.9` 배치·엣지 설치·문서 push, 명세 문구 수정, 기각 2건 유지 모두 확인 | 진행 |
| 11-21 01:0x | 공개 저장소 `study-note-deploy-system-alert` 생성·push(main dca2850) | 첫 push 의 배포 실행은 저장소에 `DEPLOY_SECRET` 이 없어 성공할 수 없어 취소. **사용자가 GitHub 저장소 비밀값을 넣기 전까지 alert 는 push 로 배포되지 않는다** |
| 11-21 01:1x | 이슈·PR — ci-cd #19/#20 · backend #40/#41 · front #49/#50 | 세 건 병합. backend·front 는 파이프라인으로 무중단 배포 성공 |
| 11-21 01:1x(16:17Z) | `.9` 에 알림 서버 최초 배치 — clone, `.env`(비밀값은 서버에서 생성, 채널은 받지 못하는 임시값), blue 자리 + nginx | 10초 안에 `ok`·`X-Deploy-Slot: blue`, 감시 8개 시작. 기록 파일은 WAL 로 생성 |
| 11-21 01:1x | ci-cd 를 세 서버에 반영(백업 `~/ci-cd-backup-20261121`), 알림 연동·alert 배포 설정 추가, agent 3 + master 재기동 | 전부 healthy. 재기동의 짧은 끊김으로는 알림이 생기지 않음(3번 연속 기준) |
| 11-21 01:1x | 실측: 아직 배포 전이던 backend 의 의존 경로를 알림 서버가 16:18:37Z 에 DOWN 으로 판정 → backend 배포 뒤 16:21:39Z 에 복구(끊긴 시간 3분 1초) | 의도하지 않은 첫 실전 판정. backend 새 경로 응답 `{"status":"UP","components":{elasticsearch·embedding·redis 모두 UP}}`, 기존 `/actuator/health` 는 `status: UP`(응답에 `groups` 항목이 보이나 이번 diff 는 새 파일 2개뿐 — 설정 무변경) |
| 11-21 01:2x | 엣지에 감시 스크립트·설정(`/etc/alert-watchdog.env`, 디스코드 주소 비움)·1분 예약 작업 설치 | 엣지에서 `alert-health` 200 `ok`, 비밀 없는 사건 접수 401 |
| 11-21 01:2x | **실행 ①** llm 활성 자리 정지 16:24:11Z | 16:25:42Z DOWN(1분 31초 뒤, `status 502`) → 재기동 뒤 16:26:12Z 복구. 관찰: 복구 알림의 "끊긴 시간 30초"는 DOWN 판정 시각부터 센 값 — 실제 끊김(첫 실패부터)은 약 2분. NEXT 후보 |
| 11-21 01:2x | **실행 ②** front 대상 자리 헬스 주소를 틀리게 하고 배포 재실행 | `cd_health` 실패 → 16:26:55Z 알림 서버에 `[ci-cd] 배포 실패 front — 단계 cd_health` 접수, 사이트는 기존 자리로 200. 설정 원복·agent 재기동, 3번째 실행 성공(green) |
| 11-21 01:3x | **실행 ④** 알림 서버 정지 16:27:27Z ~ 16:31:52Z | 엣지가 16:30:01Z(3번째 연속 실패)에 "밖에서 안 보임: 알림 서버 (3분 0초째)", 16:32:01Z 에 복구(4분 0초)를 남김 — 디스코드 주소가 없어 발송 대신 로그. 복구 사건이 front 중계로 알림 서버에 접수됨. 재기동한 알림 서버는 기록에서 미발송 6건을 되살림 |
| 11-21 01:3x(16:34Z~) | **실제 장애 관측** — 공개 주소 504, 엣지→집 front 포트 연결 시간 초과. `.9` 로컬은 200, 엣지 요청은 16:33Z 까지만 도착 | 11-20 에 본 간헐 끊김과 같은 양상(이번 작업은 엣지 nginx·공유기를 건드리지 않음). 엣지 감시자가 16:36:01Z 에 "밖에서 안 보임: 사이트 (3분 0초째)"를 남김 — 설치 직후 첫 실전 탐지 |
| 11-21 01:4x | 사이클 마감 — 측정 로그 1행, NEXT 갱신 | 아카이브 보류(명세 범위에 study-note 쓰기 없음 — 사용자 범위 확인 필요). 후보 3건은 NEXT `보류·이월`에 등재 |

## 리뷰 ledger

듀얼 1패스(O = Opus 워커, C = codex). 종합·감사·재점검 원문: 세션 scratchpad `review-alert/`(synthesis.md · results/).

| # | 지적 | 출처 | 판정 | 처리 |
|---|------|------|------|------|
| S1 | 발송이 감시 바퀴 스레드에서 동기로 돌아 채널이 죽으면 확인 주기가 멈춤 | C1·O-F2 | 고침 | 발송 전용 스레드, 재시도는 한 건이 전부 실패하면 그 회차 중단, `/events`는 맡기고 바로 응답 |
| S2 | 요약에 대상별 DOWN 횟수·합계 시간 없음, 기록을 못 읽어도 0건으로 보고 | C2·O-F3 | 고침 | 대상별 상태 변화를 따로 기록, 못 읽으면 "읽지 못했다" 명시 |
| S3 | 활성 자리 개념 없음 — 새 자리가 뜨자마자 발송(중복), 정리 알림 뒤에도 트래픽을 받는 자리는 감시가 꺼진 채 헬스 ok | O-F1·O-F4·C3 | 고침 | 프록시의 자리 표식으로 자기 확인, 대기 자리는 `standby`, 엣지는 standby 를 실패로 셈. 명세 ② 문구 수정 |
| S4 | 못 보낸 알림이 재시작 때 사라짐 | C5 | 고침(부분) | 최근 24시간 미발송 건을 기록에서 되살림. 200건 상한은 유지 — 감사는 "여전히 소실 가능"이라 봄(error 로그로 남김) |
| S5 | 엣지 스크립트가 웹훅 4xx·5xx 를 성공으로 처리 | C6 | 고침 | 응답 코드 확인, 실패 시 다음 실행에 재발송 |
| S6 | 잘못된 웹훅 주소가 예외 문구로 로그에 나올 수 있음 | C8 | 고침 | 생성 시 값 없이 검증, 오류 문구 고정 |
| S7 | master 재시작으로 중단된 배포 미보고 | O-F5 | 고침 | 건수 담은 사건 1건 |
| S8 | ci-cd 설정 예시에 alert 없음 | O-F6 | 고침 | 예시 추가 |
| S9 | 쓰지 않는 `host` 필드 | O-F7 | 고침 | 삭제 |
| S10 | SQLite 동시 접근 미검증 | O-OQ1·C-OQ2 | 고침 | 접근 직렬화 + WAL + 8스레드·두 연결 테스트(실결함 발견) |
| S11 | 첫 바퀴가 안 돌아도 `starting` 200 무기한 | O-OQ5 | 고침 | 2분 뒤 503 |
| S12 | ES 가 red 여도 200 | O-OQ7 | 고침 | 본문 status 확인 |
| S13 | 사이트 실패 중 알림 서버 확인 생략 | C7·O-OQ8 | 고침(감사로 기각 번복) | 두 경로 매번 확인, 사이트 실패 중에는 알림만 보류 |
| S14 | 본문을 끄는 대상은 5초가 아니라 10초 | O-OQ6 | 고침(감사로 후보 번복) | 본문 포함 5초 |
| S15 | 전환 직후 사건 억제 상태가 인계되지 않음 | O-F4·감사 | 고침(감사로 후보 번복) | 기록으로 판단 |
| S16 | 채널 HTTP 동작·agent 발송 지점 테스트 없음 | C verified | 고침 | 웹훅 테스트 5건, agent 정지 보류 테스트 1건 |
| R1 | 재시작 뒤 DOWN 대상의 첫 성공에 곧바로 복구 알림 | C4 | 기각(감사 이견) | 이미 알린 장애의 복구는 평소에도 성공 1회. "3번 확인 전 무알림"은 모름→DOWN 조건 |
| R2 | 정리 중인 자리는 `/events`도 발송 금지 | C3 일부 | 기각(감사 이견) | 요청은 한 자리에만 도착 — 버리면 누락 |
| K1 | 복구·재알림도 같은 바퀴끼리 묶기 | O-OQ2 | 후보 | NEXT 로 |

## 생략한 검증
- 서버 실행 ③(디스코드 실패 → 슬랙)·⑤(09:00 요약 수신) — 실제 채널 주소가 없어 미실행. ①②④는 11-21 실행(발송 대신 기록·로그로 확인).
- alert 저장소의 push 배포(워크플로) — 저장소 비밀값 `DEPLOY_SECRET` 이 없어 미확인. 최초 배치는 손으로 했다.
- 재점검 반영분(dca2850)은 다시 리뷰하지 않음(1패스 규칙) — 단위 테스트로만 확인. 자리 교대 인계는 통합 실행을 다시 돌리지 않았다(서버 배포 때 확인).
- 실제 디스코드·슬랙·Gmail 발송 — 사용자가 주소·앱 비밀번호를 주기 전까지 가짜 수신 서버로만 확인. 받은 뒤 실행 ③(폴백)·⑤(아침 요약)를 실채널로 다시 확인.

## 완료 요약

- **결과**: 알림 서버(`study-note-deploy-system-alert`, Kotlin·Spring Boot)가 `.9` 의 16000 포트(LAN 에만 열림, nginx 뒤 두 자리 구성 — 최초 배치는 blue)에 떠서 감시 대상 8개를 30초마다 확인한다. 3번 연속 실패면 DOWN 알림, 복구되면 끊긴 시간을 알리고, 다른 서버가 보내는 사건(`POST /events`)을 받아 디스코드 → 슬랙 → 메일 순서로 보낸다. 상태 변화·사건·발송 결과는 SQLite(WAL)에 남는다. ci-cd master 는 배포가 `failed` 로 끝나거나 재시작으로 배포가 중단되면 알림 서버에 사건을 보내고, agent 는 두 자리가 남았을 수 있는 상황을 보낸다. backend 에는 의존 서비스 상태 경로 `GET /api/health/dependencies` 가 생겼고(기본 `/actuator/health` 는 손대지 않음), front 는 알림 서버 헬스·사건 접수를 중계한다. 집 밖에서는 엣지의 1분 예약 작업(`edge/watchdog.sh`)이 사이트와 알림 서버를 직접 확인하고, 3분 연속 안 보이면 엣지가 직접 알린다. 단, 실제 채널 주소가 아직 없어 지금은 서버·엣지 모두 발송 대신 기록·로그로만 남는다.
- **발행**: 공개 저장소 alert(main dca2850 — 7a79e0b → 1b66ff5 → 5f9e8ec → dca2850) / ci-cd #19→PR #20(cf5d5b6) / backend #40→PR #41(bfa52be) / front #49→PR #50(e138dec). ci-cd 는 서버 3대 직접 반영(백업 `~/ci-cd-backup-20261121`). alert 의 `.9` 최초 배치와 엣지 설치는 손으로 했다.
- **규모(작업 시작 기준 → 현재 main)**: alert 48 files changed, 3342 insertions(+)(신규) · ci-cd 10 files changed, 284 insertions(+), 6 deletions(-) · backend 2 files changed, 121 insertions(+) · front 5 files changed, 140 insertions(+)
- **리뷰**: 듀얼 1패스(채택 16 · 기각 2 · 후보 1) + post-fix 재점검 1회(미해소 3 · 새 결함 3 · 테스트 2 → dca2850 에서 고침, 1건은 받지 않음). 재점검 반영분은 다시 리뷰하지 않았다.
- **수정 중 실측이 잡은 것**: ①한 SQLite 연결을 여러 스레드가 섞어 쓰면 `SQLITE_BUSY_SNAPSHOT` — 저장소 접근을 한 번에 하나씩으로 묶고 WAL ②억제된 접수가 억제 시각을 새로 적어 억제 창이 늘어남 ③기록 읽기 실패 테스트가 WAL 에서 통째로 건너뛰어지던 그린 위장(skipped 1) — 실패하는 연결을 주입하는 방식으로 바꿈.

### 핵심 코드 (git 객체에서 복사)

**alert — 감시 한 바퀴: 리뷰 전에는 `draining` 플래그로 멈추고 바퀴 안에서 동기로 발송했다** (리뷰 전 1b66ff5 `src/main/kotlin/xyz/junproject/alert/monitor/MonitorRound.kt` 42–59행, 97–101행)
```kotlin
    fun run() {
        if (draining) return
        val now = clock()
        val results = probeAll()
        if (draining) return   // 확인하는 사이 교체가 시작됐다 — 이 결과로는 알리지 않는다
        val transitions = mutableListOf<MonitorTransition>()
        for (definition in definitions) {
            val result = results[definition.name] ?: ProbeResult.failed("${roundBudget.seconds}초 안에 확인을 끝내지 못했다")
            val (next, transition) = tracker.advance(definition.name, states[definition.name] ?: MonitorState(), result, now)
            states[definition.name] = next
            runCatching { store?.saveState(definition.name, next, now) }
                .onFailure { log.warn("alert:alert:state not recorded for {}: {}", definition.name, it.message) }
            transition?.let(transitions::add)
        }
        lastRoundAt = now
        announce(transitions, now)
        notifier.retryUndelivered()
    }
```
```kotlin
    private fun send(kind: String, key: String, notification: Notification, now: Instant) {
        val result = notifier.notify(notification)
        runCatching { store?.record(Incident(now, kind, key, notification.title, notification.body, result.deliveredBy)) }
            .onFailure { log.warn("alert:alert:incident not recorded ({}): {}", kind, it.message) }
    }
```
**리뷰 뒤 — 프록시가 보내는 자리만 감시하고, 대기로 내려가면 미발송분을 내려놓고, 발송은 맡기기만 한다** (dca2850 같은 파일 46–74행, 162–167행)
```kotlin
    fun run() {
        if (!activeSlot.refresh()) {
            if (holding) {
                // 못 보낸 알림은 기록에 남아 있다 — 이어받은 자리가 되살려 보내므로 여기서는 내려놓는다(두 번 보내지 않게)
                val abandoned = notifier.abandonUndelivered()
                log.info("alert:alert:standing by — another slot is serving ({} undelivered left to it)", abandoned)
            }
            holding = false
            return
        }
        val now = clock()
        if (!holding) takeOver(now)
        restoreUndelivered(now)
        val results = probeAll()
        if (!activeSlot.active) return   // 확인하는 사이 정리 알림을 받았다 — 이 결과로는 알리지 않는다
        val transitions = mutableListOf<MonitorTransition>()
        for (definition in definitions) {
            val result = results[definition.name] ?: ProbeResult.failed("${roundBudget.seconds}초 안에 확인을 끝내지 못했다")
            val (next, transition) = tracker.advance(definition.name, states[definition.name] ?: MonitorState(), result, now)
            states[definition.name] = next
            runCatching { store?.saveState(definition.name, next, now) }
                .onFailure { log.warn("alert:alert:state not recorded for {}: {}", definition.name, it.message) }
            transition?.let(transitions::add)
        }
        lastRoundAt = now
        recordChanges(transitions)
        announce(transitions, now)
        notifier.retryUndelivered()
    }
```
```kotlin
    /** 먼저 기록하고(발송 전에는 채널이 비어 있다) 발송을 맡긴다. 나가면 그 행에 채널을 적는다. */
    private fun send(kind: String, key: String, notification: Notification, now: Instant) {
        val id = runCatching { store?.record(Incident(now, kind, key, notification.title, notification.body, null, severity = notification.severity.name)) }
            .onFailure { log.warn("alert:alert:incident not recorded ({}): {}", kind, it.message) }.getOrNull()
        notifier.submit(notification) { channel -> if (id != null) markDelivered(id, channel) }
    }
```
**alert — 미발송 재시도: 리뷰 전에는 감시 바퀴 안에서 보관함 전체를 돌았다** (1b66ff5 `src/main/kotlin/xyz/junproject/alert/notify/FallbackNotifier.kt` 34–42행)
```kotlin
    /** 못 보낸 알림을 다시 시도한다. 이번에도 못 보낸 것은 그대로 남는다. 보낸 건수를 돌려준다. */
    fun retryUndelivered(): Int {
        var delivered = 0
        repeat(undelivered.size) {
            val notification = undelivered.poll() ?: return delivered
            if (deliver(notification).delivered) delivered++ else undelivered.add(notification)
        }
        return delivered
    }
```
**리뷰 뒤 — 발송 전용 스레드에 맡기고, 한 건이 또 전부 실패하면 거기서 멈춘다** (dca2850 같은 파일 82–102행, 123–127행)
```kotlin
    /** 못 보낸 알림의 재시도를 발송 스레드에 맡긴다(이미 맡겨 둔 재시도가 있으면 겹쳐 넣지 않는다). */
    fun retryUndelivered() {
        if (undelivered.isEmpty() || !retryQueued.compareAndSet(false, true)) return
        worker.execute { try { retryNow() } finally { retryQueued.set(false) } }
    }

    /**
     * 못 보낸 알림을 오래된 것부터 다시 보낸다. 한 건이 또 모든 채널에서 실패하면 거기서 멈춘다 —
     * 채널이 죽어 있는 동안 보관함 전체를 돌며 시간을 쓰지 않는다. 보낸 건수를 돌려준다.
     */
    fun retryNow(): Int {
        var delivered = 0
        while (true) {
            val pending = undelivered.peek() ?: break
            val channel = deliver(pending.notification).deliveredBy ?: break
            undelivered.remove(pending)
            runCatching { pending.onDelivered(channel) }
            delivered++
        }
        return delivered
    }
```
```kotlin
        /** 발송 스레드 하나 + 상한이 있는 대기열 — 유입이 발송보다 빨라도 메모리가 끝없이 늘지 않는다. */
        fun boundedWorker(queueLimit: Int = SEND_QUEUE_LIMIT): Executor = ThreadPoolExecutor(
            1, 1, 0L, TimeUnit.MILLISECONDS, LinkedBlockingQueue(queueLimit),
            { task -> Thread(task, "alert-sender").apply { isDaemon = true } }, ThreadPoolExecutor.AbortPolicy(),
        )
```
**alert — 기록: 여러 스레드가 한 연결을 섞어 쓰던 것을 한 번에 하나씩 + WAL 로** (1b66ff5 `src/main/kotlin/xyz/junproject/alert/incident/IncidentStore.kt` 19–20행 → dca2850 같은 파일 30–41행. 리뷰 뒤에는 모든 공개 메서드에 `@Synchronized` 가 붙었다)
```kotlin
/** 기록 — 파일 DB(SQLite). 감시와 발송은 이 기록이 실패해도 계속돼야 하므로 호출하는 쪽이 예외를 삼킨다. */
class IncidentStore(private val jdbc: JdbcTemplate) {
```
```kotlin
/**
 * 기록 — 파일 DB(SQLite). 감시와 발송은 이 기록이 실패해도 계속돼야 하므로 호출하는 쪽이 예외를 삼킨다.
 * 연결 하나를 여러 스레드(감시 바퀴·발송·HTTP 요청)가 함께 쓰므로 모든 접근을 한 번에 하나씩으로 묶는다 —
 * 한 스레드가 읽는 도중에 다른 스레드가 같은 연결로 쓰면 SQLite 가 쓰기를 거절한다(실측: SQLITE_BUSY_SNAPSHOT).
 * 배포 중에는 두 자리(두 프로세스)가 같은 파일을 연다 — 잠긴 동안은 [BUSY_TIMEOUT_MS] 까지 기다린다.
 */
class IncidentStore(private val jdbc: JdbcTemplate) {
    init {
        jdbc.execute("PRAGMA busy_timeout = $BUSY_TIMEOUT_MS")
        // WAL: 쓰는 쪽이 읽는 쪽을 막지 않고 커밋이 짧다 — 두 자리가 겹치는 동안의 잠금 실패를 줄인다
        jdbc.execute("PRAGMA journal_mode = WAL")
        jdbc.execute("PRAGMA synchronous = NORMAL")
```
**alert — 엣지 감시자: 리뷰 전에는 웹훅 응답을 보지 않았고, 사이트가 안 보이면 알림 서버를 확인하지 않았다** (1b66ff5 `edge/watchdog.sh` 27–33행, 70–76행)
```bash
send_discord() {   # 실패해도 스크립트는 계속된다
  if [ -z "${DISCORD_WEBHOOK_URL:-}" ]; then log "discord 미설정 — 보내지 않음: $1"; return 0; fi
  local payload
  payload="$(printf '{"content": "%s"}' "$(printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g')")"
  curl -sS -m 10 -o /dev/null -H 'Content-Type: application/json' -d "$payload" "$DISCORD_WEBHOOK_URL" 2>>"$STATE_DIR/watchdog.log" \
    || log "discord 발송 실패: $1"
}
```
```bash
if probe "$HOME_TARGET/"; then
  check site "사이트" 1
  # 사이트가 보일 때만 알림 서버를 따로 본다 — 사이트가 안 보이면 알림 서버 확인도 같이 실패하므로 알림을 겹치지 않는다
  if probe "$HOME_TARGET/api/ops/alert-health"; then check alert "알림 서버" 1; else check alert "알림 서버" 0; fi
else
  check site "사이트" 0
fi
```
**리뷰 뒤 — 응답 코드로 성공을 판정하고(실패면 다음 실행에 재발송), 두 경로를 매번 따로 확인한다** (dca2850 같은 파일 27–37행, 93–98행)
```bash
# 보냈으면 0, 못 보냈으면 1 — 웹훅이 4xx·5xx 로 답한 것도 실패다(다음 실행에 다시 보낸다)
send_discord() {
  if [ -z "${DISCORD_WEBHOOK_URL:-}" ]; then log "discord 미설정 — 보내지 않음: $1"; return 0; fi
  local payload code
  payload="$(printf '{"content": "%s"}' "$(printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g')")"
  code="$(curl -s -m 10 -o /dev/null -w '%{http_code}' -H 'Content-Type: application/json' -d "$payload" "$DISCORD_WEBHOOK_URL" 2>/dev/null)"
  case "$code" in
    2??) return 0 ;;
    *) log "discord 발송 실패(응답 ${code:-없음}): $1"; return 1 ;;
  esac
}
```
```bash
# 두 경로를 매번 따로 확인한다. 사이트가 안 보이는 동안에는 알림 서버 쪽 "안 보임" 알림만 미룬다 —
# 집 전체가 끊기면 둘 다 실패하므로 알림은 사이트 것 하나면 된다. 사이트가 돌아왔는데도 알림 서버가 안 보이면 그때 알린다.
if probe "$HOME_TARGET/"; then site_ok=1; else site_ok=0; fi
if alert_watching; then alert_ok=1; else alert_ok=0; fi
check site "사이트" "$site_ok" 0
check alert "알림 서버" "$alert_ok" "$((1 - site_ok))"
```
**ci-cd — 배포 실패 시 알림 서버에 사건을 보낸다(보내기 실패는 배포 결과에 영향 없음)** (`git diff d5a779d cf5d5b6 -- internal/master/master.go` 의 해당 hunk — cf5d5b6 171–181행)
```diff
@@ -168,6 +174,10 @@ func (master *Master) advance(deployment Deployment, agentURL string) {
 		master.logger.Log(deployment.RequestID, fmt.Sprintf("deploy failed %s sha=%s stage=%s %s",
 			deployment.Service, deployment.CommitSha, stage, lastPart(detail, 200)), "error")
 		master.recordFinished(deployment)
+		// 사람이 알아야 한다 — GitHub 메일에만 기대지 않는다. 보내기에 실패해도 배포 결과는 그대로다.
+		master.alerts.Send(deployment.RequestID, "deploy_failed", "warning", "deploy-failed:"+deployment.Service+":"+deployment.CommitSha,
+			fmt.Sprintf("배포 실패 %s — 단계 %s", deployment.Service, stage),
+			fmt.Sprintf("커밋 %s\n%s", deployment.CommitSha, lastPart(detail, 800)))
 	}
 	enter := func(state string) bool {
 		deployment.State = state
```
**backend — 의존 서비스 상태를 actuator 지표가 아닌 별도 경로로 둔 이유와 본체** (bfa52be `src/main/kotlin/xyz/junproject/backend/shared/api/DependencyHealthController.kt` 15–45행)
```kotlin
/**
 * 의존 서비스 상태 — ES·임베딩은 이 서버 안에서만 열려 있어 밖(알림 서버)에서 직접 볼 수 없다.
 *
 * actuator 의 헬스 지표로 넣지 않고 별도 경로로 둔다: 지표로 넣으면 기본 `/actuator/health` 합산에 들어가
 * 의존 서비스가 죽었을 때 이 앱의 배포 헬스 판정까지 바뀐다(앱 자체는 살아 있는데 배포가 막힌다).
 */
@RestController
class DependencyHealthController(
    private val checks: Map<String, () -> Unit>,
    private val budget: Duration = Duration.ofSeconds(3),
) {
    @Autowired
    constructor(redis: StringRedisTemplate) : this(defaultChecks(redis))

    /** 항상 200 — 어느 것이 안 되는지는 본문의 components 로 알린다(부르는 쪽이 판정한다). */
    @GetMapping("/api/health/dependencies")
    fun dependencies(): Map<String, Any> {
        val executor = Executors.newVirtualThreadPerTaskExecutor()
        val pending = checks.mapValues { (_, check) -> executor.submit<String?> { runCatching(check).exceptionOrNull()?.let(::describe) } }
        executor.shutdown()
        val deadline = System.nanoTime() + budget.toNanos()
        val components = pending.mapValues { (_, future) ->
            val failure = try {
                future.get(maxOf(0, deadline - System.nanoTime()), TimeUnit.NANOSECONDS)
            } catch (_: Exception) { "${budget.seconds}초 안에 응답 없음" }
            if (failure == null) mapOf("status" to "UP") else mapOf("status" to "DOWN", "detail" to failure)
        }
        executor.shutdownNow()   // 예산을 넘긴 확인은 버린다 — 한 대상이 느려도 응답이 늦지 않게
        val allUp = components.values.all { it["status"] == "UP" }
        return mapOf("status" to if (allUp) "UP" else "DOWN", "components" to components)
    }
```

### 검증 결과 (서버 실행 시각은 UTC — 11-21 01:2x~01:3x KST)

| 구분 | 언제 | 결과 |
|------|------|------|
| 단위 — alert | 11-20 22:2x KST | 75개 2회 연속 통과, 건너뜀 0(리뷰 전 36 → 리뷰 반영 69 → 재점검 반영 75) |
| 단위 — ci-cd | 11-20 21:4x·22:0x | `go vet` + `go test -race` 통과(개수는 기록하지 않음) |
| 단위 — backend | 11-20 21:4x·22:0x | 새 테스트 3개 + 전체 통과 |
| 단위 — front | 11-20 21:4x | vitest 45개 통과 |
| 통합 실행(노트북: 실제 nginx + blue·green + 가짜 수신 서버, 주기 2초) | 11-20 22:1x | 두 자리가 겹친 12초 동안 중복 알림 0 · 전환 뒤 6초 안에 green 이 이어받음(DOWN 1건 승계, 재알림 없음) · 전환 뒤 같은 key 사건 억제 · 복구 알림 1회 · 활성 자리에 정리 알림만 간 경우 4초 안에 다시 맡음 |
| 엣지 스크립트(가짜 대상) | 11-20 22:1x | 시나리오 6종 모두 기대대로 |
| 첫 실전 판정(의도하지 않음) | 11-21 01:1x KST(16:18:37Z → 16:21:39Z) | 배포 전이던 backend 의존 경로를 DOWN 판정, backend 배포 뒤 복구(끊긴 시간 3분 1초) |
| 서버 실행 ① llm 활성 자리 정지 | 16:24:11Z 정지 → 16:25:42Z DOWN → 16:26:12Z 복구 | DOWN 까지 1분 31초(`status 502`). 복구 알림의 끊긴 시간 30초는 DOWN 판정 시각부터 센 값 |
| 서버 실행 ② front 헬스 주소를 틀리게 한 배포 | 16:26:55Z | `cd_health` 실패 → `[ci-cd] 배포 실패 front — 단계 cd_health` 접수, 사이트는 기존 자리로 200. 원복 뒤 3번째 실행 성공(green) |
| 서버 실행 ③ 디스코드 실패 → 슬랙 | — | 미실행(실제 채널 주소 없음) |
| 서버 실행 ④ 알림 서버 정지 | 16:27:27Z ~ 16:31:52Z | 엣지가 16:30:01Z 에 "밖에서 안 보임: 알림 서버 (3분 0초째)", 16:32:01Z 에 복구(4분 0초) — 디스코드 주소가 없어 로그로. 복구 사건이 front 중계로 접수됨. 재기동한 알림 서버가 미발송 6건을 기록에서 되살림 |
| 서버 실행 ⑤ 09:00 요약 수신 | — | 미실행(실제 채널 주소 없음) |
| 실제 장애 탐지 | 16:34Z~ | 공개 주소 504, 엣지→집 연결 시간 초과. 엣지 감시자가 16:36:01Z 에 "밖에서 안 보임: 사이트 (3분 0초째)"를 남김 |

### 남은 것

- **실제 채널 발송**: 디스코드·슬랙·Gmail 주소를 받지 못해 `.9` `.env` 의 채널은 받지 못하는 임시값이고, 엣지 설정의 디스코드 주소는 비어 있다. 지금은 알림이 사람에게 가지 않는다. 주소를 받은 뒤 실행 ③(폴백)·⑤(아침 요약)를 실채널로 확인해야 한다.
- **alert 의 push 배포**: GitHub 저장소 비밀값 `DEPLOY_SECRET` 이 없어 push 로 배포되지 않는다(첫 실행은 취소). 사용자가 넣은 뒤 워크플로 배포를 한 번 확인해야 한다.
- **복구 알림의 끊긴 시간**: DOWN 판정 시각부터 센다 — 실행 ①에서 실제 끊김은 약 2분인데 30초로 나왔다. 첫 실패부터 세도록 바꾸는 것이 NEXT 후보.
- **재점검 반영분(dca2850) 미리뷰**: 1패스 규칙으로 다시 리뷰하지 않았고 단위 테스트로만 확인했다. 자리 교대 때의 미발송 인계는 통합 실행을 다시 돌리지 않았다 — alert 의 다음 배포 때 서버에서 확인한다.
- **미발송 보관 상한 200건**: 넘치면 오래된 것부터 버린다(error 로그로 남김). 리뷰 감사는 여전히 소실 가능하다고 봤다.
- **복구·재알림 묶기**(K1): 같은 바퀴의 DOWN 만 묶고 복구·재알림은 대상마다 나간다 — NEXT 후보.
- **전환 직후의 `standby`**: 배포 전환 직후 한 바퀴(실운영 최대 30초) 동안 프록시 경유 헬스가 `standby` 로 보인다. 엣지의 3분 기준에는 걸리지 않는다.
- **확인하지 않은 것**: backend `/actuator/health` 응답에 `groups` 항목이 보이는 이유(이번 diff 는 새 파일 2개뿐이라 이번 변경과는 무관하다고 봤으나 원인은 보지 않음) · 11-20·11-21 에 본 엣지→집 간헐 끊김의 원인(엣지 감시자의 `outages.log` 에 쌓이기 시작함).
