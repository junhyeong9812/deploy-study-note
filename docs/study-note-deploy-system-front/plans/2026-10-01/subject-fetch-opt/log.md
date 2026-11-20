# log — (a) subject 페이지 fetch 최적화

- 2026-10-01 | 명세 합의(auto)+set-state | SPEC=1
- 2026-10-01 | 구현 | page.tsx subject 분기: 케이스 선판별 후 필요한 문서만 fetch(다중목록=README만·chapter=챕터+README·단일=그 문서만). 단일 선택 README→contentDocs[0] 교정
- 2026-10-01 | 검증 | tsc 클린·vitest 12·next build Compiled
- 2026-10-01 | 리뷰 | Opus 적대적(codex 사용량한도). 주경로 verified. **F1 채택·fixed**: README-only is_subject 리프에서 `===1`이 0 제외→비동등 → `<=1` + doc=contentDocs[0]??readme로 복원(PaneReader 유지). F1-보조(에러폴백 비동등) 저위험 수용. 재검증 tsc·build 통과
