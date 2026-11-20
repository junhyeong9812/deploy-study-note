# requirement-spec — (a) subject 페이지 fetch 최적화

> 2026-10-01. 대상 = study-note-deploy-system-front. #3-(a).
> 배경: subject 분기가 `node.docs` 전부를 fetch — 다중-post 목록 뷰는 내용이 불필요한데 N개를 다 가져옴(Opus F1 이연분).

## ① 목표
subject 페이지 렌더에 **필요한 문서만** fetch한다: 다중 목록=README만 · chapter=챕터+README · 단일 post=그 문서만.

## ② 경계·불변식
- 렌더 결과 **불변**(목록·chapter 탭·단일 리더 모두 기존과 동일). fetch 수만 감소.
- 겸사 교정: 단일 post 리프에서 `single`이 doc_kind find로 README를 집던 가능성 → **contentDocs[0](실제 post)** 선택.
- chatDocPath 산출 유지(summary→readme→첫문서).
- backend·study-note 무변경.

## ③ 기준소스
`app/wiki/[...slug]/page.tsx` subject 분기, `features/wiki/ui/WikiView.tsx`(SubjectView 소비), `features/wiki/lib/tree.ts`(CHAPTER_KINDS).

## ④ 금지영역
폴더/else-doc 분기 변경 금지(subject 분기만). 렌더 컴포넌트(SubjectView) 변경 금지.

## ⑤ 검증
tsc·vitest·next build. 라이브: 다중목록(history/java)·chapter 리프·단일 post·folder README 전부 기존대로 렌더. 리뷰 Opus(코덱스 한도).

## ⑥ stakes: 중간 (공개 렌더 fetch 로직, 가역)
## 자율성: auto
## 가정: SubjectView 다중목록 분기는 node.docs 참조 + readme intro만 필요(이미 구현 확인) → README만 fetch로 충분.
