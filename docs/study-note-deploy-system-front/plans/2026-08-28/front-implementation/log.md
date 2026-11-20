# log — front-implementation
| 시각 | 사건 | 결과 |
|---|---|---|
| 2026-08-28 | 인터뷰 3문 합의 | 3탭(가림X)·헤더 검색바·Actions+secret 위임 |
| 2026-08-28 | 이슈①~④ 구현·머지(PR #2·4·6·8) | 홈·위키(3탭)·검색·sync 중계 — 각 단계 .9 실기동+엣지 E2E |
| 2026-08-28 | **전체 루프 관통** | study-note push 429b95cc → Actions 202 → 엣지 → front → backend 증분 1파일/9청크 → last_sha 일치 |
| 2026-08-28 | codex 1회 리뷰(듀얼 생략 사유: 표시 계층, spec 명기) → fix PR #9 머지 | 7건: 채택3(requestId 전파·본문 상한 413·링크 hash 보존) 기각3(packet 오탐 2 — standalone·alias 실재/3탭 고정은 부재 허용 설계 위배) 부분1(vitest 6건). 실기동 413·401 확인 |

## 완료 요약 — front 1차 (이슈 4 + 리뷰 fix, PR 5개 머지, www.junproject.xyz 가동)
- 화면: 홈(버킷) · /wiki(트리·폴더·주제 3탭·md SSR·상대링크 치환) · /search(폴백 뱃지) — 전부 엣지 200
- BFF: /api/search·/api/sync(패스스루·4KB 상한) · requestId는 진입 서버(front) 발행→X-Request-Id 전파
- CD 사슬 완성: study-note push → Actions(SYNC_SECRET) → 엣지 → front → backend 색인 (실증: 429b95cc, 9.7s)
| 2026-08-28 | #10 features 재편(PR #11) | app=순수 라우팅·features/{home,wiki,search,sync}+shared(참조: squatting front-server 동형) · 챕터 3탭 고정+작성전 패널(코테 서머리 재결정 반영) · 미사용 /api/search 제거 — vitest 6·실기동·엣지 200 |
| 2026-08-28 | 시크릿 대장 | 루트 docs/secrets.md(로컬 전용) — SYNC_SECRET 기록·gh secret 관리 위임 접수 |
| 2026-08-31~09-01 | 레이아웃 라운드(이슈 #17·18·19·23 / PR #20·21·22·24) | 드릴다운 사이드바(피드백 6회 반영)·/tree 접이식·검색 자동완성(ES suggest·마커 강조)·표 CSS·횡스크롤 fix — 전부 자동 배포 |
| 2026-09-01 | backend #21 prev·#22 suggest 연동 | 배포 401 사건(시크릿 오등록+curl -f 부재 위장) 검출·교정 — 잔여: 워크플로 curl -f 일괄 추가 |
| 2026-09-01 | 문서 | docs/workflow/ 6종(deploy-study-note)·study-note 이슈 문서 5건·chat 설계·MVC vs WebFlux 비교 |
