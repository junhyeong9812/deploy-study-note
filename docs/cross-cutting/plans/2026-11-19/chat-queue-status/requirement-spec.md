# requirement-spec — 채팅 대기열 표시 + 가상 스레드

> 2026-11-19. 대상 repo 3개: `llm`(래퍼) · `backend` · `front`. 각 repo마다 이슈→브랜치→PR→배포.
> 후속 작업(별도 명세): ②방문 추적+어드민(admin.junproject.xyz, ID/PW+TOTP, 90일 보관, 푸터 고지) ③Study 사이트.

## ① 목표·대상
문서 채팅에서 LLM 동시 2건이 차면 **줄을 세우고**(최대 8명·60초), 화면에 **"대기 중 (앞에 N명)"** 을 보여준다. "질문이 도착해 대기 중"과 "서버 자체 문제"를 화면에서 구별한다. backend는 **가상 스레드**로 대기 중인 연결을 싸게 붙잡는다.

## ② 경계·불변식
- **대기열 소유 = llm 래퍼**(GPU 동시성의 단일 소유자). 채팅만 줄을 세운다. **검색 재작성(/rewrite)은 지금처럼 즉시 거절→폴백**(계약 무변경).
- **상한**: 동시 생성 2 · 대기 8 · 대기 60초. 9번째 대기자 = 즉시 `queue_full`. 60초 초과 = `queue_timeout`. 상한 없는 대기 금지.
- **연결 유지**: backend는 SSE가 열려 있는 동안 15초마다 주석 줄(keep-alive)을 보낸다 — 시작 후 첫 토큰 전처럼 이벤트 사이가 길어져도 엣지가 끊지 않게(리뷰 감사 반영). backend는 llm 본문이 150초 동안 멈추면 스트림을 닫고 오류로 끝낸다.
- **무응답 방지**: 대기 중에는 순번이 안 바뀌어도 10초마다 `queued`를 다시 보낸다(엣지 nginx `proxy_read_timeout 60s` 실측) · SSE 응답에 `X-Accel-Buffering: no`. 엣지 conf는 건드리지 않는다.
- **순서**: 먼저 온 질문이 먼저 시작(FIFO). 대기 중 클라이언트가 끊으면 자리 반납(유령 대기 금지) · 세마포어 반납 누락 금지(예외 경로 포함).
- **스트림 계약(신설)**
  - llm→backend: `application/x-ndjson` 한 줄 = 이벤트 하나 — `{"type":"queued","position":N}`(순번 바뀔 때마다) · `{"type":"start"}` · `{"type":"token","text":"…"}` · `{"type":"error","code":"queue_full|queue_timeout|upstream"}` · `{"type":"done"}`.
  - backend→front→브라우저: `text/event-stream`(SSE) 같은 5종 이벤트. backend가 추가하는 오류 코드: `llm_unreachable`(연결 실패·타임아웃 = 서버 꺼짐) · `internal`.
  - 스트림이 열린 뒤의 오류도 **이벤트로** 전달(지금처럼 본문에 "[오류]" 글자를 섞지 않는다). 요청 검증 실패(422)만 기존 봉투 JSON 유지.
- **화면 문구 구별**: queued → "대기 중 (앞에 N명)" · start → 타자 렌더 · `queue_full`/`queue_timeout` → "지금 질문이 몰려 있어요, 잠시 후 다시" · `llm_unreachable` → "로컬 모델 서버가 꺼져 있어요" + **Claude 버튼 노출** · 그 외 → "응답 생성 실패".
- **이력 기록**: 답변이 정상 완료(done)된 경우에만 Redis 이력에 질문·답변 저장(대기 중 이탈·오류는 저장 안 함 — 현행 유지).
- **가상 스레드**: backend `spring.threads.virtual.enabled=true` + 채팅 스트림 실행기를 고정 풀(3)에서 가상 스레드 실행기로. 동시 연결 수는 래퍼 상한(2+8)이 제한.
- **Ollama 동시성**: `.164` `ollama/.env` `OLLAMA_NUM_PARALLEL=2`(래퍼 2와 일치). VRAM 실측 후 8GB 초과·CPU 오프로드 발생 시 1로 되돌리고 보고.
- 에스컬레이션(/chat/escalate)·이력(/chat/history)·세션 쿠키 계약 무변경.

## ③ 기준소스
llm `wrapper/src/app/{api.py,usecase/chat.py,usecase/rewrite.py}` · backend `chat/api/ChatController.kt`·`chat/usecase/ChatService.kt`·`shared/infra/LlmChatStreamClient.kt` · front `src/app/api/chat/route.ts`·`src/features/chat/ui/ChatPanel.tsx` · 실측(.164 `ollama/.env` NUM_PARALLEL=1·MAX_QUEUE=8·KEEP_ALIVE=30m, 2026-10-18).

## ④ 금지영역
/rewrite 동작·타임아웃 변경 금지 · 검색 경로 변경 금지 · Claude 자동 전환(별도 작업) 금지 · 추적/어드민 코드 혼입 금지 · 채팅 UI 디자인 개편 금지(상태 문구·버튼 노출만) · WebFlux 전환 안 함.

## ⑤ 검증 방법
- 단위: 래퍼 — 3번째 요청이 queued(position 1) 후 앞 건 종료 시 start / 11번째 = queue_full / 60초(테스트는 단축 주입) = queue_timeout / 대기 중 끊김 → 대기 수 감소 / 예외 후 세마포어 원복 / rewrite는 포화 시 여전히 즉시 503. backend — NDJSON→SSE 변환, 연결 실패 → `llm_unreachable`, 오류 시 이력 미저장. front — 이벤트별 상태 전이(파서 단위 테스트).
- 실행: 라이브에서 동시 4건 → 2건 생성·2건 "대기 중 (앞에 1·2명)" → 순서대로 시작. `.164` wrapper 정지 → "서버 꺼짐" 문구+Claude 버튼. `nvidia-smi`로 NUM_PARALLEL=2 VRAM·`ollama ps` 100% GPU.
- 반증: 프록시(Next·오라클 nginx)가 SSE를 버퍼링해 대기 이벤트가 늦게 오지 않나? 대기 60초가 엣지/front 타임아웃(180s)보다 짧은가? 탭을 닫으면 대기 자리가 실제로 빠지나?
- 리뷰: 중간 — 듀얼 1패스(Opus 워커 ∥ codex) + post-fix 재점검.

## ⑥ stakes: 중간
동시성·대기·타임아웃 + 3개 repo에 걸친 스트림 계약 변경. 데이터 변경 없음, repo별 revert로 복구.

## 배포 순서 (계약 호환)
1. **llm**: `/chat`이 `Accept: application/x-ndjson`일 때만 새 형식(대기열 포함), 아니면 기존 text 스트림 유지 → 먼저 배포해도 구 backend 무영향.
2. **backend**: NDJSON 소비 + `Accept: text/event-stream`일 때 SSE, 아니면 기존 text → 구 front 무영향. 가상 스레드.
3. **front**: SSE 소비 + 상태 문구. → 화면 확인.
4. 정리(구 text 경로 제거)는 3단계 확인 후 별도 커밋.
- **되돌리기는 역순**(front → backend → llm). 새 front + 구 backend, 새 backend + 구 llm 조합은 채팅이 전부 실패한다(리뷰 R7).

## 자율성
auto 제안. push·이슈·PR 생성은 각각 확인. 3단계(front) 후 화면 확인 대기.

## load-bearing 가정 (착수 직후 실증)
1. 오라클 nginx → 집 → Next 라우트 → backend 경로가 SSE 이벤트를 **버퍼링 없이** 즉시 흘려보낸다(현행 text 스트림은 흐름 — SSE도 같은지 1단계 전에 빈 SSE로 스모크).
2. `OLLAMA_NUM_PARALLEL=2`에서 qwen3:8b가 8GB VRAM에 100% GPU로 올라간다.
