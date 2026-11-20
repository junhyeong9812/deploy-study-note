# 요구사항 명세 — 응답 정규화(envelope)
| 칸 | 내용 |
|----|------|
| ① 목표 | 업무 응답을 success/error 2형 봉투로 정규화 — backend가 `success` 플래그 하나로 분기. `{"success":true,"data":{...}}` / `{"success":false,"error":{code,detail?,retry_after?}}` |
| ② 불변식 | 상태코드 의미 유지(200/503/422/501) · /health는 인프라 엔드포인트라 봉투 제외(docker healthcheck 계약) · FastAPI 입력검증 422도 봉투로 통일 |
| ③ 기준소스 | docs/design/wrapper-api.md D2(개정 포함) · 사용자 지시 2026-08-24 |
| ④ 금지 | 다른 리포 변경 |
| ⑤ 검증 | 단위 테스트 전면 갱신(green) · .164 재배포 스모크 1회 |
| ⑥ stakes | 낮음~중간(계약 변경이나 소비자 미존재 — backend 미구현) → 셀프체크+테스트 |
- auto · 절차: 이슈 → 브랜치 → 구현 → PR → 머지
