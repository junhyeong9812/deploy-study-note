# log — 작업A: 위키 트리/색인 denylist (docs·templates)

## 진행 기록 (발생 시점 append)

- 2026-10-01 | 명세 합의(auto) + set-state | SPEC=1·MODE=auto·DEBT=0
- 2026-10-01 | choke point 실증 | 트리·전체/증분색인·/docs = allMarkdown/changedMarkdown 경유 / 챗봇·/doc = 클라이언트 doc_path 직접 → 목록필터+직접가드 2지점 필요
- 2026-10-01 | 구현 | PathGuard.isHidden(denylist={docs,templates}) 추가 → GitRepository.allMarkdown·changedMarkdown 필터 + ChatController 3핸들러 + ContentController /doc(404) 가드
- 2026-10-01 | 테스트 | PathGuardTest 신설(숨김·노출·유사접두·독립성). gradle test(JDK21, 출력 스크래치 리다이렉트 — repo의 .gradle/build/.kotlin가 root소유라) = **28 tests·0 failure**
- 2026-10-01 | 리뷰 packet | BASE=edc00af307d5a2f535f662b3aed9698a79f4537b · OUT=/tmp/tmp.OgU5G6GMEe · mirror=/tmp/tmp.UNJftojKlr · 보안스캔 통과
- 2026-10-01 | 듀얼 1패스 리뷰 착수 | codex(bg bet4i8v9p) ∥ Opus 워커(a48730e0b7f4eb834) 병렬

## 리뷰 ledger (듀얼 1패스 — 中)

- codex: bwrap loopback으로 미러 파일읽기 2회 실패 → **packet 인라인 방식**으로 3회차 성공(파일 미읽기, spec+diff 텍스트 리뷰). 확정 finding 0, open question 2(full 재색인 실행 여부·rename 처리).
- Opus 워커(미러 전수 접근): finding 0, 6렌즈 verified(file:line). codex open question 2건 실코드로 해소.
- **채택 finding: 0** (수정 없음 → ④ post-fix 재점검 비대상). 종료: 채택 0 + 대칭부담(applicable 렌즈 양쪽 커버, codex는 인라인 한정이라 미러근거는 Opus가 담당 — 비대칭 아님, 둘 다 무결론 일치).
- verified 렌즈: API예외전파(/doc 404·chat 422 무음없음) · 세그먼트정확성(PathGuard.kt:13, 테스트 커버) · 완전성(suggest=ES색인→필터로 덮임, 다른 노출경로 없음) · 통합(orphan=SyncService:87→IndexingService:85 deleteStale, rename=parseNameStatus D+A분해 후 필터) · 네이밍 · 과잉구현(없음).
- open(운영, 결함아님): 배포 후 full 재색인 1회 필요(증분으론 stale 안 지워짐) — spec ②·⑤ 요구사항, 배포 runbook에서 수행·검증.
- 참고(조치 불요): shared→content import(spec 지정·기존 의존 있어 새 위반 아님) · /history는 커밋메타만(문서내용 아님, 범위 밖) · /doc 404 vs chat 422(spec 둘 다 허용).
- codex 환경 제약: 이 환경 bwrap 불가로 codex의 미러 파일접근 불가 — 인라인 리뷰로 독립 신호 확보(측정로그 기록).

## 배포·검증 (2026-10-01)

- 이슈 #30 생성 → 브랜치 feat/tree-denylist-30 커밋 c84c657 → push → PR #31 → merge(main 3944f1e). 배포 Actions run 36787679048 success(8s=202 접수).
- **라이브 검증(www.junproject.xyz)**: 홈 사이드바 최상위에 docs·templates **없음**(cs·history·issue·lab·languages·opensource·portfolio·practice·project·reference·workflow·독후감·세미나만) ✓ · `/wiki/docs/logging.md`→404 ✓ · `/wiki/cs`→200 ✓ → **배포 반영·트리/doc 필터 라이브 동작 확인**.
- 검색 색인 잔존 확인: `suggest?q=measurement` → `docs/measurement-log.md` 아직 반환 → **full 재색인 필요**(예상대로).

## 남은 검증 (배포 후 — 사용자 시크릿 필요)

- **full 재색인**: `POST /api/sync {"full":true}` + X-Sync-Secret → prevSha=null 경로로 allMarkdown(필터)+deleteStale(orphan 제거). 시크릿은 credential이라 메인이 grep 안 함(§6) → 사용자 실행 또는 시크릿 제공 대기.
- 재색인 후 검증: `suggest?q=measurement`에 docs 경로 0 · 검색 결과에 docs/templates 0.

## 환경 메모

- backend 빌드: JDK 21 필요(toolchain=21). repo의 .gradle·build·.kotlin가 root 소유(도커 빌드 잔재)라 로컬 빌드는 GRADLE_USER_HOME·--project-cache-dir·--init-script(buildDir)·-Pkotlin.project.persistent.dir를 스크래치패드로 리다이렉트해야 함.
