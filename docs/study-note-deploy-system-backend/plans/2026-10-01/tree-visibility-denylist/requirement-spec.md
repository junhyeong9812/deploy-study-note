# requirement-spec — 작업A: 위키 트리/색인 denylist (docs·templates 완전 제외)

> 작업 폴더 생성: 2026-10-01. 대상 = **study-note-deploy-system-backend**(Kotlin/Spring, 실행물).
> 배경: study-note를 CS 공부 사이트로 정리 — 비-공부 기계류(docs·templates)를 위키에서 완전히 뺀다.
> 후속 별개(작업B): workflow/ → project/study-note-deploy-system/ 이동(문서 이동, 이 작업과 분리).

## ① 목표·대상
study-note 최상위 `docs`·`templates`를 위키의 **트리 + 검색색인 + 챗봇 + 단일문서(/doc)** 전부에서 완전 제외한다(denylist). 루트 `index.md`·`README.md`는 랜딩으로 유지, 나머지 최상위(cs·languages·issue·lab·opensource·portfolio·practice·project·reference·history·workflow·독후감·세미나)는 노출.

## ② 경계·불변식
- **denylist = {`docs`, `templates`}** — 최상위 세그먼트 기준. **단일 상수 1곳**(`content/domain/PathGuard`에 `HIDDEN_TOP_LEVEL` + `isHidden(path)`).
- **4소비자 전부 차단**(실증됨):
  - 목록 경유(트리·전체/증분 색인·/docs) → `GitRepository.allMarkdown()`·`changedMarkdown()`에서 `filter { !PathGuard.isHidden(it) }`.
  - 직접 경로(챗봇 /chat·/history·/escalate, 콘텐츠 /doc) → 핸들러에서 `isHidden` 시 거부(404/invalid).
- 루트 직속 파일(`index.md`·`README.md`)은 최상위 세그먼트가 폴더가 아니므로 denylist 비대상 — 유지.
- **재색인 필요**: 이미 색인된 docs/templates 청크는 배포 후 **full 재색인의 orphan 정리**로 제거(SyncService full 경로가 이번 SHA 아닌 문서 삭제 — 기존 로직 재사용).
- front 변경 불필요(트리 응답이 이미 걸러져 옴).

## ③ 기준소스
- 실코드: `shared/infra/GitRepository.kt`(allMarkdown L50·changedMarkdown L38·diff), `content/usecase/TreeService.kt`(build(allMarkdown)), `content/api/ContentController.kt`(/docs·/doc), `chat/api/ChatController.kt`(doc_path 검증), `content/domain/PathGuard.kt`(공유 술어).
- study-note 최상위 폴더 실목록.

## ④ 금지영역
- workflow/ 이동은 **작업B**(이 작업 아님).
- front·llm·ci-cd repo 변경 금지.
- denylist 외 폴더 노출 규칙 변경 금지. PathGuard의 기존 트래버설·.md 검증 로직 변경 금지(추가만).

## ⑤ 검증 방법
- **스모크(배포 전 로컬 테스트 우선)**: PathGuard.isHidden 단위 테스트(`docs/x.md`·`templates/x.md`=true, `cs/x.md`·`index.md`=false). allMarkdown/changedMarkdown 필터 반영 확인.
- **배포 후 실플로우**: `/api/tree`에 docs·templates 노드 없음 · `/api/search?q=<docs 전용어>` 결과에 docs 경로 없음 · `/api/doc?path=docs/logging.md` 거부 · chat `doc_path=docs/...` 거부.
- **재색인 검증**: full 재색인 후 ES에 docs/templates path 청크 0(count/query). silent failure 반증 — 부분 제외로 일부만 남지 않나.
- **반증 질문**: 이미 색인된 docs 청크가 재색인 전까지 검색에 남나(→ full 재색인 필요 명시)? front가 숨은 경로로 /doc 직접 요청하면 거부되나? 루트 index.md가 실수로 걸러지나(세그먼트 판정)?
- **리뷰**: 실행물·stakes 중간 → 듀얼 1패스(Opus 워커 ∥ codex → 종합 → 재점검 1회). 보안(직접접근 가드) 렌즈 포함.
- **커밋**: backend repo 브랜치. push는 사용자 확인.

## ⑥ stakes: 중간
근거: 검색 corpus·public 트리 계약 변경 + 직접접근 가드(경미 보안) + 재색인 필요. 전부 가역(코드·git). 데이터 삭제 아님(색인 재생성).

## 자율성
auto 제안.

## load-bearing 가정 (실증 완료)
1. 트리·전체/증분색인·/docs는 모두 allMarkdown/changedMarkdown 경유 → 목록 필터 1곳으로 덮임 (grep 실증 ✓).
2. 챗봇·/doc은 클라이언트 doc_path 직접 로드라 목록 필터로 안 막힘 → PathGuard.isHidden을 핸들러 가드에도 적용해야 완전 제외 (실증 ✓).
