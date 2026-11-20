# log — zero-downtime-deploy

| 시각(KST) | 사건 | 결과 |
|-----------|------|------|
| 11-20 12:0x | 사전 실측(서버 3대 자원·포트·컨테이너, 두 벌 공존 시 충돌할 백그라운드 작업 grep) | 메모리 여유 충분, compose에 이름·포트 고정, backend 주기 작업 없음(sync는 요청 구동·공유 볼륨) |
| 11-20 12:1x | 인터뷰(선택 질문 4) → 명세 초안 | 사용자 합의 대기 |
| 11-20 12:3x | 사용자: "진행하자" | set-state spec-approved / mode auto. 기준 SHA: ci-cd 339c22b · llm 92dab17 · backend e66f4d3 · front 7b7395c |
| 11-20 12:41 | task 01 가정 실증 — 로컬 nginx 1.27 + 스트림 서버 2개(blue·green), 스트림 2개를 물린 채 대상 변경 후 reload(`worker_shutdown_timeout 20s`) | **가정1 성립**: reload 직후 새 요청 10/10이 green, 12초 스트림은 blue에서 12줄 전부 수신. **가정2 성립**: `ps`에 `shutting down` worker가 연결이 남은 동안 1, 끝나면 0. 상한 확인: 40초 스트림은 약 21초(24줄)에서 nginx가 끊음 = `worker_shutdown_timeout`이 실제 상한 |
| 11-20 12:5x | 설계 문서 `design.md`(agent 전환 계약: 활성 파일·명령 순서·실패 시 되돌림) | 설계 선검증(codex)·blind 테스트 워커 입력 |

## 리뷰 ledger

## 생략한 검증
