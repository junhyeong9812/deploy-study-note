# 요구사항 명세 — llm 래핑 서버 구현
| 칸 | 내용 |
|----|------|
| ① 목표·대상 | study-note-deploy-system-llm: compose(ollama+wrapper) + FastAPI — /rewrite·/health 구현, /digest 501(계약만). D1~D8 준수 |
| ② 경계·불변식 | Ollama 호스트 비노출·모델 env 고정 · Semaphore(2) 즉시 503 · JSON 3단 검증(스키마→pydantic→재시도 1회→422) · 시크릿/사설IP repo 0 |
| ③ 기준소스 | docs/design/wrapper-api.md (리포 내) |
| ④ 금지영역 | main 직접 push · 다른 리포 변경 · Ollama 포트 호스트 바인딩 |
| ⑤ 검증 방법 | 단위(거절·검증·재시도 경로 우선, httpx mock) → .164 실기동 스모크(qwen3:8b pull → /rewrite 실호출 스키마 통과 → 동시 3발 시 503 확인) → 듀얼 리뷰 1패스 → 머지 |
| ⑥ stakes | 중간 |
- 자율성 auto · load-bearing 가정: (1) qwen3:8b가 format 스키마 출력을 대체로 준수(재시도 1회 내 수렴) (2) Ollama 내부 큐+NUM_PARALLEL=1로 직렬화 충분
- 프로세스: 이슈 → 브랜치 → 구현 → PR → 리뷰 → main 머지 (사용자 승인: 2026-08-24 머지까지 위임)
