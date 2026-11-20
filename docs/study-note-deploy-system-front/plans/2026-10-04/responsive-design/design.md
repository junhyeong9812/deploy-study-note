# 설계 — front 반응형·디자인 토큰·패널 열고닫기

> 2026-10-04 · L0 설계 문서(코드 변경 없음). 구현은 이 문서 합의 후 별도 명세(requirement-spec)로 단계 진행.
> 대상 repo: study-note-deploy-system-front (Next 15 · React 19).

## 1. 목표

1. **반응형** — 데스크톱·태블릿·모바일 3단에서 읽기 화면이 깨지지 않게.
2. **디자인 토큰** — 색·여백·글자·radius·레이아웃 폭을 CSS 변수 한 곳에서 관리.
3. **트리창·채팅창 열고 닫기** — 두 패널을 사용자가 접고 펼칠 수 있게(상태 기억).
4. (확인 필요) **분할 리더를 1/2/3 챕터 탭 페이지까지 확장** — 공부 콘텐츠 대부분이 챕터 페이지라 체감 효과가 큼.

## 2. 현재 상태 진단

| 항목 | 현재 | 문제 |
|---|---|---|
| 스타일 방식 | inline `style={{}}` **99곳 / 12파일** | inline엔 미디어쿼리 불가 → 반응형 근본 불가 |
| 레이아웃 | `WikiView` grid `260px · 1fr · 340px` 고정 | 폭이 줄면 본문이 찌그러짐 |
| 모바일 판정 | PaneReader만 JS `matchMedia(720px)` | 레이아웃 전체는 모바일 대응 없음 |
| 토큰 | 색 7개(`--bg --fg --muted --line --accent --accent-bg --code-bg`) + OS 다크모드 | 여백·글자·폭·z-index 토큰 없음, 매직넘버(53px, 260, 340, 860) 산재 |
| 채팅 소유 | **이원화** — 일반 페이지는 `WikiView` grid 3열, 단일 문서는 `PaneReader` 내부 | 토글을 넣으려면 소유자가 하나여야 함 |
| 죽은 코드 | `features/wiki/ui/Sidebar.tsx`, `features/home/ui/HomeView.tsx` — import 0 | 이전 범위에서 제외·삭제 후보 |

## 3. 결정 — CSS Modules + 디자인 토큰

| 방식 | 판단 |
|---|---|
| **CSS Modules + 토큰 (채택)** | Next 내장 — **새 의존성 0**. 컴포넌트별 `*.module.css`로 미디어쿼리 가능. inline → 클래스 이전만 하면 됨 |
| Tailwind | 빠르나 의존성 추가 + 99곳 전면 재작성. 클래스 문자열이 길어져 읽기 코드 가독성 저하 |
| 컴포넌트 라이브러리(shadcn·radix) | 읽기 위주 사이트엔 과함(Ponytail ①·⑤) |

## 4. 토큰 설계 (`globals.css`)

```css
:root {
  /* 색 — 기존 7개 유지 */
  --bg; --fg; --muted; --line; --accent; --accent-bg; --code-bg;
  /* 여백 스케일 */
  --space-1: 0.25rem; --space-2: 0.5rem; --space-3: 0.75rem;
  --space-4: 1rem;    --space-6: 1.5rem; --space-8: 2rem;
  /* 글자 */
  --text-xs: 0.78rem; --text-sm: 0.875rem; --text-md: 1rem; --text-lg: 1.25rem; --text-xl: 1.6rem;
  --reading-width: 860px;         /* [화면 확인 후 결정] 설계안 72ch는 한글 본문에서 ≈630px로 급격히 좁아져 4단계에서 현행 860px 유지 */
  /* 모양 */
  --radius-sm: 6px; --radius-md: 8px; --radius-pill: 20px;
  /* 레이아웃 */
  --header-h: 53px;               /* calc(100vh - 53px) 매직넘버 대체 */
  --tree-w: 260px; --chat-w: 340px;
  /* 레이어 */
  --z-overlay: 40; --z-drawer: 50;
}
```
브레이크포인트는 CSS 변수로 미디어쿼리에 못 쓰므로 **상수로 문서화**: `mobile < 720px ≤ tablet < 1200px ≤ desktop`.

## 5. 레이아웃 지도 (브레이크포인트별)

```
[데스크톱 ≥1200]
┌──────────── Header (검색 · [≡트리] [💬챗] 토글) ────────────┐
│ 트리 260 │        본문(단일)  또는  pane A │ pane B │ 챗 340 │
│ (접기 가능)│        reading-width 캡       │        │(접기가능)│
└──────────┴────────────────────────────────┴────────┴────────┘
  - 트리 접힘 → 본문이 그 폭을 가져감
  - 분할 시 챗 기본 닫힘(기존 규칙 유지), 토글로 열기

[태블릿 720~1199]
┌──────────── Header [≡] [💬] ────────────┐
│  본문 / pane A │ pane B                  │   트리: 좌측 드로어(오버레이)
│                                          │   챗:  우측 드로어(오버레이)
└──────────────────────────────────────────┘   기본 둘 다 닫힘

[모바일 <720]
┌──── Header [≡] [💬] ────┐
│  pane 1개(스택 top)       │   트리: 전체폭 드로어
│                          │   챗:  하단 시트(높이 70%)
└──────────────────────────┘   ESC/✕로 pane pop (기존 유지)
```

## 6. 패널 열고닫기 상태 모델

- **소유자 단일화**: 새 클라이언트 컴포넌트 `LayoutShell`이 `treeOpen`·`chatOpen`·`chatDocPath`를 소유. `WikiView`는 Shell에 슬롯(sidebar·main·chat)만 넘긴다. `PaneReader`는 챗을 직접 그리지 않고 **현재 오른쪽 pane 문서 경로를 Shell에 올려보낸다**(콜백/컨텍스트) → 챗 이원화 해소.
- **기본값**: 데스크톱 트리=열림·챗=단일문서에서 열림/분할 시 닫힘 · 태블릿/모바일 = 둘 다 닫힘.
- **기억**: 데스크톱의 열림/닫힘 선택은 `localStorage`(뷰어별 편의, 실패 시 기본값). 태블릿/모바일 드로어는 기억 안 함(매번 닫힘 시작).
- **조작**: Header의 `[≡]`(트리)·`[💬]`(챗) 토글 버튼. 단축키 후보 `Ctrl+\`(트리)·`Ctrl+/`(챗) — 확인 필요. 드로어는 바깥 클릭·ESC로 닫힘(ESC 우선순위: 열린 드로어 → pane pop).
- **접근성**: 토글 버튼 `aria-expanded`·`aria-controls`, 드로어 열릴 때 포커스 이동·닫을 때 복귀.

## 7. 이전 대상 (inline → CSS Module)

| 파일 | inline 수 | 비고 |
|---|---|---|
| WikiView.tsx | 19 | 레이아웃 핵심 → `LayoutShell` 도입과 함께 |
| DrillSidebar.tsx | 12 | 트리 |
| SearchResultsView.tsx | 11 | |
| ChatPanel.tsx | 11 | 챗(드로어/시트 대응) |
| SearchBar.tsx | 10 | Header |
| PaneReader.tsx | 10 | `matchMedia` 제거 → CSS 미디어쿼리로 |
| CollapsibleTree.tsx | 8 | `/tree` 페이지 전용 |
| Tabs·Header·mark | 6 | |
| Sidebar.tsx · HomeView.tsx | — | **미사용 → 삭제**(Ponytail) |

## 8. 적용 순서 (UI 단계별 확인 규칙)

한 단계 배포 → **화면 확인** → 다음 단계.
1. 토큰 정리(`globals.css`) + 죽은 코드 삭제 — 화면 변화 거의 없음
2. `LayoutShell` + 트리/챗 토글(데스크톱) — 챗 소유 단일화
3. 태블릿·모바일 드로어/시트
4. 본문·리더 타이포(reading-width) + PaneReader 미디어쿼리 이전
5. 나머지 컴포넌트(검색·탭·트리페이지) inline 이전
6. (합의 시) 분할 리더 챕터 탭 확장

## 9. 결정 (2026-10-04 사용자 확정)

1. **분할 리더 챕터 탭 확장 — 포함**(마지막 단계). 탭 본문도 링크 인터셉트 렌더러로.
2. **단축키 채택** — `Ctrl+\` 트리 토글 · `Ctrl+/` 챗 토글(입력창 포커스 중엔 무시).
3. **다크모드 수동 토글 추가** — 라이트/다크/자동(OS) 3상태. `:root[data-theme="dark"]`로 토큰 재정의, 자동이면 `prefers-color-scheme` 따름. 선택은 `localStorage`, **첫 페인트 전 적용**(layout `<head>` 인라인 스크립트로 깜빡임 방지).
4. **데스크톱 챗 기본 = 열림**(현행 유지). 분할 시 닫힘 규칙 유지. 사용자가 바꾸면 기억.

### 반영된 적용 순서 (확정)
1. 토큰 정리 + 다크모드 토글(`data-theme`) + 죽은 코드 삭제
2. `LayoutShell` + 트리/챗 토글(데스크톱, 단축키 포함) — 챗 소유 단일화
3. 태블릿·모바일 드로어/시트
4. 본문·리더 타이포 + PaneReader `matchMedia` → CSS 미디어쿼리
5. 나머지 컴포넌트 inline 이전(검색·탭·트리페이지)
6. 분할 리더 챕터 탭 확장
