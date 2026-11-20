# requirement-spec — front 반응형·토큰·패널 토글·다크모드·리더 확장

> 2026-10-04. 대상 = study-note-deploy-system-front(실행물). 설계 정본 = 같은 폴더 `design.md`(§9 결정 포함).

## ① 목표·대상
`design.md` §9 확정 순서 6단계를 구현한다.
1. 토큰 정리 + 다크모드 수동 토글(라이트/다크/자동, `data-theme`, 첫 페인트 전 적용) + 죽은 코드(`Sidebar.tsx`·`HomeView.tsx`) 삭제
2. `LayoutShell`(클라) + 트리/챗 토글(데스크톱) + 단축키 `Ctrl+\`·`Ctrl+/` — 챗 소유 단일화(PaneReader는 오른쪽 pane 문서만 Shell에 보고)
3. 태블릿(720~1199) 드로어 · 모바일(<720) 트리 드로어 + 챗 하단 시트
4. 본문·리더 타이포(`--reading-width`) + PaneReader `matchMedia` → CSS 미디어쿼리
5. 나머지 inline → CSS Modules(검색·탭·트리페이지·헤더)
6. 분할 리더를 1/2/3 챕터 탭 본문까지 확장

**진행 방식**: 단계마다 별도 이슈→PR→배포 → **사용자 화면 확인 후 다음 단계**(UI 단계별 확인 규칙).

## ② 경계·불변식
- **동작 불변**: 라우팅·데이터 fetch·검색·자동완성·챗 API·분할 리더 스택 규칙(왼=top교체/오른=push/ESC=pop)은 그대로. 바뀌는 것은 표현·레이아웃·패널 토글뿐(6단계는 리더 적용 범위 확장).
- 기본값: 데스크톱 트리 열림·챗 단일문서 열림/분할 시 닫힘. 태블릿·모바일 둘 다 닫힘 시작. 데스크톱 선택·테마는 `localStorage`(실패 시 기본값으로 정상 렌더).
- 단축키는 입력창(input·textarea·contenteditable) 포커스 중 무시. ESC 우선순위: 열린 드로어 → pane pop.
- 접근성: 토글 `aria-expanded`/`aria-controls`, 드로어 포커스 이동·복귀.
- 새 의존성 없음(CSS Modules = Next 내장).

## ③ 기준소스
`design.md` · `app/globals.css` · `app/layout.tsx` · `features/wiki/ui/{WikiView,PaneReader,DrillSidebar,Tabs,ClientMarkdown}.tsx` · `features/chat/ui/ChatPanel.tsx` · `shared/ui/{Header,SearchBar}.tsx` · `app/wiki/[...slug]/page.tsx`.

## ④ 금지영역
backend·llm·ci-cd·study-note 변경 금지. API 계약·라우트 경로 변경 금지. 단계 범위 밖 파일 선행 수정 금지(필요 시 멈추고 보고).

## ⑤ 검증 방법
- 단계마다: `tsc`(내 파일)·`vitest`·`next build` 컴파일 + 배포 후 라이브 SSR 확인 + **사용자 화면 확인**.
- 순수 로직은 단위 테스트: 패널 기본값/저장 복원, 단축키 판정(입력 포커스 무시), 테마 3상태 전이.
- 반증: localStorage 차단 시 정상 렌더? 다크 첫 페인트 깜빡임 없나? 분할+챗 토글 상호작용? 드로어 열린 채 ESC → 드로어만 닫힘?
- 리뷰: 단계당 stakes 중간 → 듀얼 1패스(codex 가능 시) / codex 불가 시 Opus 적대적 리뷰(사유 log 기록).

## ⑥ stakes: 중간
전역 레이아웃·표현 변경(공개 UI), 가역(코드). 데이터·보안 경계 무관.

## 자율성
auto 제안 — 단, 단계 경계마다 사용자 화면 확인 대기.

## load-bearing 가정
1. inline → CSS Module 이전 시 Next SSR에서 미디어쿼리가 정상 적용(서버 컴포넌트에서도 `*.module.css` import 가능) — 1단계에서 실증.
2. 챗 소유를 `LayoutShell`로 옮겨도 PaneReader의 "오른쪽 pane 문서 = 챗 문서" 규칙을 콜백/컨텍스트로 유지 가능 — 2단계 착수 직후 실증.
