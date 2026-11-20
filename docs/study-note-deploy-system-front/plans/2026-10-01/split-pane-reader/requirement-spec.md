# requirement-spec — 컨텐츠 분할 리더 (스택 기반 2-pane)

> 작업 폴더: 2026-10-01. 대상 = **study-note-deploy-system-front**(실행물).
> 배경: 단일 문서 보기에서 링크 클릭 시 페이지 이동 → 한 문서를 보며 참조 문서를 **나란히** 볼 수 없음. 스택 2-pane 리더로 해결.

## ① 목표·대상
단일 문서 보기 화면에서, 문서 내부 링크 클릭 시 **옆 pane에 열어** 두 문서를 나란히 읽는다. 이전 화면은 스택으로 관리하고 닫으면(ESC/버튼) 되돌아간다.

**스택 모델** (표시 = 스택의 마지막 1~2개):
- 시작 stack=[A] → A 단일 표시.
- A(왼쪽)에서 B 클릭 → push → `A|B`.
- A(왼쪽)에서 C 클릭 → **오른쪽 교체**(stack 끝 교체) → `A|C`.
- B(오른쪽)에서 D 클릭 → **push·이동** → stack=[A,B,D] → `B|D`.
- 닫기(ESC 또는 오른쪽 pane 닫기 버튼) → pop → `B|D`→`A|B`→`A`(단일).
규칙: **왼쪽 pane 링크 = 스택 top 교체 / 오른쪽 pane 링크 = push / 닫기 = pop**.

## ② 경계·불변식
- **적용 범위 = 단일 문서 보기에만**(SubjectView 단일 post 분기 + page.tsx else 문서 분기). 목록·폴더·chapter(1/2/3 탭)·다중-post 목록 뷰는 **기존 유지**(거기서 문서 클릭 시 단일 문서 보기로 진입하며 리더 시작).
- **링크 인터셉트**: pane 내부 **내부 문서 링크(/wiki/<path>)만** 인터셉트(push/replace). 외부 링크·앵커(#)는 기본 동작(새 네비/스크롤).
- **클라이언트 상태만**: 스택은 React 상태. 새로고침 = 단일 문서로 리셋(URL 미동기화). 초기 pane(A)는 SSR 콘텐츠 재사용(초기 로드 유지), 이후 pane은 클라이언트 fetch.
- **챗봇**: 분할(2 pane) 활성 시 우측 챗봇 숨김 + **토글 버튼**. 챗봇 재개 시 **오른쪽 pane 문서 기준**.
- **신규 BFF 라우트** `/api/doc`(GET ?path=) — backend `/api/doc` 프록시(봉투 해제, requestId 발행). PathGuard는 backend가 담당(denylist·트래버설). 클라 fetch 전용.
- 모바일(좁은 폭): 2 pane 가로가 안 되면 **오른쪽(top) pane만** 단일 표시(분할 비활성 폴백).
- backend·llm·ci-cd·study-note 변경 금지(순수 front).

## ③ 기준소스
- 실코드: `features/wiki/ui/Markdown.tsx`(링크 렌더·resolveHref), `features/wiki/ui/WikiView.tsx`(레이아웃·SubjectView), `app/wiki/[...slug]/page.tsx`(단일문서 분기), `features/wiki/lib/links.ts`(resolveHref), `app/api/suggest/route.ts`(BFF 프록시 패턴), `shared/api/backend.ts`(봉투 해제), `features/chat/ui/ChatPanel.tsx`.

## ④ 금지영역
- 목록/폴더/chapter 렌더 경로 변경 금지(리더는 단일 문서 분기에만 추가). backend/study-note 변경 금지. #3(page.tsx fetch 최적화·workflow 폴더화)는 별도.

## ⑤ 검증 방법
- 빌드(tsc·next build 타입)·vitest. 스택 전이 로직은 순수 함수로 분리해 **단위 테스트**(push/replace-top/pop, 좌·우 클릭 분기, 길이 1 경계).
- 라이브(배포 후): 단일 문서에서 내부 링크 클릭 → 옆 pane / 왼쪽 클릭=교체 / 오른쪽 클릭=이동 / ESC·닫기=pop / 단일 복귀 / 외부링크 정상 / 챗봇 토글. 한글 경로.
- 반증: 링크가 denylist(docs) 가리키면 /api/doc 404로 안전? 외부 링크 인터셉트 안 되나? 스택 top 교체 vs push 분기 정확? 새로고침 리셋?
- 리뷰: 실행물 medium → 듀얼 1패스(렌더·상태전이·링크 인터셉트 렌즈).

## ⑥ stakes: 중간
새 상호작용 컴포넌트 + 신규 BFF 라우트 + 레이아웃 변경. 가역(코드). 데이터/보안 경계는 backend PathGuard 재사용.

## 자율성: auto

## load-bearing 가정
1. 내부 링크 인터셉트는 ClientMarkdown의 `a` 컴포넌트 onClick(preventDefault)으로 가능 — 내부/외부 판별은 resolveHref 결과가 `/wiki/`로 시작하는지.
2. `/api/doc` BFF는 suggest 라우트와 동일 패턴으로 backend 프록시 가능(backendGet 재사용). → 착수 직후 라우트 스모크로 조기 실증.
3. 스택 전이는 순수 함수로 분리 가능(테스트 용이) — UI와 분리.
