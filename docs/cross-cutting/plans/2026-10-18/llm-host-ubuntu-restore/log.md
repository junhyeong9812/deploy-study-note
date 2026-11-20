# log — llm-host-ubuntu-restore

| 시각(KST) | 사건 | 결과 |
|-----------|------|------|
| 10-18 00:23 | .164 Ubuntu 재부팅 후 실측 | uptime 0min · nvidia-smi 정상(595.99.02, RTX 2070 SUPER) — 드라이버 불일치 해소 · 컨테이너 4개 Exited 그대로(unless-stopped인데 미기동) |
| 10-18 00:24 | `docker start llm-ollama` → `llm-wrapper ci-cd-agent` | 3개 healthy · ollama 내부 GPU 인식 · `ollama ls` qwen3:8b 존재 |
| 10-18 00:25 | LAN 확인 | .158→:8000/health ok(qwen3:8b) · .9→:15001/health ok(agent) |
| 10-18 00:26 | /rewrite 직접 호출 5회 | **전부 upstream_timeout(5s)** — 모델 미적재 콜드스타트. 수동 프리로드(25.9s) 후에도 2회 timeout |
| 10-18 00:28 | 동일 요청 장시간 타임아웃 재현 | 1.36s 정상 → 이후 /rewrite 1.46s·1.43s success. 콜드 직후 첫 몇 건만 5s 초과(원인 미확정 — 구조화 출력 첫 호출 추정) |
| 10-18 00:28 | 라이브 /search | backend 로그 `rewrite=true dense=true hits=10` — 복구 확인 |
| 10-18 | 원인 조사 부산물 | ①10-05 05:19 <LAN>.114에서 SSH 다수 접속 직후 05:23 컨테이너 일괄 정상 종료(exit 0) — 수동 stop/down 가능성(미확정) ②metrics-agent 서비스가 `/home/jun/metrics-agent/agent.py` 없음으로 64만 회 재시작 루프 → 다운 알림 부재의 원인 ③엣지가 curl 기본 UA 차단(로컬 검증 시 000) |

## 생략한 검증
(없음 — stakes 낮음, 설정 무변경)
