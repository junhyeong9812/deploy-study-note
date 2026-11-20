# 요구사항 명세 — 서버별 프로젝트 폴더 3개 스캐폴드
| 칸 | 내용 |
|----|------|
| ① 목표·대상 | `front/`(.9) `backend/`(.158) `qwen-server/`(.164) 생성 · 각각 `git init` · README에 프로젝트 이름만 · 초기 커밋 1개 |
| ② 경계·불변식 | 커밋 규칙 `type(scope): title` · AI attribution 금지 · 기본 커밋만(코드 없음) |
| ③ 기준소스 | README.md §2 배치 |
| ④ 금지영역 | 원격 생성·push · 다른 폴더 변경 |
| ⑤ 검증 방법 | `git log --oneline` 3개 · `git status` clean |
| ⑥ stakes | 낮음 |
- 자율성 auto · load-bearing 가정: 폴더명 = README §2 역할명(front/backend/qwen-server)
