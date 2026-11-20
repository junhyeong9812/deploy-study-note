# requirement-spec — 이슈1: cs·workflow 지식을 study-note로 이전

> 작업 폴더 생성 시각: 2026-09-23. 대상 프로젝트 = **study-note**(git·배포 위키). 처리 기록은 deploy-study-note/docs(process 기록).
> 관련 후속: 이슈2(누락 결정문서 신규 작성 — BFF 패스스루·쿠키 3금기 등)는 **별도 작업 폴더**로 분리.

## ① 목표·대상
deploy-study-note/docs 아래의 **공부용 지식 문서**(cs 개념 3건 + workflow 흐름 7건)를 study-note로 이전한다. deploy-study-note/docs에는 이후 **구현 로그·스팩·TODO(히스토리)만** 남긴다.

이전 매핑:
| 원본 (deploy-study-note/docs) | 대상 (study-note) | 처리 |
|---|---|---|
| `cs/semaphore.md` | `cs/systems/semaphore/{1-question,2-summary,3-answer}.md` | 1/2/3 승격 (기준소스: llm wrapper `Semaphore(2)`, backend `streamExecutor` 3-thread) |
| `cs/RESP.md` | `cs/systems/resp-protocol/{1-question,2-summary,3-answer}.md` | 1/2/3 승격 (기준소스: ci-cd RESP-direct XADD logger) |
| `cs/backoff.md` | `cs/ops-patterns/01-retry-backoff/3-answer.md` | 기존 리프에 **우리 사례(ci-cd 재시도) 병합** — 신규 폴더 생성 안 함 |
| `workflow/{README,sync,search,deploy,chat-design,content,streaming-mvc-vs-webflux}.md` (7) | `study-note/workflow/` (신설 최상위) | 문서형 그대로 이전 |

이전 완료 후 원본(`deploy-study-note/docs/cs/`, `docs/workflow/`) 삭제.

## ② 경계·불변식
- **시크릿 0**: 이전 문서에 시크릿 값·내부 IP·자격증명 없음(스캔 완료 — 헤더 이름만 존재). 이전 중에도 새로 유입 금지.
- **기존 study-note 파일 훼손 금지**: `01-retry-backoff/3-answer.md`는 **append(우리 사례 절 추가)** 만, 기존 내용 변경·삭제 없음.
- **cs/systems 컨벤션 준수**: 18개 리프가 1/2/3 포맷 → semaphore·resp-protocol도 동일 3파일 구조 + 각 파일 상단 복습 안내 헤더(기존 리프와 동일 문구).
- **위키 트리 불변**: 새 최상위 `workflow/`는 리인덱스 시 사이드바 최상위 탭에 자동 노출. is_subject/README 규칙상 각 최상위·주제 폴더는 대표 문서 필요(workflow/README.md가 그 역할).
- deploy-study-note/docs의 **process 문서(plans/·secrets.md·measurement-log.md·TODO)는 이전 대상 아님** — 그대로 유지.

## ③ 기준소스
- 이전할 원본 내용 = `deploy-study-note/docs/cs/*.md`, `docs/workflow/*.md`(실파일).
- 1/2/3 승격의 코드 기준소스 = llm wrapper(`src/app/usecase/chat.py`, `api.py`)·backend(`chat/api/ChatController.kt`)·ci-cd(RESP XADD logger) 실코드.
- study-note 리프 포맷 기준 = `cs/systems/lsm-tree/`, `cs/ops-patterns/01-retry-backoff/`(실파일).

## ④ 금지영역
- study-note의 cs/systems·ops-patterns **기존 리프 다른 파일** 수정 금지(backoff 병합 1곳 예외, append only).
- 서비스 코드 repo(front/backend/llm/ci-cd) 변경 금지 — 본 이슈는 study-note 문서 전용.
- 결정문서 신규 작성(BFF·쿠키 3금기 등)은 **이슈2** — 본 이슈에서 손대지 않음.
- deploy-study-note/docs의 process 문서 삭제·이동 금지.

## ⑤ 검증 방법
- **스모크**: 이전 후 `find study-note/cs/systems/semaphore study-note/cs/systems/resp-protocol study-note/workflow` 로 파일 존재·구조 확인. 각 신규 md `head`로 헤더·내용 육안 확인.
- **트리 렌더**: 로컬에서 트리 빌드 로직이 새 최상위 `workflow/`를 리프/주제로 올바르게 잡는지 확인(is_subject·README 규칙). 불가 시 push 후 위키에서 최상위 탭·드릴다운 렌더 확인(사후 빚 아님 — 배포 전 최소 육안).
- **원본 삭제 검증**: `deploy-study-note/docs/cs/`·`docs/workflow/` 부재 확인, process 문서(plans/·secrets.md 등) 잔존 확인.
- **반증 질문**: 병합한 backoff가 기존 3-answer 흐름을 깨지 않나? workflow/ 최상위가 기존 cs·lab·project 탭 정렬을 흔들지 않나? 시크릿 재유입 없나?
- **발행**: study-note는 git repo → 브랜치 생성 → 커밋 → **push는 사용자 확인 후** → PR 생성도 사용자 확인. main 직접 작업 금지.

## ⑥ stakes: 중간
근거: 배포되는 위키 콘텐츠 변경 + 새 최상위 탭 트리 렌더 영향 + 1/2/3 승격의 코드 기준소스 확인 필요. 단 전부 git 이력으로 복구 가능(불가역 아님).

## 자율성
auto 제안(합의 후 자율 실행 — 검증은 위 ⑤ 비례). lazy 원하면 매 diff 확인.

## load-bearing 가정 (착수 직후 실증)
1. 위키 트리는 폴더 구조에서 생성되어 새 최상위 `workflow/`가 코드 변경 없이 자동 노출된다(사이드바 최상위 탭 하드코딩 없음). → 트리 빌드 로직/설정 1곳 확인으로 조기 실증.
2. 1/2/3 승격 시 기존 설명 내용을 3-answer 초안으로 이전 — 인출퀴즈 컨벤션상 사용자 자가 재산출은 이후 사용자 몫(초안 제공은 이전이지 대필 아님).
