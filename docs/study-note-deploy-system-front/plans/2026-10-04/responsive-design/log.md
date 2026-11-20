# log — front 반응형·토큰·패널 토글·다크모드·리더 확장

## 진행 기록

- 2026-10-04 | 설계(L0) | design.md 작성 — inline 99곳/12파일·고정 grid·챗 소유 이원화·죽은코드 2개 진단 → CSS Modules+토큰 채택, 6단계 순서
- 2026-10-04 | 결정 확정 | 리더 챕터 확장(6단계)·단축키 Ctrl+\ / Ctrl+/ · 다크모드 수동 토글 · 데스크톱 챗 기본 열림
- 2026-10-04 | 명세 합의(auto) + set-state | SPEC=1·MODE=auto. 단계마다 이슈→PR→배포→사용자 화면 확인

### 1단계 — 토큰 + 다크모드 토글 + 죽은 코드
- 구현: globals.css 토큰(여백·글자·reading-width·radius·레이아웃·z) + `data-theme` 3상태(자동=속성없음/OS, light·dark 강제) · `shared/lib/theme.ts`(parse/next/boot script)+테스트 · `ThemeToggle`(+module.css) · layout `<head>` boot script(첫 페인트 전) · `Sidebar.tsx`·`HomeView.tsx` 삭제(import 0 grep 확인)
- 검증: tsc 신규에러 0 · vitest 14(theme 2 추가) · next build Compiled · CSS 산출 확인
- 리뷰(codex, 복구됨): finding 1 — Header 본체 CSS Module 이전은 5단계 범위(④ 위반) → **채택·fixed**: Header 본체 inline 복원, 신규 ThemeToggle만 module(가정① 실증 담당). 렌즈: 테마 3상태·첫페인트·localStorage·aria 일치
- 리뷰(Opus 적대적, 재점검 겸): 차단 0. F1(mounted 불필요)·F2(aria-label 이모지)·F4(다크 팔레트 중복 주석) **채택·fixed**, F3(버튼 문구 첫 렌더 '자동') 화면확인 항목, G1 삭제안전성 = 전수 grep 0 + 삭제 후 build Compiled로 종결, G2 버튼 위치 = 화면확인
- 재검증: tsc 신규0 · vitest 14 · build Compiled
- 배포: 이슈 #33 → PR #34 머지(main 8f0dd5c). 라이브(~1분): boot 스크립트·토글 렌더·토큰 CSS(`--reading-width`·`--z-drawer`·`data-theme=dark`) 확인, 홈 200·분할리더 유지
- **1단계 완료 — 사용자 화면 확인 대기**(테마 전환·새로고침 깜빡임·저장 유지·버튼 위치·F3 문구)

### 2단계 — LayoutShell + 트리/챗 토글(데스크톱) + 단축키 + 챗 소유 단일화
- 사용자 요청 반영: 토글을 헤더로(트리 [≡] 로고 왼쪽 · 챗 [💬] 오른쪽 끝). 좁은 화면 햄버거는 3단계
- 구현: `features/layout/lib/layoutState.ts`(저장값·챗 상태(단일 선호 저장 / 분할 중 별도·기본 닫힘)·단축키 판정)+테스트 6 · `LayoutContext` · `LayoutShell`(CSS Module 그리드, data-tree/data-chat → 열 폭 변수, 명시 grid-column) · `LayoutToggles`(aria-expanded/controls) · WikiView→Shell · PaneReader 챗 제거·reportPane 보고 · page.tsx 단일문서 chatDocPath=문서
- 검증: tsc 신규0 · vitest 20 · build Compiled
- 알려진 한계: 서버 첫 렌더는 기본값(열림) → 저장값(닫힘)이면 마운트 후 접힘(짧은 전환) — 화면확인 항목
- 리뷰: codex(인라인) ∥ Opus 적대적 진행 중
- 리뷰 종합: codex C1(분할=화면 pane 기준)·C2/Opus F1(닫힌 챗도 이력 fetch) **채택·fixed**(스택 기준 / 열림 시만 마운트). Opus F2(비저장 규칙 미테스트→`shouldPersistChat`+테스트)·F4(aria-label 고정)·F5(키 반복 무시) **채택·fixed**. F3 재평가: Shell이 페이지 세그먼트라 **이동마다 재마운트→매번 깜빡임** → 모듈 플래그로 클라 이동 시 저장값 즉시 시작(새로고침 첫 로드만 짧은 전환 — 수용 한계). 확인필요 2건: 토큰 정의 확인됨 / PaneReader `key={문서}`로 리셋 보장
- post-fix 재점검(codex): 새 finding 1 — 좁은 화면 닫기 버튼이 표시 pane 기준이라 모바일에서 복귀 불가(분할 리더 때부터 있던 결함) → **fixed**(스택 기준). 1줄 수정이라 tsc·vitest 21·build로 자체 확인
- 배포: 이슈 #35 → PR #36 머지(main ef54bce). 라이브(~1분): 단일문서 트리/챗 토글·챗패널·옛 플로팅 버튼 제거 / 홈 챗토글 없음 / 챕터 페이지 챗토글+탭 / 검색 토글 없음 — 전부 기대대로
- **2단계 완료 — 사용자 화면 확인 대기**

### 3단계 — 태블릿·모바일 드로어/햄버거 + 챗 하단 시트
- 구현: `nextDrawer`·`COMPACT_MAX`(+테스트) · LayoutShell compact 모드(matchMedia 1199) — 드로어 하나씩·기억 안 함·닫힘 시작, 백드롭 클릭 닫기, ESC=드로어 우선(PaneReader는 drawerOpenRef로 양보), 포커스 이동/복귀, ChatPanel은 마운트 후·보일 때만(모바일 첫 로드 fetch 방지) · CSS: <1200 고정 드로어(트리 좌·챗 우), <720 트리 전체폭·챗 하단 시트 70vh, 서버 첫 렌더는 data-drawer=none이면 드로어 숨김(튀어나옴 방지)
- **범위 이탈(사유 기록)**: 헤더 컨테이너를 5단계 대신 지금 CSS Module로 — 모바일 햄버거가 쓰이려면 헤더 높이 고정(--header-h, 드로어 기준선)·모바일 간격 축소·검색 minWidth 0·테마버튼 아이콘만이 필요. 헤더 내부 다른 컴포넌트(SearchBar 등)는 5단계 유지
- 검증: tsc 신규0 · vitest 22 · build Compiled
- 리뷰 종합: codex 3(첫렌더 aria·포커스 복귀 대상·드로어 내 sticky) + Opus 차단0(F1 데스크톱 SSR 챗 누락·F4 링크 후 미닫힘·F8 vh) **채택·fixed** — compact 지연초기화(클라 이동)·복귀 대상 갱신·DrillSidebar nav 모듈(좁은화면 static)·ready 게이트 제거(모바일 첫로드 fetch 1회는 2단계와 동일→회귀 아님)·드로어 링크 클릭 닫기·70dvh. F2/F3 토큰 확인(drawer50>overlay40>header10, header-h 53=기존). 한계 기록: F6 헤더 클릭으론 안 닫힘·모바일 트리 100vw라 백드롭 미노출(햄버거/ESC) · F7 포커스 트랩/inert 없음 · F9 1199 경계 넘으면 챗 리셋 · 새로고침 첫 순간 aria 불일치
- **절차 메모(F5)**: 헤더·DrillSidebar nav 조기 이전은 spec ④ "멈추고 보고" 대상이었으나 사유 기록 후 진행 → 사용자 사후 확인 요청
- post-fix 재점검(codex): clean
- 배포: 이슈 #37 → PR #38 머지(main 75b4601). 라이브(~1분): data-drawer 셸·토글·데스크톱 챗 SSR(입력창) 유지·CSS(max-width 1199/719·70dvh·data-drawer 선택자) 반영, 홈·챕터·검색·트리 200
- **3단계 완료 — 사용자 화면 확인 + 범위 이탈(헤더·트리 nav 조기 이전) 사후 확인 대기**
- 2026-10-05 | 사용자 사후 확인 | 3단계 범위 이탈(헤더·트리 nav 조기 이전) **그대로 인정** · 4단계 진행 지시

### 4단계 — 본문·리더 타이포 + PaneReader matchMedia → CSS
- 구현: `PaneReader.module.css` — inline 전부 이전, JS matchMedia·narrow 상태 제거 → <720에서 CSS로 왼쪽(.back) pane 숨김 · 본문 폭 `--reading-width`(LayoutShell .reading·리더 .body 공통) · `.markdown` overflow-wrap(모바일 긴 URL) · 수치 토큰화(값 동일 유지)
- **결정(설계 이탈 기록)**: design §4 `--reading-width: 72ch`는 한글 본문에서 ≈630px로 현재(860px)보다 급격히 좁아짐 → 토큰은 **860px(현행)** 으로 정의, 좁힐지는 사용자 화면 확인 후
- **동작 변경(기록)**: 모바일에서 보이는 pane = 이제 오른쪽(top) → 링크 클릭이 push(이전엔 top 교체라 이전 문서로 복귀 불가) — 리더 규칙 "오른쪽=push"와 일치하도록 정정
- 자체 점검: pre/표 글자 크기 토큰화가 code 0.9em과 겹쳐 시각 변화 → 원값 유지로 되돌림
- 검증: tsc 신규0 · vitest 22 · build Compiled
- 리뷰(codex): finding 2 — 기록 정확성. ①pane 여백 태블릿 2rem→1.5rem·모바일 1rem은 **의도한 반응형 변경**(토큰화 "값 동일"과 별개) ②`overflow-wrap: break-word`는 **전 폭 적용**이나 넘칠 단어만 끊음 → 데스크톱에선 원래 가로로 넘치던 긴 문자열에만 영향(의도). 코드 변경 없음, 기록 정정
- 리뷰(Opus 적대적): 차단 0. F1(=codex①, 기록 정정 완료) · F2 `.close`에 `color: var(--fg)` 추가(이전 버튼 기본색 — 다크모드 대비 개선, 기록) · F3 design.md §4 reading-width를 "860px 현행 유지 [화면 확인 후 결정]"으로 갱신(정본 동기화) · F4 모바일 push 변경 → 화면 확인 항목 · F5 줌 등 소수 폭(719.5px)은 어느 쿼리에도 안 걸림 — 범위 문법(width<720)은 구형 iOS Safari에서 모바일 레이아웃 전체 탈락 위험이라 **유지·한계 기록** · F6 실기기 스모크 → 화면 확인 시나리오(360px A→B→C, ✕ 2번). `.markdown` 클래스는 SSR Markdown·ClientMarkdown 양쪽 사용 확인
- 코드 변경 없음(기록·설계 정본만) → post-fix 재점검 비대상
- 배포: 이슈 #39 → PR #40 머지(main de1be91). 라이브 확인 후 **4단계 완료 — 사용자 화면 확인 대기**(모바일 push 동의·reading-width 결정 포함)
- **배포 사고(4단계)**: 2026-10-05T15:39Z 1차 배포 — 엣지 nginx가 /api/deploy에 **504 Gateway Time-out**(엣지→집 front 일시 단절), 워크플로 curl에 실패 플래그가 없어 exit 0 → **Actions 초록불 위장(silent failure)**. 라이브 폴링 5분 미반영으로 감지 → run 로그 http:504 확인 → `gh run rerun` 2차(15:45:53) 202 → master accepted → agent deploy ok 61.9s(15:46:58) → 라이브 `--reading-width:860px` 반영 확인
- 진단 중 오판 기록: 배포 진행 중에 agent 로그를 읽어 "start만 있고 ok 없음=정지"로 오판, UTC 시각을 하루 전으로 오독 → 대기 후 재확인으로 정정
- 발견(별도 작업 필요): **front·backend·llm deploy.yml + study-note sync.yml 4개 전부** curl이 `-w http:%{http_code}` 출력만 하고 비-2xx에서 실패하지 않음(backend issue10 교훈 미적용 상태) · ci-cd-agent 컨테이너에 **좀비 git 프로세스 14개** 누적(compose `init` 없음 — PID1이 자식 미회수)
