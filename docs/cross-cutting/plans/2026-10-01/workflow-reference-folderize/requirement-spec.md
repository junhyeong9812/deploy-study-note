# requirement-spec — (b) workflow·reference/writing 폴더규약화

> 2026-10-01. 대상 = **study-note**(콘텐츠). #3-(b). history-B와 동형(폴더=주제 약속).
> 링크 분석: workflow 내부 링크는 README의 7개(`](sync.md)` 등)뿐 — resolveHref가 `.md`를 벗겨 `/wiki/workflow/sync`로 정규화하고, 재구성 후 `workflow/sync/`(폴더 노드)가 **같은 URL**이라 링크 불변. reference/writing은 내부 링크 0. index.md의 역참조는 README 경로(불변) 대상.

## ① 목표
다중-post 리프 `workflow/`·`reference/writing/`의 각 문서를 `<name>/post.md`로 분리 — 폴더=주제 약속 준수, 드릴다운 폴더화.

## ② 경계·불변식
- 이동 대상: `workflow/*.md`(README 제외 7개: sync·content·search·deploy·chat-design·streaming-mvc-vs-webflux·logging) + `reference/writing/evidence-*.md`(10개). → 각 `<name>/post.md`(`git mv`, 이력 보존).
- `README.md`는 폴더 본문으로 **잔존**. 접두·내용 **무편집**(이동만). **링크 재작성 없음**(resolveHref가 .md 흡수 — URL 안정, 분석 완료).
- reference/ 최상위 직속 파일(organize-guide 등)·learning·tools는 **대상 아님**(reference는 children 보유 폴더라 이미 FolderView 나열).

## ③ 기준소스
study-note `workflow/`·`reference/writing/` 실파일, `features/wiki/lib/links.ts`(resolveHref — .md 정규화 근거).

## ④ 금지영역
history·cs 등 다른 트리 변경 금지. 문서 내용 편집 금지(이동만). front/backend 변경 금지.

## ⑤ 검증
이동 후 구조(각 `<name>/post.md`·README 잔존·flat 0). workflow README의 7개 링크가 재구성 후에도 `/wiki/workflow/<name>` 폴더로 해소되는지 확인(resolveHref 근거 + 배포 후 라이브). git mv 이력. 리뷰 = 파일이동 낮음 → 셀프+구조검증.

## ⑥ stakes: 낮음~중간 (콘텐츠 이동·URL 안정·가역). 재색인 필요(새 경로+구 orphan).
## 자율성: auto
## 가정: resolveHref(.md 벗김)로 workflow README 링크 URL 불변 — 배포 후 라이브로 실증.
