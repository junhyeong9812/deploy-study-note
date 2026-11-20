# docs — 작업 기록

| 폴더 | 대상 |
|---|---|
| `study-note-deploy-system-front/plans/` | front(.9) 단독 작업 |
| `study-note-deploy-system-backend/plans/` | backend(.158) 단독 작업 |
| `study-note-deploy-system-llm/plans/` | llm(.164) 단독 작업 |
| `cross-cutting/plans/` | 횡단관심사 — 2개 이상 리포/서버·엣지·인프라에 걸치는 작업 |

공통 규약: [로그 규약](logging.md) — requestId:server-name:message, Redis Stream 중앙 큐.

작업 폴더 규칙: `<대상>/plans/YYYY-MM-DD/작업명/` = `requirement-spec.md` + `log.md`.
