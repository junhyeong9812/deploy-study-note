# 요구사항 명세 — front 1차 (Next.js, .9:11000)
| 칸 | 내용 |
|----|------|
| ① 목표 | study-note-deploy-system-front: ⑴ 위키 — /api/tree 사이드바 + 주제 페이지 1/2/3 **3탭(가림 없음)** + md SSR 렌더(/api/doc) ⑵ 검색 — **헤더 상시 검색바** + 결과(경로·헤딩·스니펫, rewrite/dense 뱃지) ⑶ BFF — 브라우저→front 라우트핸들러→backend(LAN) 프록시, /api/sync 중계(Actions→backend, 헤더 패스스루) ⑷ study-note Actions workflow(main push→sync 호출) + SYNC_SECRET gh secret 등록 ⑸ 로그 규약: **진입 서버가 requestId 발행**(front)→X-Request-Id로 backend 전달(규약 문서 갱신), stdout+Redis XADD |
| ② 경계·불변식 | backend 계약(봉투) 소비만 — backend 무수정(규약 문서 제외) · 공개 read-only(쓰기 경로는 sync 중계뿐, 비밀 헤더 필수) · IP·시크릿 repo 0(.env) · 오라클 무접촉(www:11000 재활용) |
| ③ 기준소스 | backend README(API 계약)·docs/logging.md·docs/design/es-index.md |
| ④ 금지 | main 직접 push · backend 코드 수정 · 오라클 conf 변경 |
| ⑤ 검증 | 컴포넌트 단위 최소(md 렌더·트리 변환) → .9 실기동(트리·문서·검색·sync 중계) → **엣지 E2E**(https://www.junproject.xyz 실응답) → 中 셀프체크+codex 1회(front는 표시 계층 — 듀얼 풀패스는 과함, 사유 기록) → 이슈별 PR |
| ⑥ stakes | 중간(외부 노출 재개) |
- auto · 이슈: ①스캐폴드+compose ②위키 뷰 ③검색 ④sync 중계+Actions+E2E
- load-bearing 가정: ⑴ .9(4C/2.1GHz)에서 Next 빌드·SSR 감당 ⑵ www conf(11000 프록시)가 그대로 유효 — 이슈① 배포 직후 엣지 실응답으로 실증
