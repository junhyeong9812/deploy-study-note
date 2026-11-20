# 요구사항 명세 — backend 1차 (Kotlin/Spring, .158)
| 칸 | 내용 |
|----|------|
| ① 목표 | ⑴ compose: app(:8090)+ES(nori, 내부전용)+로그 Redis(:6379 LAN)+BGE-M3(기존 이미지, 내부전용) ⑵ sync API: 비밀키 검증·**commit_sha 멱등**(마지막 처리 SHA/처리중 SHA와 동일→skip, single-flight 1건, 완료 후에만 SHA 전진) → pull→diff→청킹→임베딩→ES 색인 ⑶ 콘텐츠 API(트리·원문 JSON — 렌더는 front) ⑷ 검색 API(llm /rewrite 폴백 연동→BM25+kNN→RRF→봉투) ⑸ requestId 발행+로그 규약 |
| ② 불변식 | es-index.md D1~D5 준수 · LAN 전용 · 봉투·로그 규약 llm 동일 · 시크릿/IP repo 0 |
| ③ 기준소스 | docs/design/es-index.md · docs/logging.md · llm API 계약 · study-note 실구조 |
| ④ 금지 | main 직접 push · study-note 수정(Actions는 front 단계) · jun-bank 무접촉 · 13000번대 회피 |
| ⑤ 검증 | 단위(diff·청킹·폴백·멱등 경로 우선) → 실기동 전체 색인 record-level(count·sample) → 한국어 실검색 스모크 → 中 듀얼 1패스 → 이슈별 PR |
| ⑥ stakes | 중간 |
- auto · 이슈 분해: ①스캐폴드+compose ②sync 파이프라인 ③콘텐츠 API ④검색 API
- load-bearing 가정: ⑴ .158 15Gi에 ES(heap 2G)+app+BGE-M3 동시 가동 ⑵ nori가 ES 8.x 이미지 빌드로 설치 — 이슈① 스모크로 실증
- 합의: 2026-08-24 (멱등 조항 사용자 추가 포함)
