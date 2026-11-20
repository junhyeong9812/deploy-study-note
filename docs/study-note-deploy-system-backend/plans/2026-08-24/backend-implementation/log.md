# log — backend-implementation
| 시각 | 사건 | 결과 |
|---|---|---|
| 2026-08-24 | 인터뷰 4문 + 멱등 추가 합의 | Kotlin/Spring · front 렌더 · Actions→front→backend 갱신 · www:11000 재활용 · SHA 멱등 |
| 2026-08-24 | 이슈① 머지(PR #2) | 4컨테이너 기동·nori 실증·로그 파이프라인 관통(.164→.158 XADD)·메모리 가정 실증 |
| 2026-08-24 | 이슈② 구현·실기동 | 실기동 결함 4건 검출·수정: ①embedding 로딩 전 /embed(depends_on healthy+타임아웃) ②ES 본문 ISO-8859-1 인코딩(UTF-8 바이트 전송) ③git quotepath 한글 경로 ④spring redis 기본 localhost. 청킹 바이트/문자 혼동은 단위 테스트가 검출 |
| 2026-08-24 | 전체 색인 성공(PR #4 머지) | 616파일→911청크 783s · ES count=911 일치 · duplicate skip 실증 · 한국어 BM25 스모크(lsm-tree 톱히트) |
| 2026-08-24 | 미완 | 증분 sync 실검증은 study-note 다음 실제 push 때(파이프라인 diff 경로는 단위로 커버) · kNN·RRF는 이슈④ |
| 2026-08-24 | 이슈③(PR #6)·④(PR #8) 머지 | 콘텐츠 API(트래버설 차단·한글 경로) · 검색 API(RRF·폴백 실증 — wrapper 정지 상태 검색 정상) |
| 2026-08-24 | 듀얼 리뷰 ① 시작 | packet=1cf6dc1..main(구현 누적) · codex ∥ Opus 워커. (절차 메모: 이슈별 머지를 먼저 진행해 리뷰가 사후가 됨 — finding은 후속 PR로 반영) |
| 2026-08-24 | ②종합·③감사·④수정(PR #10 머지) | 채택 B1~B19(+감사 3: BIND fail-closed·MAX_EMBED 9000·거대 문단 분할 / B13은 "sha=트리거 힌트·색인=HEAD 수렴"으로 설계 명문화 기각) · post-fix 재점검 3건 반영(4xx 구분·404 한정·surrogate 분할) |
| 2026-08-24 | **rewrite 제안 필터 실측 기각** | "세마포어가 뭐야"에 모델이 doc_kind=question 제안→정리·정답 전멸. 하드 필터=명시 파라미터만, 제안은 로그 축적([구현 검증] #7) |
| 2026-08-24 | full 재색인(B7 실증) | 630파일→950청크·고아 정리·검색 재검증. 테스트 22건 green |

## 리뷰 ledger (듀얼 1패스 — 상세 synthesis: scratchpad/review-backend)
채택 fixed: B1 RRF키·B2 doc_kind필터·B3 ES일원화·B4 kNN폴백·B5 title·B6 전역봉투·B7 full/고아/강등·B8 git행·B9 diff테스트·B10 임베딩상한+차원·B11 MAXLEN/requestId·B12 상수시간·B16(부분: 진행로그)·B17·B18·B19 + 감사3 + 재점검3
기각(근거 기록): B13(수렴 멱등 설계 명문화)·B15(평면 목록=계약. front가 트리 구성)
부분/이연: B14(fail-closed 채택·requirepass는 [구현 검증] #6)·B16 refresh 전략([구현 검증] #4)

## 완료 요약 — backend 1차 (이슈 4 + 리뷰 이슈 1, PR 5개 머지)
- API: /internal/sync(멱등·full)·/internal/sync/status·/api/docs·/api/doc·/api/search — 전부 봉투·로그 규약
- 실측: full 색인 630파일→950청크 ~13분 · 검색(RRF·폴백·필터) 정상 · 크로스호스트 로그 큐 가동
- 남김: 증분 sync 실검증(다음 실제 push 때) · [구현 검증] 7건 · study-note 이슈 문서 + 이해 게이트(다음 턴)
| 2026-08-25 | study-note 재구조화(cs/practice/project/lab/portfolio) + db-engine-lab→db-engine(리포·폴더) | 증분 sync 실검증: rename 1224건(D+A)→796청크 10분 · 문서 push 6파일→35청크 31s · 구 topic 전량 소멸·새 경로 검색 정상. 최종 1027청크 |
| 2026-08-25 | study-note backend issue1~5 정리 push | 이해 게이트 대기 |
| 2026-08-27 | 이해 게이트 통과(교정 3) + 사용자 재결정 | 트리 API 채택(기각 번복 — sync 시 생성·sha 태깅)·레이어 재편 지시·issue4 문서 상세화 |
| 2026-08-27 | #11 레이어 재편(PR #13)·#12 /api/tree(PR #14) 머지 | api/usecase/domain/infra·TreeBuilder(리프=주제)·24건 green·실기동 스모크. 배포 함정 1: rsync --delete 누락→옛 패키지 잔존→빈 충돌(재발 방지: --delete 표준화) |
| 2026-08-28 | 게이트(2차) 통과 + 아키텍처 재결정 | #15 도메인-우선 재편(PR #16): <도메인>/{api,usecase,domain}+shared·DIP 포트 7종(usecase 소유·shared 다중 구현)·테스트 포트 mock 전환 — 24건 green·실기동 200 · D3 코테 서머리 교정(PR #17) |
| 2026-09-01 | 채팅 라운드 codex 리뷰 | F1 packet 오탐(채팅 새 파일이 git show에 안 담김 — 실코드 E2E 검증완료) · **채택 F2~F8(전부 브리지 보안)**: 인증(공유 시크릿 상수시간)·동시 1건·출력/본문 상한·chunked 거부·도구 전면 차단(프롬프트 주입 완화)·stderr 비노출. backend는 X-Bridge-Secret 전달(PR #29). F5(스트리밍 vs 버퍼) = 에스컬레이션은 비스트리밍 확정(문서화) |
| 2026-09-01 | 인증 브리지 E2E | 로컬 무인증 401·인증 200 · 엣지 에스컬레이션 재관통(SSTable 질문) |
