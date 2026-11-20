# TODO - ci-cd (study-note 동기화)

## 2026-09-13 sync 워크플로우 실패 - 엣지 nginx의 curl User-Agent 차단

- 증상: study-note `.github/workflows/sync.yml` 12행의 `curl -sS -X POST https://www.junproject.xyz/api/sync`가 `curl: (92) HTTP/2 stream 1 was not closed cleanly: PROTOCOL_ERROR`, http 000으로 실패.
- 원인(실측 2026-09-13): 오라클 엣지 nginx가 User-Agent가 `curl/`, `python-requests/`인 요청을 연결 단계에서 끊는다. 같은 요청을 UA만 바꾸면 GET / 200, POST /api/sync 401(인증 필요, 엔드포인트 정상). 백엔드와 sync 엔드포인트는 문제 없음.
- 해결안(택 1):
  1. 워크플로우 curl에 UA와 HTTP/1.1 지정: `curl -sS --http1.1 -A "study-note-sync/1.0" -X POST "https://www.junproject.xyz/api/sync" ...` (UA는 `curl/`로 시작하지만 않으면 됨)
  2. 엣지 nginx UA 차단 규칙에서 `curl` 제외(봇 차단 의도가 있으면 1안).
- 이번(2026-09-13)에는 수동 동기화로 처리. push는 됐으나 사이트 미반영 상태였음(study-note main 1c85b7c).
- 관련: webhook(`POST /hooks/github`)은 GitHub 저장소에 미등록 - 등록하면 액션 없이도 동기화됨(HMAC 시크릿 필요).

## 2026-09-13 포트폴리오 사례 본문이 README.md라 검색 대상에서 빠짐

- 배경: 하위 폴더가 있는 폴더는 프론트가 `README.md`만 본문으로 렌더링(없으면 목록 폴백)하므로 study-note `portfolio/*/NN_*/post.md` 8건을 `README.md`로 바꿨다(study-note 89a5d63). 단계 48건(`해결과정/NN_*/post.md`)은 리프 폴더라 그대로 렌더링됨.
- 부작용: 검색 기본 kinds = summary, answer, post (D3: question, index, readme 제외)라 사례 본문 8건은 검색 결과에서 빠진다. 단계 48건은 검색됨.
- 선택지: (1) 검색 기본 kinds에 readme 포함 - 다른 폴더의 목차성 README도 같이 검색되는 부작용 확인 필요 (2) 프론트 폴더 렌더링에 `README.md` 없으면 `post.md`를 본문으로 쓰는 폴백 추가 후 study-note를 post.md로 되돌림 (3) 현상 유지.

---
## [해결됨 2026-09-13] 
- 4개 워크플로(sync.yml + backend/front/llm deploy.yml) curl에 `--http1.1 -A "study-note-*/1.0"` 추가 → 전부 http 202 통과 확인.
- 수동 동기화 완료(backend 직접, SHA 1c85b7ca, 61 files). 사이트 최신 반영.
- 기록: study-note project/study-note-deploy-system/ci-cd/issue5.
- 잔여: webhook 등록은 후속(선택).
