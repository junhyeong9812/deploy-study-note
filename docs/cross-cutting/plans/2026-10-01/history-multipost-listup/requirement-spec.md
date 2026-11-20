# requirement-spec — history 다중-post 리스트업 (A: 프론트 렌더 + B: 폴더 규약)

> 작업 폴더: 2026-10-01. 대상 = **study-note-deploy-system-front**(A, 실행물) + **study-note**(B, 콘텐츠). 커밋 분리(§6).
> 근본원인: `page.tsx:39-41`이 `docsByKind = Map<doc_kind,…>` — 다중 post가 같은 doc_kind로 덮어써져 1개만 렌더. 파일명 문제 아님.

## ① 목표·대상
- **A (프론트)**: `SubjectView`가 **다중 non-chapter post 리프를 본문 목록**으로 렌더(현재 1개만 나옴). 모든 다중-post 주제(history·workflow·reference/writing 등)가 리스트업된다.
- **B (study-note)**: `history/<lang>/<name>.md` → `history/<lang>/<name>/post.md` (폴더=주제 약속 준수). `history/<lang>`가 드릴다운 폴더가 되어 좌측 사이드바에 각 항목 리스트업. 대상 83개(database·js·network·python·rust·web 각 7, java 28, spring 13).

## ② 경계·불변식
- **A**: chapter(1/2/3) 리프는 기존 3탭 유지(무변경). **단일 post 리프는 기존 인라인 렌더 유지**. **다중(≥2) non-chapter post만** 목록 렌더. 링크는 기존 doc-path 라우팅(`page.tsx` else 분기 `fetchDoc(path+".md")`) 사용 — 새 라우팅 안 만듦. `docsByKind`가 doc_kind로 덮는 문제도 함께 교정(다중 post는 path 기준으로 다룸).
- **B**: `README.md`는 폴더 본문으로 **잔존**(이동 안 함). 각 `<name>.md`는 `git mv`로 `<name>/post.md`(이력 보존). `NN-`/버전 접두 유지(정렬). **내용 편집 없음 — 이동만**. post.md는 기존 단일-post 규약(portfolio 리프와 동일).
- denylist(docs·templates)와 무관. workflow·reference 폴더화는 **이 작업 아님**(A로 렌더는 됨 → NEXT).

## ③ 기준소스
- 실코드: `features/wiki/ui/WikiView.tsx`(SubjectView·FolderView), `app/wiki/[...slug]/page.tsx`, `features/wiki/lib/tree.ts`(CHAPTER_KINDS·otherDocs·KIND_LABEL).
- study-note/history 실파일.

## ④ 금지영역
- backend·llm·ci-cd 변경 금지. history 문서 내용 편집 금지(이동만). workflow·reference 재구성 금지(NEXT).
- A: chapter·단일 post 렌더 경로 변경 금지(다중 post 분기만 추가).

## ⑤ 검증 방법
- **A**: 프론트 빌드 + 기존 vitest. 로컬/배포후 렌더 — 다중post 리프=목록·클릭시 문서 렌더 / 단일 post=인라인 유지 / chapter=3탭 유지. 리뷰 = front 코드 medium → 듀얼 1패스.
- **B**: 이동 후 구조 확인(각 `<name>/post.md` 존재·`README.md` 잔존·flat `.md` 0). `git mv` 이력 보존 확인. 리뷰 = 파일이동 낮음 → 셀프+구조검증.
- **배포 후**: history/java 드릴다운에 자식(java-5…) 리스트업, 클릭 렌더. **full 재색인 필요**(구 history 평면경로 orphan 제거 + 새 post.md 색인).
- **반증**: 단일 post 리프가 실수로 목록이 되나? chapter 탭이 깨지나? git mv가 이력 끊나? README가 이동되나?

## ⑥ stakes: 중간
A=공개 렌더 계약 변경, B=URL 변경·재색인 필요. 전부 가역(코드·git mv).

## 자율성: auto

## load-bearing 가정 (실증 완료)
1. 노드 아닌 doc 경로(`/wiki/history/java/java-11`)는 `page.tsx` else 분기가 `<path>.md` fetch로 렌더 → A의 목록 링크가 동작 (page.tsx:48-55 확인).
2. B 후 `history/<lang>`는 children 보유 → non-subject → FolderView/사이드바가 자식 나열(기존 동작).
