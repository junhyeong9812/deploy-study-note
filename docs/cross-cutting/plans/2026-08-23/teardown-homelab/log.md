# log — teardown-homelab

| 시각 | 사건 | 결과 |
|---|---|---|
| 2026-08-23 21:2x | 3대 읽기 전용 인벤토리 실측 | jun-bank 5컨테이너+agent 가동 중 확인 · local-llm 8 · readlog 2 · 실험 잔재 다수. Readlog PG 30MB, 일일 백업 존재 |
| 2026-08-23 21:3x | 명세 작성 | requirement-spec.md — 사용자 확인 대기 |
| 2026-08-23 21:4x | 사용자 확인(AskUserQuestion) | 전부 삭제 · 불가역 볼륨 삭제 승인 · Ollama 컨테이너+호스트 둘 다 제거. set-state spec-approved + mode auto |
| 2026-08-23 22:1x | .9 실행 | readlog 최종 덤프(7 tables) → claude_bridge kill → compose down -v admin/api/mcp/web/core/server → 잔여 볼륨 3 · 이미지 10 삭제 → 홈 잔재 `~/_trash-20260823/`(32M) 이동 |
| 2026-08-23 22:1x | .158 실행 | embedding down(이미지·hf-cache 유지) · 잔여 볼륨 7 삭제 · 홈 잔재 이동 |
| 2026-08-23 22:1x | .164 실행 | llm down -v(ollama 컨테이너·모델 볼륨) · vllm/cache-split 등 이미지 전부 삭제 · builder prune · 홈 잔재 이동. 디스크 61G→14G 사용 |
| 2026-08-23 22:2x | 사용자 추가 지시 "덤프 불필요, 다 지워" | `~/readlog-backups` → _trash 이동 |
| 2026-08-23 22:2x | 검증 | jun-bank health 13080/13002(.9)·13001(.158)·13002(.164) 전부 200 · 호스트 ollama pid 1517 소멸(컨테이너 내부 프로세스였음, 유닛 없음) · 각 호스트 listening = jun-bank 포트 + 22 + 9100(metrics-agent)만 |

## 생략한 검증 / 잔여 (sudo 필요 — 사용자 터미널)
- `metrics-agent.service` 3대 · `intel-daily.timer/service`(.9) 중지+disable+유닛 삭제 — 암호 sudo라 미실행
- `~/_trash-20260823/` 3대 — 1주 뒤 `rm -rf` (지금은 이동만)

## 완료 요약
- 남은 것: jun-bank(gateway 13080 · core-green 13002 · mysql · jun-agent 13000/13100 · settlement .158:13001 · ledger .164:13002) + 재활용용 `embedding-embedding` 이미지·`embedding_hf-cache`(.158)
- 무접촉: 오라클 conf/인증서/DNS · 공유기 포워딩 9000/10000/11000/12000 · SSH 키
