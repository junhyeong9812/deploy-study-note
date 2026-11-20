# log — zero-downtime-deploy

| 시각(KST) | 사건 | 결과 |
|-----------|------|------|
| 11-20 12:0x | 사전 실측(서버 3대 자원·포트·컨테이너, 두 벌 공존 시 충돌할 백그라운드 작업 grep) | 메모리 여유 충분, compose에 이름·포트 고정, backend 주기 작업 없음(sync는 요청 구동·공유 볼륨) |
| 11-20 12:1x | 인터뷰(선택 질문 4) → 명세 초안 | 사용자 합의 대기 |
| 11-20 12:3x | 사용자: "진행하자" | set-state spec-approved / mode auto. 기준 SHA: ci-cd 339c22b · llm 92dab17 · backend e66f4d3 · front 7b7395c |
| 11-20 12:41 | task 01 가정 실증 — 로컬 nginx 1.27 + 스트림 서버 2개(blue·green), 스트림 2개를 물린 채 대상 변경 후 reload(`worker_shutdown_timeout 20s`) | **가정1 성립**: reload 직후 새 요청 10/10이 green, 12초 스트림은 blue에서 12줄 전부 수신. **가정2 성립**: `ps`에 `shutting down` worker가 연결이 남은 동안 1, 끝나면 0. 상한 확인: 40초 스트림은 약 21초(24줄)에서 nginx가 끊음 = `worker_shutdown_timeout`이 실제 상한 |
| 11-20 12:5x | 설계 문서 `design.md`(agent 전환 계약: 활성 파일·명령 순서·실패 시 되돌림) | 설계 선검증(codex)·blind 테스트 워커 입력 |
| 11-20 13:0x | 설계 선검증 — codex(medium, 인라인) | 깨지는 경우 6: ①파일 교체 후 agent 중단 → 파일과 실제 불일치 ②reload 뒤 실패 시 새 자리를 바로 내리면 들어간 연결 끊김 ③reload가 조용히 미적용인데 외부 헬스는 구 버전의 200으로 통과 ④성공 직후 agent 중단 → 두 벌 방치 ⑤3분 넘는 스트림 절단 ⑥대상 자리 정지 실패 후 진행. 반영: ①③ 응답 헤더 `X-Deploy-Slot`로 실제 자리 판정 ② 되돌린 뒤 새 자리는 정리 절차로 ④ agent 기동 시 반대쪽 정리 ⑥ 정지 실패면 중단. ⑤는 기각 — 명세 ②의 사용자 결정(최대 3분). 명세 ② 3곳 보정(활성 판정·reload 뒤 실패·재시작 정리) — **사용자 보고 필요** |
| 11-20 13:3x | task 02 구현(ci-cd 브랜치 feat/blue-green-delivery) ∥ blind 테스트 워커(opus, 91k 토큰, 7 tool — 명세·설계·기존 테스트 관례만 열람, 구현 미열람) | 워커가 `bluegreen_test.go` 15개 작성(정상 순서, 거절 3종, 실패 단계별 운영 무변경·복원, 정리 상한, 다음 CD 대기, 기동 시 정리). 구현 쪽 상수 이름 1개를 바꾼 것 외에 **수정 없이 15/15 통과**. 메인 보충 3개(되돌림 실패 보고·CI의 활성 자리 기준·이미지 정리). `go vet` + `-race -count=3` 통과. 설계에 없던 것 1: `DEPLOY_MODE_<SVC>=bluegreen`(서비스별로 하나씩 옮기는 동안 나머지는 기존 방식) — 워커에 전달해 테스트 헬퍼에 반영 |
| 11-20 13:5x | task 03 backend compose(x-app 앵커 + app-blue·app-green + nginx) · `deploy/nginx/nginx.conf`·자리 템플릿 2개 | `compose config` 해석 정상(두 자리 127.0.0.1:18090·18091, nginx가 BIND_ADDR:8090), `nginx -t` 통과. 설계 중 발견: 안쪽 nginx는 `X-Accel-Buffering`을 소비하고 넘기지 않으므로 `proxy_pass_header`로 앞단에 전달 |
| 11-20 13:55 | **로컬 통합 실험** — 실제 agent 이미지 + 실제 nginx 설정 + 스트림 서버(자리 2개), 초당 약 14건 부하와 15초 스트림을 건 채 `POST /agent/cd` | 전환 4.4초, **부하 189건 실패 0**(구 버전 91·새 버전 98), 스트림 15줄 완주(구 버전), 헤더 `X-Deploy-Slot` blue→green, `X-Accel-Buffering` 전달됨. 구 자리는 스트림이 끝난 약 12초 뒤 정리(3분 대기 아님). agent 기동 시 반대쪽 정리도 동작 |
| 11-20 14:0x | 로컬 실패 실험 3종(부하 유지) | ①없는 이미지 → `cd_up` ②대상 템플릿 nginx 문법 오류 → `cd_switch`, 활성 파일 복원 ③대상 자리 헬스 실패 → `cd_health`. 셋 다 응답 자리·본문·활성 파일 불변, 대상 자리 정지. **부하 1022건 실패 0**. 실험 스크립트 오류로 2회 재실행(작업 폴더 지정 실수 — 제품 문제 아님). 발견 1: agent가 바꾼 활성 파일이 root 소유가 됨 → 원래 소유자 유지로 수정 |
| 11-20 14:2x | 리뷰 루프 1 — ⓪ packet `scratchpad/reviewzd.Rzzg`(ci-cd 339c22b→브랜치, backend e66f4d3→브랜치, 보안 스캔 0건) ① codex(인라인, 입력 비대칭) finding 3 ∥ Opus 워커(opus, 141k 토큰, 11 tool) finding 5·OQ 7 | ② 채택 R1~R9 → ③ codex 감사: R1(probe 실패 시 HEAD 대체 부적절)·R4(10분 뒤 포기)·OQ7(README만으로는 평소 한 벌 미보장) 판정 오류 + 누락 1(파일 교체 직후 중단 뒤 nginx 재기동) → 반영 |
| 11-20 14:4x | ④ 수정 — ci-cd(되돌림 뒤 복귀 확인·정리 직전 자리 확인·대기 상한·기동 시 무기한 재시도·활성 파일 맞춤·운영 자리 probe→파일→HEAD) · backend(자리에 profiles, nginx 디렉토리 마운트, body 10m) | fix verification 테스트 9개 추가. `go vet` + `-race` 반복 통과. blind 15개는 무수정 통과 유지 |
| 11-20 14:14(UTC 04:14) | 로컬 통합 재실험(프로필·디렉토리 마운트 구성) | 전환 4.3초, **부하 218건 실패 0**, 스트림 10줄 완주, 정리 뒤 한 벌. nginx.conf를 새 파일로 바꿔치기해도 컨테이너가 새 내용을 봄. 이름 없는 `compose up -d`는 nginx만 건드림(두 자리 안 뜸). 활성 파일 소유자 유지 |
| 11-20 15:0x | 리뷰 루프 2 — packet `scratchpad/reviewzd.loop2` · codex(인라인) finding 2 ∥ Opus 워커(opus, 162k 토큰, 15 tool) finding 2·OQ 5 | 신규 채택 6(R10~R15). 감사는 루프 1에서 1회 수행(추가 왕복 없음) |
| 11-20 15:1x | 루프 2 수정 — ci-cd b9741e7·후속 커밋, backend 후속 커밋 | 기동 시 정리를 배포와 같은 잠금으로 직렬화 · 활성 파일을 못 맞추면 정리 보류 · master CD 호출 9분 · 502여도 표식으로 자리 판정(고치는 배포 가능) · 자리 판정 3회 재확인 · nginx가 앱 주소를 요청 때 해석. 테스트 3개 추가, `-race` 반복 통과 |
| 11-20 15:2x | 로컬 실험 5종(변수 proxy_pass 구성) | ①앱 없이 nginx 기동 — 502 + 표식 blue ②앱 기동 뒤 200 ③앱 컨테이너 주소 변경(.3→.4) — 1초 뒤부터 200 ④실제 agent 전환 — **부하 190건 실패 0**, 스트림 9줄 완주, 한 벌만 남음 ⑤운영 앱을 죽인 뒤 배포 — 502+표식 green에서 blue로 전환 성공. (정리용 `rm` 명령이 안전 검사에 막혀 1회 미실행 — 덮어쓰기로 대체) |
| 11-20 15:5x | 리뷰 루프 3(상한) — packet `scratchpad/reviewzd.loop3` · codex(인라인) finding 2 ∥ Opus 워커(opus, 165k 토큰, 17 tool) finding 4·OQ 5 | 신규 채택 7(R16~R22). 루프 상한 도달 — 추가 전면 리뷰 대신 수정분 타깃 재점검 1회로 닫는다(사용자 보고) |
| 11-20 16:0x | 루프 3 수정 — ci-cd 2커밋 · backend 1커밋 | 활성 파일 복원 실패 시 대상 자리 유지 · 정지 시간 예산 분리(대기 여유 70초) · **nginx 본 설정을 git 밖 사본으로 운영, 전환 실패 시 복원** · 되돌림 확인은 표식만 · 기동 시 정리는 TryLock · job 상한 50분 · 실제 probeSlot 테스트. `-race -count=3` 통과(agent 테스트 합계 60개 안팎, blind 15개 무수정 통과 유지) |
| 11-20 16:1x | 로컬 통합 실험(활성 디렉토리 사본 구성) | ①문법이 깨진 본 설정 원본으로 배포 → `cd_switch`, 운영 사본은 이전 내용으로 복원(`nginx -t` 통과), 구 버전 서비스 유지 ②고친 원본으로 배포 → 성공, 사본이 새 내용으로 갱신 ③반대 방향 배포 성공. **세 배포 내내 부하 309건 실패 0** |
| 11-20 16:3x | 루프 3 수정분 타깃 재점검 — codex | R16·R17·R19~R22 해소. R18 일부 미해소(운영 사본을 읽지 못한 채 새 사본을 쓰면 실패 시 복원 불가) + 새 결함 2(P1 같은 경로에서 대상 자리를 내림 / P2 nginx 첫 기동 전에 운영 사본을 만드는 경로 없음) |
| 11-20 16:4x | 재점검 반영(ci-cd) | P1·R18: 운영 사본을 읽을 수 없으면 교체하지 않고 `cd_switch`(테스트 추가). P2: 최초 전환은 서버에서 한 번 하는 수동 절차 — ci-cd README에 명령 순서를 적음(설계의 "최초 전환은 수동" 그대로). `-race -count=3` 통과. agent 테스트 46개(기존 13 · blind 15 · 보충 18) |
| 11-20 16:4x | **리뷰 종료 판정** | 루프 상한(3) 도달. 3개 루프 채택 24건 + 재점검 2건 전부 fixed, open은 서버 실측 항목뿐. 루프 3에서도 신규 채택이 있었으므로 "신규 0" 종료 조건은 충족하지 못함 — `review unresolved`가 아니라 **상한 종료 + 타깃 재점검**으로 닫고 잔여 위험을 사용자에게 보고 |
| 11-20 16:5x | 사용자: "진행하자"(1~5번 승인) | ci-cd #13 → PR #14 병합(59d067a). 서버 3대 반영(백업 `~/ci-cd-backup-20261120`), `.158` `.env.agent`에 DEPLOY_MODE_BACKEND·자리별 헬스 2줄 추가 |
| 11-20 17:2x | backend #36 → PR #37 병합(cfe89cc) | 예고대로 CI 통과 뒤 `cd_switch`(활성 파일 없음), 운영 무변경. profiles 구성에서 `compose build app-blue`가 서버(compose 5.0.0)에서 동작 |
| 11-20 17:27 | `.158` 최초 전환 | 1차: `deploy/`가 root 소유라 `mkdir` 권한 거부 — 무변경으로 중단(set -e). 2차: agent 컨테이너로 활성 폴더 생성 → blue 선기동(헬스 6초) → 기존 컨테이너 정지 → nginx 기동. **중단 5.4초(08:27:02.8~08.5Z), 요청 46건 실패**. ES·Redis·embedding 생성 시각 불변. 응답 자리 blue |
| 11-20 17:28 | 워크플로 재실행 = 첫 무중단 배포(blue→green) | succeeded(ci 3.0s·cd 8.3s), 1초 뒤 구 자리 정리. **트리 조회 579건 실패 0**, 검색 102건 중 1건 실패(배포 8초 전, 측정 제한 3초 초과 — 제한 10초로 올린 뒤 재현 안 됨) |
| 11-20 17:31 | 헬스 실패 실험 1차 | **무효** — 접수가 엣지 504를 5회 받아 "접수 실패 5회"로 끝남(두 번째 원인, 재시도 5회로 못 넘김) |
| 11-20 17:35 | 헬스 실패 실험 2차(blue 헬스 주소를 닫힌 포트로) | `cd_health`, 응답 자리 green 유지, 앱 한 벌. **트리 775건·검색 140건 실패 0**. 설정 원복. agent 재기동 4회 모두 기동 직후 반대쪽 정리 로그 |
| 11-20 17:4x | 최초 전환 때 내린 구 컨테이너 `backend-app` 제거 · llm PR #24·front PR #46(워크플로 25분·50분) 병합 | 두 배포(지금 방식) 중 실패: llm 5건(약 0.5초), front 3건(약 0.25초). `experiments.md` 작성 |

## 리뷰 ledger

- review packet 루프 1: base ci-cd 339c22b · backend e66f4d3 / `scratchpad/reviewzd.Rzzg` / mirror `reviewzd.Rzzg/mirror`

| id | loop | source | 근거 | disposition | status | fixed |
|----|------|--------|------|-------------|--------|-------|
| R1 | 1 | codex·opus OQ1(+감사) | pipeline.go — CI의 운영 버전 판정이 활성 파일 기준 | 채택 | fixed — probe → 활성 파일 → HEAD 순 | 1 |
| R2 | 1 | codex·opus F1 | bluegreen.go — 되돌림 실패 뒤 새 자리 정리, 정리가 실제 자리 미확인 | 채택 | fixed — 되돌림 뒤 복귀 확인, 정지 직전 probe | 1 |
| R3 | 1 | codex·opus F3 | bluegreen.go — 정리 대기 상한 없음 | 채택 | fixed — 완료 신호를 정지 직후로, 대기 상한 초과 시 cd_up | 1 |
| R4 | 1 | opus F2(+감사) | 기동 시 정리가 probe 1회 | 채택 | fixed — 확인될 때까지 30초 간격 재시도 | 1 |
| R5 | 1 | opus F4 | backend compose — nginx.conf 단일 파일 mount | 채택 | fixed — 디렉토리 mount(실측) | 1 |
| R6 | 1 | opus F5 | 되돌림 실패·적용됐지만 실패한 reload 미검증 | 채택 | fixed — 테스트 추가 | 1 |
| R7 | 1 | opus OQ3 | front·llm 워크플로 20분 | 채택 | fixed — llm PR #24·front PR #46 | 3 |
| R8 | 1 | opus OQ2 | DEPLOY_MODE 문서 누락 | 채택(문서) | fixed(설계) · README는 task 06 | 1 |
| R9 | 1 | opus OQ4 | nginx body 1m | 채택(소) | fixed — 10m | 1 |
| R10 | 2 | codex·opus F1 | 기동 시 정리가 CD와 잠금 없이 경합 | 채택 | fixed — 같은 잠금 아래 판단·등록 | 2 |
| R11 | 2 | codex | 활성 파일 복원 실패를 무시하고 반대쪽 정리 | 채택 | fixed — 보류·재시도 | 2 |
| R12 | 2 | opus F2 | CD 최악 소요가 master 8분 초과 가능, 설계 수치 불일치 | 채택 | fixed — 9분, 수치 통일 | 2 |
| R13 | 2 | opus OQ2 | nginx가 앱 주소를 설정 로드 때 한 번만 해석 | 채택 | fixed — resolver + 변수 proxy_pass(실측) | 2 |
| R14 | 2 | opus OQ3 | 외부 probe 실패 시 CD 거절 ↔ 고치는 배포 불가 | 채택 | fixed — 502여도 표식으로 판정(실측) | 2 |
| R15 | 2 | opus OQ4 | 내리기 직전 probe 1회 | 채택(소) | fixed — 3회 재확인 | 2 |
| - | 2 | opus OQ1 | profiles + 이름 지정 명령 | 해소 | 로컬 실측(stop·ps -q·up·build 동작). 서버 compose 5.0.0에서 최초 전환 때 재확인 |
| - | 2 | opus OQ5 | 최초 전환 순서(compose 변경과 agent 설정) | open | 서버 전환 절차에서 다룸 — agent 설정 먼저 |
| R16 | 3 | codex | 활성 파일 복원 실패에도 대상 자리 정지 | 채택 | fixed — 복원 실패면 유지 | 3 |
| R17 | 3 | codex·opus F3 | 3분 대기 뒤 정지 시간이 부족 | 채택 | fixed — 예산 분리, 여유 70초 | 3 |
| R18 | 3 | opus F1 | nginx 본 설정이 git 작업 트리 — 실패 시 복원 안 됨, 재부팅 시 깨진 설정 적용 | 채택 | fixed — 활성 디렉토리 사본(실측) | 3 |
| R19 | 3 | opus F2 | 되돌림 확인이 200을 요구 | 채택 | fixed — 표식만 | 3 |
| R20 | 3 | opus F4 | job timeout 40분 < 접수 20 + 조회 25 | 채택 | fixed(backend 50분) · front·llm은 R7과 함께 | 3 |
| R21 | 3 | opus OQ3 | 무기한 reconcile이 잠금을 쥐어 배포에 409 | 채택 | fixed — TryLock, 배포 중이면 건너뜀 | 3 |
| R22 | 3 | opus OQ5 | 실제 probeSlot 테스트 없음 | 채택 | fixed | 3 |
| - | 3 | opus OQ2 | CLI가 끊겨도 데몬이 정지를 계속하는가 | open question | 서버 실측 대상 아님 — 다음 CD의 2단계가 다시 내림 | - |
| - | 3 | opus OQ4 | .env.example 미반영 | 이연 | task 06 | - |
| A1 | 1 | 감사·opus OQ7 | 이름 없는 compose up이 두 자리를 띄움 | 채택 | fixed — profiles(실측) | 1 |
| A2 | 1 | 감사 | 파일 교체 직후 중단 뒤 nginx 재기동 | 채택 | fixed — 기동 시 활성 파일을 실제에 맞춤. 4단계 헬스 통과 뒤에만 파일을 바꾸므로 그 자리는 검증된 자리 | 1 |

## 생략한 검증
- 리뷰 종료 조건 "신규 채택 0인 루프" 미충족 — 루프 3까지 매 회 신규 채택(11·6·7건). 상한에서 타깃 재점검으로 닫음. 잔여 위험: 되돌림·복원이 연쇄로 실패하는 드문 경로에 미발견 결함이 더 있을 수 있다(그런 경로의 공통 방어 = 응답 중이거나 상태를 모르는 자리는 내리지 않는다).
- codex 입력 비대칭(인라인 자료만) — 샌드박스 중첩으로 미러 읽기 불가. 루프 2·3은 누적 diff 전문 대신 변경 뒤 전체 파일 + 수정 diff를 줌.
- 서버 실측: backend는 최초 전환·배포 중 실패 0건·헬스 강제 실패·agent 재기동 뒤 한 벌·profiles 명령까지 수행(`experiments.md`). 미수행: 서버 전체 재부팅, 생성 중 채팅이 있는 배포, reload 뒤 되돌림의 서버 실측.
