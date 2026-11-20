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
| R7 | 1 | opus OQ3 | front·llm 워크플로 20분 | 채택 | open — 두 repo PR에서 반영 | - |
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
| A1 | 1 | 감사·opus OQ7 | 이름 없는 compose up이 두 자리를 띄움 | 채택 | fixed — profiles(실측) | 1 |
| A2 | 1 | 감사 | 파일 교체 직후 중단 뒤 nginx 재기동 | 채택 | fixed — 기동 시 활성 파일을 실제에 맞춤. 4단계 헬스 통과 뒤에만 파일을 바꾸므로 그 자리는 검증된 자리 | 1 |

## 생략한 검증
