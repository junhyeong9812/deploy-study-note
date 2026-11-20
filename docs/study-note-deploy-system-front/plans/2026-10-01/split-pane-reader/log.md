# log — 컨텐츠 분할 리더 (스택 2-pane)

## 진행 기록

- 2026-10-01 | 실증 | Markdown은 `<a href>`만 렌더(인터셉트 필요)·클라 doc fetch 라우트 없음(BFF 신설)·page.tsx else 분기가 doc경로 렌더(링크 라우팅 재사용)
- 2026-10-01 | 명세 합의(auto, 단일문서뷰·분할시 챗 토글숨김·클라상태만) + set-state
- 2026-10-01 | 구현 | paneStack.ts(순수)+테스트 · /api/doc BFF · ClientMarkdown(링크 인터셉트) · PaneReader(스택·ESC·챗토글·fetch) · page.tsx 단일문서 분기 배선(wide·chatDocPath=null)
- 2026-10-01 | 검증 | tsc 내파일 클린(기존 tree.test.ts prev 2건 무관) · vitest 12 pass(paneStack 6) · next build ✓ Compiled
- 2026-10-01 | 리뷰 | codex 사용량 한도 초과(11:57까지)로 산출 실패 → **사용자 승인 Opus 단독 적대적 리뷰(user override)** · Opus 미러 전수

## 리뷰 ledger (Opus 적대적 1패스 — codex user-override 생략)

- **F1 채택·fixed** (강함, UX): WikiView `maxWidth:860`가 PaneReader 전폭 가둠 → `wide` prop 추가(리더는 캡·패딩 제거) WikiView.tsx·page.tsx.
- **모바일 폴백 채택·fixed**: spec 좁은폭 단일 pane 미구현 → PaneReader matchMedia(max-width:720)로 narrow 시 top pane 하나만.
- **F4 채택·fixed**: fetch가 setDocs 업데이터 내부(StrictMode 2중) → `requested` ref 가드 + 업데이터 밖 fetch.
- **F5 채택·fixed**: 에러 영구 캐시(재시도 불가) → 에러 시 requested 해제 + "다시 시도" 링크.
- **F2 채택·fixed**: 폴더/subject 링크 .md 404 → 에러 pane에 "페이지에서 열기"(정상 네비) 폴백.
- **F7 채택·fixed**: 챗 토글 버튼 하단 겹침 → top-right 이동.
- F3 유지(기각): split effect로 챗 토글 리셋 — spec② 기본흐름 충족, 수동선호 미보존은 경미.
- F6 유지(기각): ClientMarkdown vs Markdown 중복 — 클라 onClick 때문에 분리 정당(Ponytail 수용).
- **post-fix 재검증**: tsc 클린·vitest 12·next build Compiled(수정 반영). codex 부재로 독립 재점검 불가 → user override 하 self+build/test. UI(wide·모바일)는 배포 후 라이브 확인.

## 남은 것

- 커밋 → 이슈 → PR → 배포 → 라이브 확인(링크 클릭 분할·ESC·챗토글·전폭·모바일 단일·외부링크).

## 배포·검증 (2026-10-01)
- 이슈 #29 → 브랜치 feat/split-reader-29 → PR #30 머지(main 270a1a1) → 배포.
- 라이브: `/wiki/history/java/java-11` 200 + 리더 토글(💬) SSR 렌더 확인(재빌드 ~1분). 분할 클릭·ESC·모바일 단일은 클라 JS → 사용자 화면 최종 확인.
- **완료**(배포·SSR 검증). 인터랙션 시각 확인은 사용자.
