# log — chat-queue-status

| 시각(KST) | 사건 | 결과 |
|-----------|------|------|
| 11-19 17:1x | 명세 합의 · auto | set-state spec-approved / mode auto. 기준 SHA: llm d16d7be · backend 3944f1e · front de1be91 |
| 11-19 17:20 | 가정1 스모크 — 현행 text 스트림을 엣지 경유로 청크 시각 측정 | 204청크가 3.55s~6.82s에 걸쳐 도착 = 엣지·Next 구간 비버퍼링 확인. 단 엣지 conf `proxy_read_timeout 60s`·`proxy_buffering` 기본값 → SSE는 `X-Accel-Buffering: no` + 대기 중 10초 간격 queued 재전송(heartbeat)으로 방어(명세 ②에 추가) |
| 11-19 | 부산물: `.164 ~/llm-boot.log`에 11-18 07:16 재부팅 기록 | `@reboot` 경로 실증됨(llm-host-boot-autostart 생략 검증 해소) |
| 11-19 17:25 | 가정2 스모크 — .164 `ollama/.env` NUM_PARALLEL=2(서버 작업트리만 수정)·ollama 재생성 | `ollama ps` 6.2GB **100% GPU** · VRAM 6042/8192MiB · 동시 2건 각 64 tok/s(단독 70) 동시 완료 = 진짜 병렬. 가정 성립. repo 반영은 llm PR에서 |
| 11-19 17:2x | llm 구현(브랜치 feat/chat-queue, 8b298bc) — spec 기준 테스트 선작성(red) → 구현 | pytest 41 passed(기존 29 + 신규 12, docker python:3.12). 중첩 async 제너레이터가 닫힐 때 대기 정리가 지연되는 결함을 테스트가 잡음 → `aclosing`으로 수정 |
| 11-19 17:3x | backend 구현(feat/chat-queue-sse, dd847d1) | gradle test 34 passed(신규 6, docker temurin:21 — 호스트 `.gradle`·`build`가 root 소유라 로컬 실행 불가) |
| 11-19 17:3x | front 구현(feat/chat-queue-status, b0ddcba) | vitest 28 passed(신규 6) · tsc 신규 오류 0 · docker build 성공(node 22) |
| 11-19 17:4x | 리뷰 ⓪ packet — OUT=`scratchpad/review.WerH`(packet·mirror·results) · 보안 스캔 매칭 0 | ① Opus 워커 ∥ codex(medium, read-only, cwd=미러) 병렬 실행 |
| 11-19 17:5x | 리뷰 ① codex 1차 | **실패** — `bwrap: loopback: Failed RTM_NEWADDR`로 미러 읽기 불가, 전 렌즈 "판정 불가". 1회 재시도: packet+변경 파일 전문을 stdin에 인라인(codex는 인라인 자료만, Opus는 미러 전체 = **입력 비대칭**) → finding 5 |
| 11-19 18:0x | 리뷰 ① Opus 워커(opus, 127k 토큰, 23 tool) 회수 | finding 8 + open question 7. Grep/Glob 미가용으로 Read만 사용(README·설계 문서는 related-raw로만 확인 — packet 기재) |
| 11-19 18:0x | 리뷰 ② 메인 종합 → ③ codex 종합 감사 | 채택 13(R1~R13). 감사: OQ4 기각 오류·R4/OQ3 무응답 미해결·R6 범위 부족 지적 → 전부 반영(SSE keep-alive 15s, 이력 조회 abort, 본문 중 오류=upstream) |
| 11-19 18:1x | ④ 수정 — llm 8c85628 · backend 5068fe7 · front a49a6bd | pytest 42 · gradle 46 · vitest 35 passed · front docker build 성공. MockMvc에서 한글이 `??`로 깨짐 발견 → 스트림 텍스트 UTF-8 명시+응답 문자셋 지정(실서버는 Boot 기본이 UTF-8이라 구 경로는 정상이었음 — 방어 추가) |
| 11-19 18:2x | post-fix 타깃 재점검 1 — codex | R1~R13 해소 확인. 새 결함 1: keep-alive 전송 실패를 삼켜 이탈 후에도 생성 슬롯 점유(P1) + 테스트 보강 요구 3 |
| 11-19 18:3x | P1 수정(backend c843117) → 재점검 2 | 해소 방향 확인, 잔여: 이탈 신호가 작업 스레드 등록보다 먼저 오는 경합(P2)·테스트 공유 목록 비동기화 |
| 11-19 18:4x | P2 수정(7e3b139) → 재점검 3 | **제품 코드 미해소 없음**. 테스트 실패 시 스레드 정리 지적 → 반영(테스트만, 재점검 생략). 최종: pytest 42 · gradle 49 · vitest 35 passed |
| 11-19 17:4x~18:1x | **부산물: www 504 조사**(사용자 질문) | 엣지 nginx 504 40건 전부 `connect` 단계 10s 초과(설정 보수성 아님 — 평소 connect 4ms). 3경로 20분 감시(엣지→집, LAN→.9, .9→밖): 실패는 09:04:17~37(UTC) **세 경로 동시**, `.9 enp4s0 Link is Down/Up` 3회와 초 단위 일치. 플랩 ≈37분 주기·하루 ~115회·1주일 이상, 링크 100Mbps 고정·align_errors 24 → 랜선/포트 물리 계층 의심. 단 08:43~44 군집·09:14:37 단발은 플랩 시각과 불일치 = **두 번째 원인 미확정**. 도커 실행 연관은 실험으로 배제. 별도 작업 후보 |
| 11-19 18:28 | 사용자: 이슈·push·PR·병합 진행 승인(3건) | llm #18→PR #19 · backend #32→PR #33 · front #41→PR #42 병합 |
| 11-19 18:28 | llm 배포 확인 | Actions http:202 · agent deploy ok 893e629(13s) · wrapper healthy · CHAT_* env 반영. 스모크(.158→wrapper 동시 4건): 1·2 즉시 start, 3 queued#1, 4 queued#2→#1, 17s에 순차 start, 4건 done. VRAM 6050MiB·100% GPU. 구 backend 경유 채팅 정상 |
| 11-19 18:30~37 | backend 배포 확인 | http:202 · deploy ok f59e96c(**411s**) — `compose up --build app`이 ES 이미지까지 다시 빌드해 **backend-es 재생성(검색 약 30초 중단)**, 인덱스 study-v1 66,387 docs 보존 확인. SSE 직접 호출 정상(한글 정상·X-Accel-Buffering)·로그 스레드 `virtual-NN`·구 front 경유 text 경로 정상 |
| 11-19 18:38~40 | front 배포 확인 | http:202 · deploy ok a5ff80f(96s) · healthy |
| 11-19 18:41 | E2E(엣지 경유 동시 4건) 1차 | 3·4번이 done 없이 절단 — `.9 enp4s0` 플랩(09:41:29Z)과 일치, backend `chat client gone` 기록(정상 반응). 재실행: queued 이벤트 1.1s·1.6s 도착(=엣지·Next 무버퍼링), 10s 재전송·15s keep-alive 확인, #2→#1 즉시 통지, 4건 done |
| 11-19 18:43 | E2E 대기 중 이탈(3번을 6s에 종료) | **결함 발견** — backend는 10s 뒤 `client gone` 인지했으나 llm이 자리를 안 놓고 그 요청을 끝까지 생성(tokens~971). 격리 실험(.158→wrapper 소켓 종료)로 래퍼 원인 확정: uvicorn 0.30.6+Starlette 0.46.2는 끊김을 본문 제너레이터에 전달하지 않음(쓰기 무시) |
| 11-19 18:5x | 수정(llm 브랜치 fix/chat-queue-disconnect, dadee8b·a0e233b) | `request.is_disconnected()` 0.5s 폴링 + 이벤트 태스크 선종료. codex 재점검 4: 취소 경로 정리 순서·동시 완료 우선순위 지적 → 반영. 실제 uvicorn 소켓 테스트 추가 — **수정 전 코드 실패/수정 후 통과** 확인. pytest 45 passed |
| 11-19 18:5x | 위 수정의 이슈·PR·병합 시도 | **차단됨**(자동 모드 분류기 — 사용자 승인 범위 3건 밖). 로컬 커밋만. 사용자 확인 대기 |
| 11-19 18:5x | E2E 모델 서버 꺼짐 | llm-wrapper 정지 → SSE `event:error {"code":"llm_unreachable"}` 0.16s · 재기동 후 start·done 정상 |
| 11-19 20:1x | 사용자: P3 수정 발행 승인("진행하자") | llm 이슈 #20 → 브랜치 fix/20-chat-queue-disconnect push → PR #21 병합(78e8bf2) |
| 11-19 20:14 | llm 배포 1차 | **미배포** — Actions는 success였으나 배포 호출이 엣지에서 `http:504`(워크플로가 비-2xx를 실패 처리하지 않음). .164는 893e629 그대로임을 서버에서 확인 |
| 11-19 20:15 | 워크플로 재실행 | http:202 · agent deploy ok 78e8bf2(3s) · wrapper healthy · 컨테이너 안 api.py에 수정 반영 확인 |
| 11-19 20:16 | 재실험 ① 래퍼 직접(.158→wrapper, 대기 1번을 3.8s에 소켓 종료) | 래퍼 `chat client gone` 3.0s 뒤 기록, 4번 순번 #2→#1 **3.8s에 즉시**, 슬롯이 빈 19.5s에 start. 3번은 생성 안 함. P3 해소 |
| 11-19 20:17 | 재실험 ② 엣지 경유(e2e.py kill, 대기 1번 종료) | 4번 #2→#1이 16.2s에 통지, 19.6s start·34.9s done. 3번 생성 없음. 자리 반납까지 약 10초 = backend가 15초 keep-alive 전송 실패로 이탈을 알아채는 간격(상한 15s). spec ⑤ 반증 '이탈 시 자리 반납' 성립(브라우저 탭 닫기 자체는 화면 확인에서) |

## 리뷰 ledger

| id | loop | source | 근거 | disposition | status | fixed |
|----|------|--------|------|-------------|--------|-------|
| R1 | 1 | codex·opus | front chatStream.ts 대기 문구(position-1) vs spec ②·⑤ | 채택 | fixed | 1 |
| R2 | 1 | codex | llm chat.py — Ollama done 없이 끝나도 done 발행 | 채택 | fixed | 1 |
| R3 | 1 | codex·opus | backend LlmChatStreamClient — 헤더 타임아웃·리셋이 internal | 채택 | fixed | 1 |
| R4 | 1 | codex·opus | backend 본문 읽기 유휴 제한 없음 | 채택 | fixed | 1 |
| R5 | 1 | codex | front SSE CRLF 조각 경계 | 채택 | fixed | 1 |
| R6 | 1 | opus(+감사: 이력 조회) | front ChatPanel — 요청 미취소로 유령 대기·화면 덮어쓰기 | 채택 | fixed | 1 |
| R7 | 1 | opus | 롤백은 역순일 때만 성립 | 채택(문서) | fixed — spec 배포 순서 절 | 1 |
| R8 | 1 | opus | spec ⑤ 테스트 범위 미달(NDJSON→SSE·llm_unreachable·상태 전이) | 채택 | fixed — LlmChatStreamClientTest·ChatControllerSseTest·applyStreamEvent 테스트 | 1 |
| R9 | 1 | opus | llm 낡은 주석·문서·CHAT_* env 미전달 | 채택 | fixed | 1 |
| R10 | 1 | opus | llm api.py aclosing 누락 | 채택 | fixed | 1 |
| R11 | 1 | opus | queued 로그 중복 | 채택 | fixed | 1 |
| R12 | 1 | opus OQ6 | Done 후 전송 실패 시 이력 미저장 | 채택 | fixed | 1 |
| R13 | 1 | opus OQ1 | Next 압축 버퍼링 가능성 | 채택(소) | fixed — no-transform, 실경로 스모크로 확인 예정 | 1 |
| A1 | 1 | 감사 | 이벤트 사이 60s 무응답(시작~첫 토큰) — 엣지 절단 | 채택 | fixed — backend SSE keep-alive 15s | 1 |
| P1 | post-fix | codex | backend ChatController keep-alive 실패 무시 → 이탈 후 슬롯 점유 | 채택 | fixed(c843117) | post-fix |
| P2 | post-fix | codex | 이탈 신호·작업 등록 경합 | 채택 | fixed(7e3b139) | post-fix |
| P3 | 배포 검증 | main(E2E) | llm api.py — 상대 연결 종료 미감지로 대기 자리·슬롯 점유(spec ② 유령 대기) | 채택 | fixed(PR #21, 78e8bf2) — 배포·실측 확인 | post-deploy |
| - | 1 | opus OQ7 | 모든 종료 결과에서 Claude 버튼 노출 | 기각 — spec ②는 llm_unreachable 시 노출 요구(충족), 금지 조항 없음·UI 개편 금지(spec ④) | - | - |
| - | 1 | opus OQ2 | Next `request.signal`이 탭 종료 시 abort되는가 | open question — 배포 후 실측(spec ⑤ 반증) | open | - |

## 생략한 검증
- keep-alive 실패가 실제 요청에서 스트림 작업을 깨우는지의 통합 테스트 — MockMvc로 연결 끊김을 재현하기 어려워 미작성. 대체: 배포 후 '대기 중 탭 닫기 → llm 대기 수 감소' 실측(spec ⑤ 반증).
- codex 리뷰 입력 비대칭(인라인 자료만) — 샌드박스 중첩으로 미러 읽기 불가.
