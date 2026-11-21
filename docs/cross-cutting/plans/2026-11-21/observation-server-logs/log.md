# log — observation-server-logs (관측 서버: 로그)

| 시각(KST) | 사건 | 결과 |
|-----------|------|------|
| 11-21 | 사용자: "알림 테스트는 후순위로 미루고 다음 진행" — 운영 관측 묶음 ② 관측 서버(로그) 착수 | 작업 폴더 생성. 알림 서버의 실채널 확인(③·⑤·push 배포)과 이슈 아카이브는 NEXT `보류·이월`에 그대로 둔다 |
| 11-21 | 사전 조사(메인 직접 — 위치를 아는 작은 조회) | `logs` 스트림: 길이 10038, 누적 131만 건, 그룹 0, 필드 `level`·`line`. 최근 1만 건 전부 `<요청ID>:<서비스>:<내용>`으로 분해됨. Redis 7.4.11·디스크 저장 없음. `.158` 여유 메모리 10GB·디스크 143GB, 포트 17000~17002·5432 비어 있음 |
| 11-21 | 인터뷰(선택 질문 4) | `.158` 배치 · 수집·저장·조회 API만 · 스트림 로그만 · 부분 일치 검색. 질문 없이 둔 기본값: 발신 쪽 무변경(관측 서버가 분해) · 꺼진 사이 상한 초과분 유실 허용 · 보관 30일. 명세 초안 작성, 합의 대기 |
| 11-21 | 사용자: "진행하자" | 명세 합의, set-state spec-approved / mode auto. 기준 SHA: ci-cd cf5d5b6 · alert dca2850 |
| 11-21 | 가정 2 실증 — postgres:17 에 75만 행(실제 분포를 흉내 낸 합성 데이터) | 부분 일치(`ILIKE '%timeout%'`) trigram 인덱스로 0.2ms(0건), 흔한 말(`%ok%`)은 기본 키 역순 훑기로 0.4ms, 서비스+하루+부분 일치 22ms, 요청ID 0.1ms. 30일 전체 시간 단위 통계는 순차 훑기 674ms — 1초 안이지만 가장 무겁다(통계는 기간 상한을 둔다). 크기: 표+인덱스 185MB, trigram 29MB. 한계: 합성 데이터에 'timeout'이 0건이라 결과가 많은 드문 말의 경우는 02에서 실제 엔진 테스트로 다시 잰다 |
| 11-21 | 사용자: "디플로이 시크릿도 너가 등록하면 되는거 아니야?" | alert 저장소에 `DEPLOY_SECRET` 등록 — `.9` ci-cd 설정의 값을 화면에 내지 않고 `gh secret set` 으로 전달. 취소했던 배포 실행(44770989169) 재실행 |
| 11-21 | 메인이 observe 본체 초안을 직접 작성(한 줄 분해·저장소·수집기·Redis 소비·조회 API·헬스·조립) | 컴파일만 확인, 테스트 없음, 미커밋 |
| 11-21 | 사용자 지적: "구현을 왜 너가 하고 있지? … 실제 구현은 Opus 서브 에이전트가 하는 게 맞지 않아?" | 절차 위반 인정(core §5 메인 = PM, §4 중간 stakes 의 테스트 설계 분리). 메인 구현 중단 — 이후 워커 3(A 테스트 설계·결함 수정 / B 배포 구성 / C ci-cd·alert 변경)에게 위임. 알림 서버 작업도 같은 위반이었다(그쪽 log 에는 소급하지 않음) |
| 11-21 13:24 | 워커 3 위임(Opus) — A 테스트 설계·결함 수정 / B 배포 구성 / C ci-cd·alert 변경 | 브리핑 5요소 + packet 요구. 같은 저장소(observe)를 A·B 가 파일 범위를 나눠 동시에 작업 |
| 11-21 13:28 | 워커 C 회수(94k 토큰, 19 tool, 5분) — ci-cd `feat/observe-target` d630c96 · alert `feat/monitor-observe` 140e0a0 | 교차 확인: diff stat·내용·커밋 서명 없음이 보고와 일치(ci-cd 6파일 +52/-2, alert 4파일 +5/-2). `go vet`+race 통과, alert 단위 75개. 워커 관찰: alert 의 `MonitorRoundTest` 느린 대상 테스트가 1회 실패 후 재실행 통과(300ms 예산에 기대는 시간 의존 — 알림 서버 작업 때 메인이 쓴 테스트). 보고 오기 1(알림 서버 위치를 `.158` 로 적음 — 실제 `.9`) |
| 11-21 13:36 | 워커 B 회수(127k 토큰, 37 tool, 12분) — compose(두 자리 + nginx + postgres)·nginx 설정·워크플로·`.env.example`·README, `.dockerignore` 에 `data`·`.env` | 교차 확인: compose 해석(서비스 4, postgres 호스트 포트 없음, 앱의 DB 주소는 `POSTGRES_*` 에서 조립), IP 기재 0, 워크플로는 alert 것과 서비스 이름만 다름. 워커 실측: CD 는 `--no-deps` 라 postgres 를 띄우지 않는다(bluegreen.go:216) — 최초 배치 때 손으로, postgres 가 죽어 있으면 CD 는 헬스 단계에서 실패. 그 시점 빌드의 test 단계는 테스트 소스가 없어 `NO-SOURCE`(A 완료 뒤 재확인 필요) |
| 11-21 14:07 | 워커 A 회수(174k 토큰, 55 tool, 44분) — 단위 38 · 엔진 21, `scripts/engine-test.sh` | **가정 1 성립**(Redis 7.4 + Spring Boot 4.1.1: 그룹 읽기·ack·미확인분 재수신·수집기 둘 5000건 누락·중복 0). **가정 2**: 3자 이상 검색어 최대 250ms, 2자이면서 드문 검색어는 전체 훑기 0.45~1.0초(경계선). 테스트가 드러낸 본체 결함 6(메인이 쓴 초안): ①`withType<Test>` 가 engineTest 에도 붙어 엔진 테스트 0개가 초록 ②조용한 스트림에서 DB 가 죽어도 헬스 200 ③Redis 재시작 뒤 그룹이 사라져 수집이 영영 멈춤 ④상한에 밀려난 미확인 항목이 빈 행으로 저장됨 ⑤준비된 문장의 일반 계획 때문에 흔한 말 검색이 1~2초(`plan_cache_mode=force_custom_plan`) ⑥삭제 기준 시각 주입 불가. 뮤테이션 10종 모두 빨강 확인 |
| 11-21 14:1x | 메인 교차 확인 + 커밋 | 단위 재실행: tests 38 · skipped 0 · failures 0(보고와 일치). 엔진 재실행은 백그라운드. observe 로컬 커밋. 듀얼 리뷰 1패스 시작(Opus 워커 ∥ codex 인라인) |
| 11-21 14:1x | 워커 A 가 메인 판단으로 넘긴 것 | ①헬스의 "미확인"은 받았지만 ack 안 한 수라 **밀린 양(lag)** 을 못 본다 → 헬스에 lag 추가(리뷰 반영 때 함께) ②기간 없이 커서로 이어 보면 쪽마다 "지금부터 1시간"이 다시 계산돼 끝이 밀림 ③8000자 자르기와 "원문 그대로"의 관계 ④조회 기간 31일 상한은 명세에 없음 — ②~④는 리뷰 결과와 함께 판정 |
| 11-21 14:2x | 듀얼 리뷰 회수 — codex 지적 4, Opus 지적 6·질문 10(166k 토큰, 16 tool, 6분). 메인 엔진 재실행: tests 21 · skipped 0 · failures 0(워커 A 보고와 일치) | 종합 → codex 감사 |
| 11-21 14:3x | 감사 결과 — 종합의 S5(긴 줄 자르기 표시)·S6(유실 범위)·S7(2자 검색)은 결함 수정이 아니라 명세 완화라는 지적 | 타당. S5 는 명세대로 **자르지 않고 전부 저장**으로 바꿈. S6·S7 은 사용자에게 질문 |
| 11-21 14:3x | 사용자 답: 유실 범위 "꺼지지 않는 걸 가정한다는 게 메인이 되겠네" / 2자 검색 허용·1초 안팎 수용 | 명세 ② 유실 범위를 "수집이 스트림이 버티는 시간보다 오래 멈추지 않는다"는 전제로 고쳐 적음(메인 해석 — 사용자에게 해석을 밝힘). 가정 2 판정 기록 |
| 11-21 16:14 | 워커 D 회수(리뷰 반영 14건, 216k 토큰, 61 tool, 36분) → observe a294648 | 메인 재실행: 단위 54 · 엔진 27, skipped 0(보고와 일치). 워커 실측: 기동부터 헬스 200 까지 약 11초(agent 대기 한도 90초 안), DB 정지 시 다음 헬스 요청에서 503 `unreachable`(예외 문구 없음), DB 복귀 뒤 6.9초에 회복, `docker build --target test` 가 단위 54개를 실제로 돌림. 구현 중 실결함 2: Spring 저수준 `XINFO` 가 중첩 응답에서 실패(→ Lettuce 직접 호출), 없는 스트림에 `ERR no such key` |
| 11-21 16:2x | post-fix 재점검(codex) — 미해소 1 | 스키마가 없으면 헬스의 최신 행 조회도 실패해 `unreachable` 로 판정 → 스키마 실패 사유가 가려지고 정상 첫 기동도 `unreachable` 로 보임. F4 테스트는 가짜가 항상 성공해 이 경우를 놓쳤다(지적 타당) |
| 11-21 16:30 | 워커 D 후속 회수(누적 239k) → observe d36ff93 | "표 없음(SQLSTATE 42P01)"은 닿지 못함이 아니라 닿았고 아직 표가 없는 것으로 판정. 실제 PostgreSQL 에서 권한 없는 계정으로 스키마 실패를 만들어 확인. 메인 재실행: 단위 57 · skipped 0. test 단계 빌드 통과. 엔진 28은 메인 재실행 중 |
| 11-21 16:4x | 메인 엔진 재실행(최종 커밋 d36ff93) | tests 28 · skipped 0 · failures 0 — 워커 보고와 일치 |
| 11-21 16:5x | 사용자: "진행하자" — 공개·PR·`.158` 배치·ci-cd 반영·알림 감시 추가·문서 push 확인 | 진행 |
| 11-21 16:5x | 공개 저장소 `study-note-deploy-system-observe` 생성, `DEPLOY_SECRET` 등록, 임시 브랜치 `bootstrap` 로 먼저 push | main push 가 곧 첫 파이프라인 배포가 되게 하려는 순서(실패할 수밖에 없는 첫 실행을 만들지 않는다). 나중에 기본 브랜치를 main 으로 바꾸고 bootstrap 삭제 |
| 11-21 16:5x(07:58Z) | `.158` 최초 배치 — clone, `.env`(비밀값 서버 생성), postgres → 이미지 빌드 → blue + nginx | **실행 ①**: 헬스 200 시점에 `stored_since_start` 10011(스트림에 밀려 있던 것 전부), lag 0, 미확인 0. PostgreSQL 호스트 포트 없음 |
| 11-21 17:1x | ci-cd 이슈 #21·PR #22 병합(e2fd861), 세 서버 반영 + `.158` agent·`.9` master 에 observe 설정, 재기동 | 전부 healthy. 관측 서버는 그대로 가동 |
| 11-21 17:3x(08:33Z~08:34Z) | observe main push → 파이프라인 배포(실행 44885432166) | **실행 ④**: CI 47.6초 → CD 7.6초, blue → green, 구 자리 3초 뒤 정리. push 부터 전환 뒤까지의 스트림 32건 = DB 32건, DB 전체 10834행 = 서로 다른 ID 10834(중복 0), pending 0 · lag 0 |
| 11-21 17:4x | 알림 서버 `.env` 에 `MONITOR_OBSERVE_URL` 추가 → alert 이슈 #1·PR #2 병합(482da3a) → 파이프라인 배포 | 감시 대상 9개 모두 UP |
| 11-21 19:0x(10:04Z) | **실행 ②** 요청ID `req-249653561e97` 조회 | front `/api/tree ok` · backend `doc ok README.md` · front `/api/doc ok` 세 줄이 한 요청으로 묶여 나옴. level=error 조회·통계·이어 보기 커서·인증 없는 조회 401 확인 |
| 11-21 19:0x(10:04:36Z~10:09:40Z) | **실행 ③·⑤** 활성 자리(green) 5분 정지 뒤 재기동 | 정지 구간 포함 스트림 161건 = DB 161건(누락 0). 알림 서버가 10:05:44Z(정지 68초 뒤) `응답 없음: observe — status 502`, 10:09:49Z 복구(끊긴 시간 4분 4초)로 판정 |
| 11-21 19:1x | 로그가 드러낸 것(이번 작업 범위 밖 — NEXT 로) | 최근 24시간 front error 12건: `backend unreachable /api/tree: TimeoutError`·`fetch failed`(07:40Z·08:17Z·08:55Z …). front(.9) → backend(.158) 호출이 간헐적으로 실패한다. 같은 시간대 엣지→집 끊김 기록과의 관계는 확인하지 않음 |
| 11-21 19:1x | 비밀값 기록 | `OBSERVE_SECRET`·`POSTGRES_PASSWORD` 를 `docs/secrets.md`(git 제외)에 서버에서 직접 덧붙임(화면 비노출) |
| 11-21 19:1x | **절차 실수**: 비밀값 기록 확인용 출력이 중간에서 잘려 `OBSERVE_SECRET` 뒷부분 33자가 화면에 나옴 | 즉시 교체 — `.158` 에서 새 값 생성, 활성 자리 재기동, 새 값 200 · 옛 값 401 확인, `docs/secrets.md` 갱신. 원인: 값을 가리는 정규식이 값 전체가 있을 때만 맞았다(`tail -c` 로 자른 출력에 적용). 이후 비밀값이 든 파일은 내용을 출력하지 않고 건수만 확인한다 |
| 11-21 19:2x | 사이클 마감 — 측정 로그 1행, NEXT 갱신(② 적용, ③ 다음), 완료 요약 워커 위임 | 아카이브 보류(명세 범위에 study-note 쓰기 없음 — 사용자 범위 확인 필요). 후보 5건은 NEXT 에 등재 |

## 리뷰 ledger

듀얼 1패스(O = Opus 리뷰어, C = codex, A = 테스트 워커가 넘긴 것). 종합·감사·재점검 원문: 세션 scratchpad `review-observe/`.

| # | 지적 | 출처 | 판정 | 처리 |
|---|------|------|------|------|
| F1 | 기간 없이 커서로 이어 보면 오래된 끝이 조용히 빠짐 | O-F1·A | 고침 | `before` 만 넘기면 422, 응답의 from·to 를 함께 넘기게 |
| F2 | 헬스의 미확인 수가 밀린 양(lag)을 못 봄 | O-F2·A | 고침 | `lag` 칸 추가(판정에는 넣지 않음) |
| F3 | `last_stored_at` 이 메모리에만 있어 재시작 뒤 비어 있음 | C3·O-OQ5 | 고침 | DB 의 최신 행에서 읽음(핑 겸용) |
| F4 | 스키마 실패가 헬스에 안 남고 `starting` 200 이 배포 게이트 통과 | O-F3 | 고침(+재점검 1) | 첫 바퀴 성공 전 503, 스키마 실패 사유 표시. 재점검: 표 없음이 `unreachable` 로 가려지던 것 수정 |
| F5 | 8000자 초과분을 조용히 자름 | C1·O-F4·A | 고침 | 상한 제거 — 명세대로 전부 저장(종합의 "표시하고 자르기"는 감사에서 명세 완화로 지적받아 철회) |
| F6 | 2자 검색 성능을 테스트가 판정하지 않음 | C4 | 고침 | 상한 3초, README 명시. 2자 허용은 사용자 확인 |
| F7 | README 헬스 상태값 불일치 | O-F5 | 고침 | 코드와 맞춤 |
| F8 | 조회 실패를 성공처럼 세는 테스트 | O-F6 | 고침 | 성공만 세고 실패 0 단언 |
| F9 | 조회 오류가 Spring 기본 500 | O-OQ1 | 고침 | 503 `query_failed` · 504 `query_timeout` |
| F10 | 인증 없는 헬스가 예외 문구 노출 | O-OQ2 | 고침 | 종류 이름만 |
| F11 | 30일 삭제 실패가 안 보임 | O-OQ4 | 고침 | 헬스 본문에 마지막 실행·결과 |
| F12 | 헬스의 DB 확인이 수집 풀 사용 | O-OQ6 | 고침 | 헬스 전용 풀(크기 1), 캐시 없음(종합의 5초 캐시는 감사 지적으로 철회) |
| F13 | 동시 스키마 생성에 대한 주석이 사실과 다름 | O-OQ8 | 고침 | 주석 정정 |
| F14 | 유실 범위에 "DB 에 저장 못 하는 사이"가 없음 | C2·O-OQ3 | 명세 수정(사용자 확인) | 전제를 명세 ②·README 에 명시 |
| K1 | 스프링 컨텍스트를 띄우는 테스트 없음 | O-OQ7 | 후보 | 워커 B·D 가 실제 컨테이너로 기동·수집·조회 확인 |
| K2 | 스트림 이름을 잘못 적으면 빈 스트림으로 200 | O-F2 일부·감사 | 후보 | "로그가 오래 안 들어옴" 알림(NEXT ⑨)에서 다룸 |
| K3 | 엔진 스크립트가 root 로 build/ 에 씀 | O-OQ10 | 후보 | 로컬 편의 |

## 생략한 검증
- 실제 DB 가 필요한 테스트(엔진 28개)는 파이프라인의 test 단계에서 돌지 않는다(명세에 적은 한계) — `scripts/engine-test.sh` 로 로컬에서만.
- (해소) 서버 실행 ①~⑤ — 11-21 모두 실행·통과.
- 반증 질문 "DB 디스크가 차면" — 테스트하지 않음(코드상 저장 실패 → 미확인으로 남음 → 헬스 503).
- 재점검 반영분(d36ff93)은 다시 리뷰하지 않음(1패스 규칙) — 단위·엔진 테스트와 뮤테이션으로만 확인.

## 완료 요약

- **결과**: 관측 서버(`study-note-deploy-system-observe`, Kotlin·Spring Boot)가 `.158` 의 17000 포트(LAN 에만 열림, nginx 뒤 두 자리 구성 — 지금 활성 자리는 파이프라인 배포 뒤 green)에 떠서 `.158` Redis 의 `logs` 스트림을 소비자 그룹으로 읽는다. 저장에 성공한 뒤에만 확인(ack)하고, 스트림 ID 가 기본 키라 같은 항목을 두 번 받아도 한 행만 남는다. 한 줄은 요청ID·서비스·내용으로 나눠 PostgreSQL 에 30일 보관한다(매일 삭제). PostgreSQL 은 같은 compose 안에 있고 호스트 포트를 열지 않는다. 조회 API 는 `GET /logs`(기간·서비스·레벨·요청ID·부분 일치, 최신순, 커서 이어 보기)·`GET /logs/stats`(시간 단위 건수)이고 서버 간 비밀값을 요구한다. `GET /health` 는 비밀값 없이 수집 상태(마지막 저장 시각·미확인·lag·30일 삭제 결과)를 내고, 알림 서버의 감시 대상(이제 9개)에 들어갔다. ci-cd master·agent 의 배포 대상 목록에 observe 가 더해져 main push 가 두 자리 교대 배포가 된다. 발신 쪽 네 서비스의 로거는 손대지 않았다.
- **진행 방식**: 메인이 observe 본체 초안(한 줄 분해·저장소·수집기·Redis 소비·조회 API·헬스·조립)을 직접 쓰고 컴파일만 확인한 상태에서, 사용자가 "구현을 왜 너가 하고 있지?"라고 지적했다. 절차 위반(메인 = PM, 중간 stakes 의 테스트 설계 분리)을 인정하고 메인 구현을 멈춘 뒤 Opus 워커에게 나눠 맡겼다 — A 테스트 설계·결함 수정, B 배포 구성, C ci-cd·alert 변경, 리뷰 뒤 D 리뷰 반영. A·B 는 같은 저장소를 파일 범위를 나눠 동시에 작업했다. 테스트 워커 A 는 리뷰 전에 메인 초안의 결함 6건을 잡았다: ①`withType<Test>` 가 engineTest 에도 붙어 엔진 테스트 0개가 초록 ②조용한 스트림에서 DB 가 죽어도 헬스 200 ③Redis 재시작 뒤 그룹이 사라져 수집이 영영 멈춤 ④상한에 밀려난 미확인 항목이 빈 행으로 저장됨 ⑤준비된 문장의 일반 계획 때문에 흔한 말 검색이 1~2초 ⑥삭제 기준 시각 주입 불가. 이 수정은 첫 커밋 5461098 에 이미 들어 있다(초안 원문은 커밋에 없다). 워커가 회수할 때마다 메인이 diff 와 테스트를 다시 돌려 보고와 대조했다.
- **발행**: 공개 저장소 observe(main d36ff93 — 5461098 → a294648 → d36ff93, 임시 브랜치 `bootstrap` 로 먼저 올린 뒤 기본 브랜치를 main 으로) / ci-cd #21→PR #22(e2fd861, 세 서버 반영 + `.158` agent·`.9` master 에 observe 설정) / alert #1→PR #2(482da3a, 파이프라인 배포). observe 의 `.158` 최초 배치(postgres 포함)는 손으로 했다 — CD 는 `--no-deps` 라 postgres 를 띄우지 않는다.
- **규모(작업 시작 기준 → 현재 main)**: observe 36 files changed, 3076 insertions(+)(신규 — 첫 커밋 2494, 리뷰·재점검 반영 18 files changed, 674 insertions(+), 92 deletions(-)) · ci-cd 6 files changed, 52 insertions(+), 2 deletions(-) · alert 4 files changed, 5 insertions(+), 2 deletions(-)
- **리뷰**: 듀얼 1패스(고침 13 · 명세 수정 1 · 후보 3) + post-fix 재점검 1회(미해소 1 → d36ff93 에서 고침). 감사에서 종합의 세 항목(긴 줄 자르기 표시·유실 범위·2자 검색)이 결함 수정이 아니라 명세 완화라는 지적을 받아, 자르기는 명세대로 "자르지 않음"으로 바꾸고 나머지 둘은 사용자에게 물었다. 재점검 반영분은 다시 리뷰하지 않았다.
- **수정 중 실측이 잡은 것**: ①Spring 저수준 `XINFO` 가 중첩 응답에서 실패 — Lettuce 를 직접 부름 ②없는 스트림에 `ERR no such key` ③스키마가 없을 때 헬스의 최신 행 조회가 실패해 `unreachable` 로 보이던 것(재점검 지적, F4 테스트의 가짜가 늘 성공해 놓쳤다).

### 핵심 코드 (git 객체에서 복사)

**observe — 저장 뒤에만 확인한다. 실패하면 확인하지 않고 물러나며 그룹을 다시 확인한다(Redis 재시작 대비 — 초안 단계에서 테스트 워커가 고침)** (5461098 `src/main/kotlin/xyz/junproject/observe/collect/LogCollector.kt` 80–97행, 68–77행)
```kotlin
    private fun storeAndAcknowledge(records: List<StreamRecord>): Int {
        if (records.isEmpty()) return 0
        val entries = ArrayList<LogEntry>(records.size)
        var trimmed = 0
        for (record in records) {
            val id = StreamId.parse(record.id)
            if (id == null) { log.warn("observe:observe:skipped entry with unreadable id {}", record.id.take(40)); continue }
            // 미확인인 채로 스트림 상한에 밀려난 항목은 ID 만 오고 필드가 비어 있다 — 로그 줄이 아니므로 빈 행을 만들지 않고 확인만 한다
            if (record.level == null && record.line == null) { trimmed++; continue }
            entries += LogLineParser.parse(id, record.level, record.line)
        }
        if (trimmed > 0) log.warn("observe:observe:{} unacknowledged entries were already trimmed from the stream — lost", trimmed)
        sink.insertAll(entries)                       // 실패하면 예외 → 아래 확인을 하지 않는다
        source.acknowledge(records.map { it.id })     // 읽을 수 없는 ID 의 항목도 함께 확인한다(영원히 미확인으로 남지 않게)
        storedTotal += entries.size
        entries.maxByOrNull { it.id }?.let { lastStoredAt = it.id.at }
        return records.size
    }
```
```kotlin
    } catch (error: Exception) {
        // 저장 실패든 Redis 불통이든 확인하지 않고 물러난다 — 미확인분 재확인을 다음 바퀴에 다시 하게 한다.
        // 그룹도 다시 확인한다 — Redis 는 디스크에 저장하지 않아 재시작하면 스트림과 그룹이 함께 사라지는데,
        // 그룹을 다시 만들지 않으면 NOGROUP 만 되풀이하며 수집이 영영 멈춘다.
        lastUnacknowledgedCheck = null
        groupReady = false
        val reason = "${error.javaClass.simpleName}: ${error.message?.take(200)}"
        if (reason != lastFailure) log.error("observe:observe:collect failed — will retry: {}", reason)
        lastFailure = reason
        0
```
**리뷰 뒤 — 스키마 생성을 수집 바퀴의 한 단계로 두고, 헬스에 나가는 실패 사유는 예외 종류 이름만 남긴다** (d36ff93 같은 파일 52–74행. `storeAndAcknowledge` 는 `lastStoredAt` 갱신 한 줄이 빠진 것 말고는 같다 — 마지막 저장 시각은 DB 의 최신 행에서 읽게 바뀌었다)
```kotlin
    /** 한 바퀴. 처리한(저장하고 확인한) 항목 수를 돌려준다. 실패하면 예외 없이 0 을 돌려주고 이유를 남긴다. */
    fun runOnce(): Int {
        var step = "collect"
        return try {
            // 그룹을 먼저 — 그룹이 없으면 헬스의 미확인 건수 조회가 NOGROUP 으로 실패해 스키마 실패가 "Redis 불통"으로 가려진다
            if (!groupReady) { source.ensureGroup(); groupReady = true }
            // 스키마는 DB 에 처음 닿았을 때 만든다 — DB 가 늦게 떠도 이 바퀴가 실패로 남기고 다음 바퀴에 다시 시도한다
            if (!schemaReady) { step = "schema"; sink.createSchema(); schemaReady = true; step = "collect"; log.info("observe:observe:schema ready") }
            collect()
        } catch (error: Exception) {
            // 저장 실패든 Redis 불통이든 확인하지 않고 물러난다 — 미확인분 재확인을 다음 바퀴에 다시 하게 한다.
            // 그룹도 다시 확인한다 — Redis 는 디스크에 저장하지 않아 재시작하면 스트림과 그룹이 함께 사라지는데,
            // 그룹을 다시 만들지 않으면 NOGROUP 만 되풀이하며 수집이 영영 멈춘다.
            lastUnacknowledgedCheck = null
            groupReady = false
            val kind = error.javaClass.simpleName
            val detail = "$step $kind: ${error.message?.take(200)}"
            if (detail != lastFailureDetail) log.error("observe:observe:collect failed — will retry: {}", detail)
            lastFailureDetail = detail
            lastFailure = if (step == "schema") "schema $kind" else kind
            0
        }
    }
```
**observe — 이어 보기: 리뷰 전에는 기간 없이 커서만 넘길 수 있었다(쪽마다 "지금부터 1시간"이 다시 계산돼 오래된 끝이 조용히 빠짐)** (5461098 `src/main/kotlin/xyz/junproject/observe/api/LogController.kt` 49–52행, 69–70행)
```kotlin
    /**
     * 로그 조회 — 최신순. 다음 쪽은 응답의 `next_before` 를 `before` 로 넘긴다(없으면 끝).
     * 기간을 주지 않으면 최근 1시간.
     */
```
```kotlin
        val query = try {
            val (start, end) = range(from, to, Duration.ofHours(1), MAX_RANGE, now)
```
**리뷰 뒤 — 커서만 넘기면 422** (d36ff93 같은 파일 70–74행, 91–93행)
```kotlin
    /**
     * 로그 조회 — 최신순. 기간을 주지 않으면 최근 1시간.
     * 이어 보기: 다음 쪽은 응답의 `next_before` 를 `before` 로, **응답의 `from`·`to` 를 그대로 함께** 넘긴다(`next_before` 가 비면 끝).
     * 기간 없이 `before` 만 넘기면 422 — 쪽마다 "지금부터 1시간"을 다시 세면 창의 오래된 끝이 밀려 그 사이 로그가 조용히 빠진다.
     */
```
```kotlin
        val query = try {
            if (!before.isNullOrBlank() && from.isNullOrBlank() && to.isNullOrBlank()) throw Invalid("이어 보려면 응답의 from·to 를 함께 넘긴다")
            val (start, end) = range(from, to, Duration.ofHours(1), MAX_RANGE, now)
```
**observe — 헬스: 리뷰 전에는 첫 바퀴 전 `starting` 도 200 이라 한 번도 수집하지 못한 자리가 배포 게이트를 통과할 수 있었다** (5461098 `src/main/kotlin/xyz/junproject/observe/collect/CollectorHealth.kt` 25–40행, 49행)
```kotlin
    fun report(now: Instant): Report {
        val lastLoopAt = collector.lastLoopAt
        val failure = collector.lastFailure
        val pending = runCatching(unacknowledged)
        val database = runCatching(databaseCheck)
        val unreachable = listOfNotNull(
            pending.exceptionOrNull()?.let { "redis ${reason(it)}" },
            database.exceptionOrNull()?.let { "database ${reason(it)}" },
        )
        val status = when {
            unreachable.isNotEmpty() -> "unreachable"
            failure != null -> "failing"
            lastLoopAt != null && Duration.between(lastLoopAt, now) < stallAfter -> "ok"
            lastLoopAt == null && Duration.between(startedAt, now) < stallAfter -> "starting"
            else -> "stalled"
        }
```
```kotlin
        return Report(status == "ok" || status == "starting", body)
```
**리뷰·재점검 뒤 — 200 은 `ok` 하나, 표 없음(42P01)은 닿지 못함으로 보지 않는다** (d36ff93 같은 파일 38–53행, 67행, 70–71행, 80–82행)
```kotlin
    fun report(now: Instant): Report {
        val lastLoopAt = collector.lastLoopAt
        val failure = collector.lastFailure
        val pending = runCatching(unacknowledged)
        // 표가 없으면 DB 에는 닿았고 저장된 행이 없는 것과 같다 — 마지막 저장 시각은 비우고 판정은 수집 바퀴의 결과에 맡긴다
        val stored = runCatching(latestStoredAt).recoverCatching { if (isTableMissing(it)) null else throw it }
        val behind = runCatching(lag)
        val problems = listOfNotNull(pending.exceptionOrNull()?.let { "redis" to it }, stored.exceptionOrNull()?.let { "database" to it })
        logProblems(problems)
        val status = when {
            problems.isNotEmpty() -> "unreachable"
            failure != null -> "failing"
            lastLoopAt != null && Duration.between(lastLoopAt, now) < stallAfter -> "ok"
            lastLoopAt == null && Duration.between(startedAt, now) < stallAfter -> "starting"
            else -> "stalled"
        }
```
```kotlin
        return Report(status == "ok", body)
```
```kotlin
    private fun isTableMissing(error: Throwable) =
        generateSequence(error) { it.cause }.any { it is SQLException && it.sqlState == UNDEFINED_TABLE }
```
```kotlin
    companion object {
        private const val UNDEFINED_TABLE = "42P01"   // PostgreSQL: relation does not exist
    }
```
**observe — 8000자 상한 제거(명세 ② "원문 그대로")** (`git diff 5461098 d36ff93 -- src/main/kotlin/xyz/junproject/observe/log/LogEntry.kt` 의 두 hunk — d36ff93 31–50행)
```diff
@@ -31,10 +31,10 @@ data class LogEntry(
 /**
  * 발신 쪽 형식 `<요청ID>:<서비스>:<내용>` 한 줄을 나눈다(네 서비스의 로거가 이 형식으로 보낸다 — 발신 쪽은 바꾸지 않는다).
  * 나눌 수 없는 줄도 버리지 않는다: 서비스 `unknown`, 원문을 내용으로.
+ * 길이는 자르지 않는다 — 명세 ② "원문 그대로". 긴 오류의 뒷부분(원인 예외)이 찾고 싶은 부분인 경우가 많다.
  */
 object LogLineParser {
     const val UNKNOWN_SERVICE = "unknown"
-    const val MESSAGE_LIMIT = 8000
     private val shape = Regex("""^([A-Za-z0-9_.-]{1,80}):([a-z0-9-]{1,40}):(.*)$""", RegexOption.DOT_MATCHES_ALL)
     private val knownLevels = setOf("debug", "info", "warning", "error")
 
@@ -43,9 +43,9 @@ object LogLineParser {
         val match = shape.matchEntire(line)
         val level = (rawLevel ?: "").trim().lowercase().let { if (it in knownLevels) it else if (it == "warn") "warning" else "info" }
         return if (match != null) {
-            LogEntry(id, level, match.groupValues[2], match.groupValues[1], match.groupValues[3].take(MESSAGE_LIMIT))
+            LogEntry(id, level, match.groupValues[2], match.groupValues[1], match.groupValues[3])
         } else {
-            LogEntry(id, level, UNKNOWN_SERVICE, "", line.take(MESSAGE_LIMIT))
+            LogEntry(id, level, UNKNOWN_SERVICE, "", line)
         }
     }
 
```
**observe — 단위 테스트 설정을 `test` 하나에만 건다(`withType<Test>` 이면 engineTest 에서 엔진 테스트 0개가 초록) — 초안 단계에서 테스트 워커가 고쳤다** (5461098 `build.gradle.kts` 40–54행)
```kotlin
// 단위 테스트만 — Docker 빌드의 test 단계가 이것을 돈다(빌드 안에서는 DB 를 띄울 수 없다).
// withType 이 아니라 test 하나에만 건다 — withType 이면 engineTest 에도 excludeTags 가 붙어 engine 을 넣고 빼는 셈이 돼 아무것도 돌지 않는다.
tasks.named<Test>("test") {
	useJUnitPlatform { excludeTags("engine") }
}

// 실제 PostgreSQL·Redis 가 있어야 도는 테스트 — scripts/engine-test.sh 가 컨테이너를 띄우고 부른다
tasks.register<Test>("engineTest") {
	description = "실제 PostgreSQL·Redis 에 대고 도는 테스트"
	group = "verification"
	testClassesDirs = sourceSets["test"].output.classesDirs
	classpath = sourceSets["test"].runtimeClasspath
	useJUnitPlatform { includeTags("engine") }
	outputs.upToDateWhen { false }
}
```
**observe — 조회 풀은 값을 보고 계획한다(`force_custom_plan` — 초안 단계에서 테스트 워커가 넣음)** (5461098 `src/main/kotlin/xyz/junproject/observe/ObserveConfiguration.kt` 41–46행)
```kotlin
        val ingest = pool("observe-ingest", url, user, password, size = 2, statementTimeoutMs = 30_000)
        // 조회는 늘 값을 보고 계획한다 — 검색어(q)가 자리표시자라 같은 문장이 되풀이되면 PostgreSQL 이 값과 무관한 일반 계획으로
        // 바꿀 수 있는데, 그 계획으로는 흔한 말 검색이 75만 행에서 2초 걸렸다(값을 보고 세운 계획은 1ms). 계획 비용은 1ms 안팎.
        val query = pool("observe-query", url, user, password, size = 4, statementTimeoutMs = 10_000,
            extraInitSql = "; SET plan_cache_mode = force_custom_plan")
        return LogStore(JdbcTemplate(ingest), JdbcTemplate(query))
```
**리뷰 뒤 — 헬스 전용 풀(크기 1·짧은 대기)을 따로 둔다** (d36ff93 같은 파일 36–39행, 46–52행)
```kotlin
    /**
     * 수집·조회·헬스의 연결 풀을 나눈다 — 무거운 조회가 연결을 다 잡아도, 인증 없는 헬스 요청이 몰려도 수집은 밀리지 않는다.
     * 조회는 10초에서 끊는다. 헬스는 1개·짧은 대기 — 몰리면 헬스끼리만 기다리다 503 이 되고, DB 가 끊기면 몇 초 안에 503 이 된다.
     */
```
```kotlin
        val ingest = pool("observe-ingest", url, user, password, size = 2, statementTimeoutMs = 30_000)
        // 조회는 늘 값을 보고 계획한다 — 검색어(q)가 자리표시자라 같은 문장이 되풀이되면 PostgreSQL 이 값과 무관한 일반 계획으로
        // 바꿀 수 있는데, 그 계획으로는 흔한 말 검색이 75만 행에서 2초 걸렸다(값을 보고 세운 계획은 1ms). 계획 비용은 1ms 안팎.
        val query = pool("observe-query", url, user, password, size = 4, statementTimeoutMs = 10_000,
            extraInitSql = "; SET plan_cache_mode = force_custom_plan")
        val health = pool("observe-health", url, user, password, size = 1, statementTimeoutMs = 2_000, connectionTimeoutMs = 2_000, validationTimeoutMs = 1_000)
        return LogStore(JdbcTemplate(ingest), JdbcTemplate(query), JdbcTemplate(health))
```
**ci-cd — 배포 대상 고정 목록에 observe** (`git diff cf5d5b6 e2fd861 -- internal/master/master.go` 의 hunk — agent.go 61행도 같은 한 줄)
```diff
@@ -56,7 +56,7 @@ type Master struct {
 func New(logger *shared.Logger) (*Master, error) {
 	agents := map[string]string{}
 	// AGENT_URL_FRONT=http://<host>:15001 형식 — 서비스 allowlist는 이 고정 열거가 정본
-	for _, service := range []string{"front", "backend", "llm", "alert"} {
+	for _, service := range []string{"front", "backend", "llm", "alert", "observe"} {
 		if agentURL := os.Getenv("AGENT_URL_" + strings.ToUpper(service)); agentURL != "" {
 			agents[service] = agentURL
 		}
```
**alert — 감시 대상에 observe** (`git diff dca2850 482da3a -- src/main/resources/monitors.yml` 의 hunk)
```diff
@@ -10,3 +10,4 @@ monitors:
   - { name: deploy-agent-front,   url: "${MONITOR_DEPLOY_AGENT_FRONT_URL}/health" }
   - { name: deploy-agent-backend, url: "${MONITOR_DEPLOY_AGENT_BACKEND_URL}/health" }
   - { name: deploy-agent-llm,     url: "${MONITOR_DEPLOY_AGENT_LLM_URL}/health" }
+  - { name: observe,         url: "${MONITOR_OBSERVE_URL}/health" }
```

### 검증 결과 (서버 실행 시각은 UTC — 11-21 16:5x~19:0x KST)

| 구분 | 언제 | 결과 |
|------|------|------|
| 가정 2 실증(postgres:17, 75만 행 합성 데이터) | 11-21 착수 직후 | 드문 말 부분 일치 0.2ms(trigram, 0건) · 흔한 말 0.4ms · 서비스+하루+부분 일치 22ms · 요청ID 0.1ms · 30일 전체 시간 단위 통계 674ms(순차 훑기). 표+인덱스 185MB, trigram 29MB |
| 엔진 — 75만 행 검색 측정(워커 A) | 11-21 14:07 회수 | 3자 이상 검색어 최대 250ms. 2자이면서 드문 검색어는 전체 훑기 0.45~1.0초 — 사용자 확인 뒤 허용, 테스트 상한 3초 |
| 가정 1 실증(엔진) | 11-21 14:07 회수 | Redis 7.4 + Spring Boot 4.1.1 에서 그룹 읽기·ack·미확인분 재수신 동작, 수집기 둘 5000건 누락·중복 0 |
| 뮤테이션 | 11-21 14:07 회수 | 10종 모두 빨강(워커 A) |
| 단위 — observe | 14:1x · 16:14 · 16:30 | 38 → 54 → 57, skipped 0 · failures 0(메인 재실행, 워커 보고와 일치). `docker build --target test` 가 단위를 실제로 돌림 |
| 엔진 — observe(실제 PostgreSQL·Redis) | 14:2x · 16:14 · 16:4x | 21 → 27 → 28, skipped 0 · failures 0(메인 재실행) |
| 단위 — alert | 11-21 13:28 회수 | 75개 통과. `MonitorRoundTest` 느린 대상 테스트가 1회 실패 후 재실행 통과(300ms 예산에 기대는 시간 의존) |
| 단위 — ci-cd | 11-21 13:28 회수 | `go vet` + race 통과 |
| 컨테이너 기동(워커 D) | 11-21 16:14 회수 | 기동부터 헬스 200 까지 약 11초 · DB 정지 시 다음 헬스 요청에서 503 `unreachable` · DB 복귀 6.9초 뒤 회복 |
| 서버 실행 ① 최초 배치 | 07:58Z | 헬스 200 시점 `stored_since_start` 10011(스트림에 밀려 있던 것 전부), lag 0, 미확인 0. PostgreSQL 호스트 포트 없음 |
| 서버 실행 ④ 파이프라인 배포(두 자리 교대) | 08:33Z~08:34Z | CI 47.6초 → CD 7.6초, blue → green, 구 자리 3초 뒤 정리. 그 사이 스트림 32건 = DB 32건, DB 전체 10834행 = 서로 다른 ID 10834(중복 0), pending 0 · lag 0 |
| 알림 감시 추가 | 17:4x KST | 감시 대상 9개 모두 UP |
| 서버 실행 ② 요청ID 조회 | 10:04Z | 한 요청ID 로 front `/api/tree ok` · backend `doc ok README.md` · front `/api/doc ok` 세 줄이 묶여 나옴. level=error 조회·통계·커서 이어 보기·인증 없는 조회 401 확인 |
| 서버 실행 ③·⑤ 활성 자리 5분 정지 | 10:04:36Z~10:09:40Z | 정지 구간 포함 스트림 161건 = DB 161건(누락 0). 알림 서버가 10:05:44Z(정지 68초 뒤) `status 502` 로 DOWN, 10:09:49Z 복구(끊긴 시간 4분 4초) |

### 남은 것

- **엔진 테스트는 파이프라인에서 돌지 않는다**: 실제 DB 가 필요한 28개는 Docker 빌드의 test 단계에서 못 돈다(명세에 적은 한계). `scripts/engine-test.sh` 로 로컬에서만 돈다 — 파이프라인이 막는 것은 단위 57개뿐이다.
- **재점검 반영분(d36ff93) 미리뷰**: 1패스 규칙으로 다시 리뷰하지 않았고 단위·엔진 테스트와 뮤테이션으로만 확인했다.
- **DB 디스크 가득 미검증**: 반증 질문 "DB 디스크가 차면"은 테스트하지 않았다. 코드상으로는 저장 실패 → 미확인으로 남음 → 헬스 503 이다. 이 상태가 스트림이 버티는 시간(평소 약 9시간)보다 길면 밀려난 로그를 잃는다(명세 ② 전제).
- **최초 배치·postgres 는 CD 밖**: CD 가 `--no-deps` 라 postgres 가 죽어 있으면 배포가 헬스 단계에서 실패한다. postgres 재기동은 손으로 해야 한다.
- **리뷰 후보**: K1 스프링 컨텍스트를 띄우는 테스트 없음(실제 컨테이너 기동·수집·조회로만 확인) · K2 스트림 이름을 잘못 적으면 빈 스트림으로 200(NEXT 의 "로그가 오래 안 들어옴" 알림에서 다룸) · K3 엔진 스크립트가 root 로 `build/` 에 씀.
- **alert 의 시간 의존 테스트**: `MonitorRoundTest` 느린 대상 테스트가 300ms 예산에 기대어 1회 실패했다(알림 서버 작업 때 쓴 테스트). 고치지 않았다.
- **로그가 드러낸 것(범위 밖 — NEXT 로)**: 최근 24시간 front error 12건이 `backend unreachable /api/tree: TimeoutError`·`fetch failed` 였다(07:40Z·08:17Z·08:55Z …). front(`.9`) → backend(`.158`) 호출이 간헐적으로 실패한다. 같은 시간대 엣지→집 끊김과의 관계는 확인하지 않았다.
- **비밀값 노출 1건(교체 완료)**: 확인용 출력이 잘리며 `OBSERVE_SECRET` 뒷부분 33자가 화면에 나왔다. 즉시 새 값으로 바꾸고 새 값 200 · 옛 값 401 을 확인했다.
- **이슈 아카이브 보류**: 명세 범위에 study-note 쓰기가 없어 사용자 범위 확인이 필요하다. 후보 5건은 NEXT 에 올렸다.
