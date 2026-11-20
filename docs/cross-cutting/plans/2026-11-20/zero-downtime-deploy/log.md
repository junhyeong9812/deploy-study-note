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

## 리뷰 ledger

## 생략한 검증
