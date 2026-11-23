# CS 이슈 후보 — admin-skeleton (어드민 뼈대)

- 기준: `~/.claude/playbooks/issue-archive.md` §1 — log 에서 **실제로 발생한 문제 + 원인 + 해결**, 프로젝트 밖 사람에게 같은 문장으로 설명되는 기술 원리만. 도메인 규칙 · 문서 표기 · 리뷰 절차는 뺐다.
- 매칭은 `study-note/issue/README.md` 인덱스(카드 187개)의 한 줄 요약으로만 했다. 카드 본문은 질문 파일 몇 개의 첫머리만 봤다 — ⓑ(같은 해결) / ⓒ(방안 비교 덧붙임) 판정은 §2 대로 카드 본문을 읽고 해야 한다. 아래 "판정 예상"은 짐작이다.
- "발생" 칸: **실행 재현** = 테스트 · 미리보기 · 서버 · 리뷰어 실행에서 실제로 드러남 / **코드로만** = 리뷰가 코드를 읽고 지적, 재현 행 없음(§1 의 "실제로 발생"에 못 미칠 수 있어 따로 표시).

## 원 식별자 (카드에 나오면 안 되는 이름 — §4 노출 스캔의 입력)

- 저장소 · 도메인: `study-note-deploy-system-admin` · `-observe` · `-ci-cd` · `-alert` · `deploy-study-note` · `study-note` · `junproject.xyz` · `admin.junproject.xyz` · GitHub 소유자 이름(`junhyeong9812`) · `project-deploy-data`
- 서버 · 경로: `.9` · `.158` · `.164` · 엣지 설정 파일 이름 · `deploy/active/` · `edge-allow.conf` · `docs/secrets.md`
- 클래스 · 함수 · 파일: `AuthAttemptEngineTest` · `AuthAttemptStore` · `AuthAttemptController` · `AuthAttemptPolicy` · `EngineSupport` · `readConsistently` · `reachesShallowBoundary` · `resolveCommit` · `gitEnvironment` · `loadCommits` · `patchLines` · `diff-lines.ts` · `deploy-git-client.ts` · `login-flow.ts` · `require-session.ts` · `middleware.ts` · `git_read.go` · `git_relay.go`
- 설정 키 · 헤더 · 오류 코드: `ADMIN_ORIGIN` · `OBSERVE_URL` · `OBSERVE_SECRET` · `DEPLOY_SECRET` · `SESSION_SECRET` · `PUBLIC_PORT` · `MONITOR_ADMIN_URL` · `X-Observe-Secret` · `X-Deploy-Secret` · `X-Deploy-Slot` · `repository_changing` · `parent_unavailable` · `not_in_history` · `history_changing` · `agent_unauthorized` · 설정 접두 `observe.auth.*`
- 관리자 계정 ID(log 11-23 16:4x 행) — 카드 · 커밋 어디에도 넣지 않는다.

## 후보 (강한 것부터)

### 1. 얕은 저장소에서 "부모 없음 · 조상 아님"은 "모름"이다
- **한 문장 원리**: 얕은 clone 은 경계 커밋의 부모를 갖지 않으므로, 그 경계에서 끊긴 이력에 대한 diff · 조상 판정은 거짓 답(전부 추가된 파일 · "조상 아님")을 낸다 — 경계에 닿았는지 먼저 보고 "알 수 없음"을 따로 낸다.
- **증상**: ①이력의 가장 오래된 커밋의 `show` 가 파일 전체를 "추가"로 냄(31줄 추가 표시) ②배포마다 `fetch --depth=50` 을 하는 저장소에서 직전 배포 커밋 A 의 객체는 남아 있는데 B→A 이력이 끊겨 `merge-base --is-ancestor` 가 "조상 아님" → 응답이 200 `not_ancestor` · 빈 목록(리뷰 G1).
- **원인**: 얕은 경계 커밋은 부모 객체가 로컬에 없다. 조상 판정은 로컬 그래프만 본다.
- **해결**: 경계 목록(`shallow` 파일)에 든 커밋의 diff 요청은 "부모 없음" 갈래(404)로 답하고 외부 링크로 넘긴다. 조상 판정은 4단계 — 조상이면 ancestor / B 의 조상 순회가 경계에 닿지 않으면 not_ancestor / B 가 A 의 조상이면(확실한 되돌림) not_ancestor / 그 밖은 unknown.
- **발생**: 실행 재현 — 가정 실증(임시 저장소)과 메인이 리뷰한 SHA 를 빌드해 임시 저장소(c10→c20, depth 5)로 200 `not_ancestor` 재현.
- **log 근거**: 11-23 13:1x(실증 · 명세 §12.5) · 14:0x(G1 재현) · ledger G1.
- **기존 카드**: `cross-cutting/infra/git-pitfalls/`(배포 · CI 의 git 함정 — 본문 검색에 shallow · depth 없음) → ⓒ 또는 새 카드. 인접: `cross-cutting/data/absent-vs-empty/`("없음"과 "모름"을 뭉갬) · `cross-cutting/distributed/three-state-rpc-outcome/`(3상태).

### 2. 다른 프로세스가 바꾸는 저장소를 여러 명령으로 읽을 때 — 앞뒤 버전 비교로 일관성 확인
- **한 문장 원리**: 잠금 없이 여러 번의 읽기로 한 답을 만들면 그 사이 쓰기가 섞인다 — 읽기 앞뒤로 버전 표지를 비교해 같을 때만 답하고, 다르면 다시, 계속 다르면 "바뀌는 중"으로 답한다(낙관적 읽기 · seqlock 꼴).
- **증상**: 조회 도중 배포의 fetch 가 얕은 경계를 바꾸면 부모 없는 diff(전부 added) · 틀린 relation 이 200 으로 나감(리뷰 H1 — 테스트 워커가 리뷰한 SHA 에서 빨강 확인).
- **원인**: 경계 판정에 쓴 목록과 git 명령들이 본 이력이 서로 다른 시점의 것. 배포 쪽 잠금을 잡으면 배포를 막는다(명세가 금지).
- **해결**: 첫 처리 방향(명령마다 방어)이 모자라다는 감사 → 같은 결함을 두 번째 고치는 것이라 방식을 바꿈: 경계 목록을 git 명령들 앞뒤로 읽어 같으면 그 결과, 다르면 한 번 다시, 또 다르면 503. 기한은 재시도 포함 조회 하나 전체. 워커 스모크: 배포 흉내 300바퀴와 동시 조회 — 틀린 diff 0건.
- **발생**: 실행 재현(테스트).
- **log 근거**: 11-23 14:4x · ledger H1 · 명세 §12.9.
- **기존 카드**: 인덱스에 같은 원리 카드 없어 보임 → ⓐ 새 카드 후보(`cross-cutting/concurrency/`). 인접: `cross-cutting/security/verify-what-you-use/`(재열람 TOCTOU) · `cross-cutting/concurrency/snapshot-stream-cursor/`.

### 3. 프레임워크가 상대 Location 을 다시 해석 · 요청 Host 로 만든 이동 주소
- **한 문장 원리**: 리다이렉트 주소를 요청의 Host 나 서버 자신의 호스트 이름에서 만들면 내부 주소가 바깥으로 새고, 상대 주소는 계층(프레임워크 어댑터 · 프록시)마다 받아들이는지가 다르다 — 설정된 공개 출처를 기준으로 만들고 프록시에서 경로만 남긴다.
- **증상**: ①세션 없는 화면의 `Location` 이 내부 호스트의 절대 주소(리뷰어 실행 — 리뷰 B1) ②고치려고 상대 `Location: /login` 을 내자 단위 테스트 452 는 초록인데 실제 서버가 500 — Next 15.5.29 의 middleware 어댑터가 `Location` 을 기준 주소 없이 다시 해석(`ERR_INVALID_URL`).
- **원인**: ①`new URL(경로, request.nextUrl)` — 요청 주소 기준 ②어댑터가 `new NextURL(location)` 으로 재해석(코드 주석에 adapter.js 343행). 단위 테스트는 어댑터를 거치지 않는다.
- **해결**: 설정값(공개 출처) 기준 절대 주소 + nginx `proxy_redirect` · `absolute_redirect off` 로 바깥에는 `/login`. 테스트는 요청 주소를 내부 주소로 바꿔 "요청 호스트를 베끼면 빨강"이 되게(전에는 둘이 같아 베껴도 통과). 설정을 해석하지 못하면 요청 주소로 대신하지 않고 503.
- **발생**: 실행 재현(리뷰어 실행 · 워커 실측 · 메인 컨테이너 확인 `Host: evil.example.test` → 설정 출처의 `/login`).
- **log 근거**: 11-22 11:1x(B1) · 13:3x · 13:4x · 13:5x · 14:0x.
- **기존 카드**: `cross-cutting/network/proxy-passthrough/`(본문에 redirect · Location 언급, "prefix 를 앱이 링크에 반영") → ⓒ 후보. 단위 테스트가 어댑터를 거치지 않은 부분은 `cross-cutting/testing/verification-environment-parity/`.

### 4. 프록시의 본문 읽기 시간 제한은 "간격"이지 "전체 기한"이 아니다
- **한 문장 원리**: nginx `client_body_timeout` 은 두 번의 읽기 사이 간격이라 조금씩 꾸준히 보내는 본문은 끝없이 통과하고, 프록시가 본문을 모아 넘기면 뒤의 앱 기한은 의미가 없다 — 흘려보내기(`proxy_request_buffering off`)로 앱이 전체 기한을 직접 건다.
- **증상**: 2초 간격으로 10초에 걸쳐 보낸 본문이 nginx 를 거쳐 200(리뷰어 실측 `elapsed=10.0s 200`). 앱의 3초 기한은 nginx 뒤에서 무효.
- **원인**: 간격 타이머 + 버퍼링(앱은 다 모인 본문을 한 번에 받는다).
- **해결**: 로그인 경로만 `proxy_request_buffering off`, 앱이 4KB 상한 · 전체 3초(넘으면 400, 속도 제한에도 셈), nginx 는 8KB 상한(413)과 간격만. 같은 시험이 400, 3420ms. 처음 메인이 "nginx 가 먼저 끊는 요청은 기록 밖"으로 수용하려던 것을 감사가 조용한 완화로 지적.
- **발생**: 실행 재현.
- **log 근거**: 11-22 13:3x(워커 — nginx 가 3초에 끊음, 기록 밖) · 14:4x(리뷰어 실측 · 감사) · 16:0x(수정 뒤 3420ms) · ledger C2.
- **기존 카드**: `cross-cutting/security/local-endpoint-hardening/`(본문에 slowloris · 읽기 타임아웃) → ⓒ 후보. 인접: `cross-cutting/reliability/resource-bounding-last-defense/`.

### 5. 앞단 프록시만 믿는 헤더 — 그런데 원본 포트가 직접 닿는다
- **한 문장 원리**: 클라이언트 IP 헤더는 신뢰하는 앞단을 거친 연결에서만 믿을 수 있으므로, 원본 포트가 인터넷에서 직접 닿으면 원본 쪽에서 연결 출처를 허용 목록으로 거르고 헤더를 다시 써야 한다.
- **증상**: 가정 2 "집 쪽 포트는 엣지에서만 닿는다"가 틀림 — 인터넷에서 직접 닿는다(엣지 설정 확인). 그대로면 직접 온 연결이 `X-Real-IP` 를 속여 IP 별 속도 제한을 피할 수 있다.
- **원인**: 공유기 포트포워딩은 엣지 전용이 아니다.
- **해결**: 어드민 nginx 가 엣지 주소와 사설 대역만 받고 나머지는 444, 엣지 연결이면 엣지가 넣은 헤더를, 사설이면 실제 접속 주소를 `X-Real-IP` 로 다시 써서 앱은 한 헤더만 읽는다. K1 실측: 바깥에서 보낸 시도의 기록 주소 = 요청자 공인 주소, 클라이언트가 넣은 가짜 헤더는 기록에 없음. **한계**: 제3의 바깥 기계에서의 직접 연결 시험은 못 함(추론).
- **발생**: 가정 실증에서 드러남(공격 재현은 아님).
- **log 근거**: 11-22 06:0x · 07:5x(nginx 실험) · 11-23 20:5x(K1).
- **기존 카드**: `cross-cutting/network/proxy-passthrough/`(방안 "전달받은 헤더는 신뢰 홉 기준으로만") → ⓑ 또는 ⓒ(원본 쪽 연결 출처 허용 목록이 새 방안이면). 인접: `cross-cutting/infra/firewall-and-network-policy-layers/`.

### 6. 설정이 틀린 채로 뜨면 헬스가 거짓말을 한다 — 시작 때 형식까지 검사해 종료
- **한 문장 원리**: 필수 설정이 비었거나 형식이 틀린 상태를 "뜨되 기능만 거절"로 처리하면 헬스가 통과해 고장 난 인스턴스가 활성이 된다 — 시작 때 검사해 0 이 아닌 코드로 끝내고 헬스도 설정이 유효할 때만 200.
- **증상**: ①설정이 비어도 앱은 뜨고 헬스 200 · 로그인만 거절(사용자 지적) ②리뷰어 실측: 틀린 `OBSERVE_URL` 로 health 200 · 로그인이 영구히 임시 제한, `ADMIN_ORIGIN` 끝 `/` 로 모든 로그인 403(Origin 글자 비교).
- **원인**: 빈 값만 검사, 형식(출처 꼴 · scheme · 해시를 라이브러리가 읽을 수 있는지)은 안 봄. 헬스가 설정 유효성을 반영하지 않음.
- **해결**: 시작 검사 → exit 78 + 키 이름 1줄(값 없음), 헬스 503. `new URL(값).origin === 값` · http(s) 해석 · 해시는 검증 라이브러리로 1회 읽어 봄. 실측: 필수 키를 빼면 2초에 exit 78, 그 사이 포트 응답 0건(5ms 탐침 300회) · `restart: unless-stopped` 아래 12초에 5회 재시작 · 깨진 해시 / 끝 `/` / scheme 없음 각각 exit 78.
- **발생**: 실행 재현.
- **log 근거**: 11-22 11:4x · 13:3x · 14:4x · 16:0x · ledger B10 · C1.
- **기존 카드**: `cross-cutting/reliability/fail-closed-guard/`("설정 누락 … 통과로 삼키면") → ⓑ/ⓒ 후보. 인접: `cross-cutting/reliability/silent-failure-vs-artifact/` · `cross-cutting/testing/green-masking/`.

### 7. 두 겹 방어는 테스트에서 서로를 가린다 · 입력이 맞는 구현과 틀린 구현을 가르지 못한다
- **한 문장 원리**: 같은 동작을 두 곳이 지키면 한 곳을 지워도 다른 곳이 막아 초록이 유지되고, 기대값이 틀린 구현에서도 같게 나오는 입력은 아무것도 지키지 않는다 — 겹마다 따로 부르는 테스트와 틀린 구현이 다른 답을 내는 입력이 필요하다(뮤테이션으로 확인).
- **증상**: ①middleware 를 열어도, 세션 검사를 빼도 vitest 206 그대로 초록 ②Location 단언에서 요청 주소 = 설정값이라 요청 호스트를 베껴도 통과 ③숫자뿐인 SHA 를 대문자로 바꿔 "대소문자 무관" 입력으로 씀(값이 그대로) ④4MB 상한 테스트가 앞선 필수 칸 검사에 먼저 거절돼 공허해짐(J1) ⑤가드 한 곳만 지우면 안 잡히고 둘 다 지워야 잡히는 변형 2종.
- **원인**: 테스트가 끝단 결과만 보고, 입력이 판별력을 갖지 않음.
- **해결**: middleware 직접 호출 + 보호 경로 전수 × 잘못된 쿠키, 화면 · Route Handler 가 세션 함수를 부르는지 고정 → middleware 통과 +57 빨강 · 홈 +3 · 로그아웃 +6. 요청 주소를 내부 주소로 → 38 빨강. 입력을 글자 섞인 SHA 로. J1 은 필수 칸을 갖춘 응답으로 다시 → 상한을 64MB 로 바꾸는 변형이 깸.
- **발생**: 실행 재현(뮤테이션).
- **log 근거**: 11-22 07:5x · 09:1x(A3) · 10:0x · 13:5x · 16:0x · 11-23 15:4x · ledger A3 · J1 · J2.
- **기존 카드**: `cross-cutting/testing/green-masking/`(질문 1 이 바로 "뮤테이션으로 테스트의 이빨 확인", "커버리지 상한은 픽스처의 표현력") → ⓑ 가능성 큼, 두 겹 방어 사례가 없으면 ⓒ.

### 8. Kotlin 스코프 함수 안에서 같은 이름이 수신자 쪽을 가리킨다
- **한 문장 원리**: `apply` 블록 안의 이름은 바깥 클래스보다 수신자의 멤버를 먼저 찾으므로, 수신자에 같은 이름의 프로퍼티가 있으면 문자열 템플릿이 조용히 그쪽(null)을 읽는다 — `this@바깥클래스` 로 한정한다.
- **증상**: 엔진 테스트 23건 전부 준비 단계에서 실패.
- **원인**: `HikariConfig().apply { jdbcUrl = … + "?currentSchema=$schema" }` 의 `$schema` 가 테스트 클래스의 칸이 아니라 `HikariConfig.schema`(null).
- **해결**: `${this@<테스트클래스>.schema}`. 같은 종류의 이름 가림은 다른 곳에 없음 확인. 구현 워커가 발견하고(테스트를 고치지 않고 보고) 테스트 워커가 한 줄 수정.
- **발생**: 실행 재현.
- **log 근거**: 11-22 08:1x · 08:3x · 커밋 `8c1ff88`.
- **기존 카드**: `kotlin/language-semantics-traps/`(Java 직관이 틀리는 Kotlin 규칙 — 질문에 스코프 함수 항목은 안 보임) → ⓒ 또는 그 카드에 사례 추가. 인접: `cross-cutting/testing/test-tool-default-semantics/`("중첩 클래스 섀도잉").

### 9. 자식 프로세스는 부모의 환경 · 설정 · 지역 설정을 물려받는다 — 판정은 종료 코드로
- **한 문장 원리**: 서비스가 띄운 git 은 부모의 `GIT_*` 환경 변수 · 사용자 전역 설정 · 지역 설정(오류 글자의 언어)을 그대로 타므로, 결과를 글자로 파싱하거나 개발자 환경에서 테스트하면 환경마다 다르게 동작한다.
- **증상**: ①가정 실증에서 git 오류 글자가 한국어로 나옴 ②테스트 대상 git 이 개발자 전역 git 설정을 읽음(리뷰 G7) ③`diff.submodule=log` 설정이면 서브모듈 줄이 앞 파일 patch 에 섞임(H6, 코드로만).
- **원인**: 환경 상속 · 전역 설정 · 설정에 따라 출력 꼴이 바뀜.
- **해결**: 자식 환경에서 `GIT_*` · `LC_ALL` 제거 후 `LC_ALL=C` · `GIT_OPTIONAL_LOCKS=0` · `GIT_NO_LAZY_FETCH=1` · `GIT_NO_REPLACE_OBJECTS=1` · `GIT_TERMINAL_PROMPT=0` 고정, 판정은 종료 코드로만, `--submodule=short` 등 플래그 고정, 테스트는 HOME 을 임시 디렉터리로.
- **발생**: ①실행 재현 ②코드로만(지적 뒤 테스트 추가) ③코드로만.
- **log 근거**: 11-23 13:1x(실증) · 14:0x(G7) · 14:4x(H6) · 명세 §12.5 · §12.7.
- **기존 카드**: `cross-cutting/os/execution-context-inheritance/`(자식이 env 를 물려받음) → ⓒ 후보. 인접: `cross-cutting/infra/git-pitfalls/` · `cross-cutting/testing/test-isolation-and-determinism/`.

### 10. 기한으로 자식을 죽여도 파이프를 쥔 손자가 남으면 Wait 가 끝나지 않는다
- **한 문장 원리**: 컨텍스트 기한이 자식 프로세스만 죽이면 출력 파이프를 물려받은 손자가 살아 있는 동안 파이프가 닫히지 않아 기다림이 기한을 넘긴다 — 파이프 대기에 상한(Go `cmd.WaitDelay`)을 둔다.
- **증상**: 기한 3초인데 손자 프로세스가 남으면 8.0초(테스트 워커가 새 테스트로 드러냄).
- **원인**: `exec.CommandContext` 는 직접 자식만 죽이고, `Wait` 는 stdout 파이프의 EOF 를 기다린다.
- **해결**: `WaitDelay` 로 정리 대기 0.5초 — agent 기한 3초 + 정리 대기 < master 중계 4초가 되게(기한의 합을 테스트로 고정).
- **발생**: 실행 재현.
- **log 근거**: 11-23 14:4x · ledger H3 · 명세 §12.9 "기한의 합".
- **기존 카드**: `cross-cutting/os/process-group-and-tree-termination/`(부모만 죽이면 손자가 남음) · `cross-cutting/os/subprocess-lifecycle-and-pipes/` → ⓑ/ⓒ 후보(Go `WaitDelay` 가 새 방안이면 ⓒ).

### 11. 응답 크기 상한은 실제 직렬화 길이로 — 상한 없는 칸 하나가 전체 상한을 무너뜨린다
- **한 문장 원리**: 칸별 상한만 두고 전체를 근사로 재면 상한이 없는 칸(작성자 이름 등)이나 직렬화 오버헤드로 최종 응답이 상한을 넘는다 — 최종 바이트를 실제로 재고, 자를 때는 레코드 경계에서 표식과 함께 자른다.
- **증상**: 커밋 목록 응답 4,930,600 바이트(G4 — 메인 재현) · patch 하나가 2MB 를 넘으면 파일 목록 전체가 사라짐(G5 — 3개 중 1개만) · 작성자 이름으로 상세 응답 2,400,220 바이트(J3 — 테스트 워커 빨강).
- **원인**: 목록 응답에 최종 상한 없음 · 근사 계산(H5) · `author_name` 상한 없음.
- **해결**: 두 응답 모두 봉투 포함 실제 직렬화 길이로 2MB 확인, 뒤 레코드부터 빼고 `truncated`, 파일 목록은 patch 와 따로 지킴, 이름 200바이트(글자 경계), 다 줄여도 넘으면 오류.
- **발생**: 실행 재현.
- **log 근거**: 11-23 14:0x · 14:4x · 15:1x · 15:3x · ledger G4 · G5 · H5 · J3.
- **기존 카드**: `cross-cutting/reliability/silent-truncation-marker/` · `cross-cutting/data/byte-stream-framing/`(상한 절단도 프레임 경계에서) · `cross-cutting/reliability/resource-bounding-last-defense/` → ⓑ/ⓒ 후보.

### 12. 끝의 줄바꿈 하나를 줄로 센다 — `split("\n")` 의 경계
- **한 문장 원리**: `\n` 으로 끝나는 텍스트를 `split("\n")` 하면 마지막에 빈 조각이 하나 생겨 줄 수가 하나 많다 — 줄 나누기 규칙을 한 함수로 모으고 모든 소비처(상한 판정 · 전체 줄 수 · 화면)가 같이 쓴다.
- **증상**: 37줄 추가 파일의 줄 수가 39 · 500줄 patch 에 "더 있음"(실제 master · agent 응답의 patch 넷 모두 줄바꿈으로 끝남). 테스트의 가짜 master 가 줄바꿈 없는 patch 를 줘서 못 잡았다.
- **원인**: 소비처마다 `split("\n")` 을 따로 씀 + 가짜 응답이 실제 꼴과 다름.
- **해결**: `patchLines`(끝 줄바꿈 하나는 줄이 아님) 하나로 모으고, 가짜 master 를 실제 꼴로. 미리보기에서 README diff 13줄 = 화면 표 13줄.
- **발생**: 실행 재현(메인 — 실제 응답).
- **log 근거**: 11-23 16:0x · ledger K4.
- **기존 카드**: `cross-cutting/data/boundary-arithmetic/`(경계에서만 터지는 산술) · `typescript/next/single-source-of-truth-routing/`(같은 계산을 두 곳에서) → ⓑ/ⓒ 후보. 가짜 꼴 부분은 `cross-cutting/testing/verification-environment-parity/`.

### 13. 재시도의 전체 기한 · 시간 초과는 재시도하지 않는다
- **한 문장 원리**: 호출마다 기한을 주고 재시도하면 사용자가 기다리는 시간이 기한 × 횟수가 되고, 시간 초과는 "결과 모름"이라 같은 멱등 키로 나중에 확인하는 편이 맞다 — 전체 기한 하나 안에서만 재시도한다.
- **증상**: 느린 관측 서버에서 로그인 10.06초(A7) · 재시도에 전체 기한 없이 9.87초(B2) — 둘 다 리뷰어 실행.
- **원인**: 5초 × (첫 호출 + 재시도).
- **해결**: 시간 초과는 재시도 없이 바로 임시 제한(사용자 결정) + 같은 `attempt_id` 로 대기열 → 복귀 뒤 관측 서버가 이미 기록했으면 처음 판정이 돌아옴. 연결 실패 · 비 2xx 만 남은 시간 안에서 1회 재시도. 실측 5078ms · 5071ms.
- **발생**: 실행 재현.
- **log 근거**: 11-22 07:5x(남은 한계) · 09:1x · 09:2x · 10:4x · 13:3x · ledger A7 · B2.
- **기존 카드**: `cross-cutting/distributed/three-state-rpc-outcome/`(타임아웃은 "모름") · `cross-cutting/reliability/retry-policy-design/` · `cross-cutting/reliability/idempotent-retry-design/` → ⓑ/ⓒ 후보.

### 14. 장애 중 내린 판정을 나중에 재전송할 때는 입력이 아니라 판정을 보낸다
- **한 문장 원리**: 오프라인 동안 대체 규칙으로 내린 결정을 나중에 원본 저장소로 재전송할 때 입력(자격이 맞았나)만 보내면 원본이 다른 규칙으로 다시 매겨 실제와 다른 기록이 남는다 — 실제로 내린 결과를 함께 보내고 원본은 그대로 기록한다.
- **증상**: 장애 중 임시 제한으로 거절(423)한 시도가 복귀 뒤 `success` 로 기록(`credential_ok:true, replayed:true` 전송 — 리뷰어 실행).
- **원인**: 대기열 항목에 판정이 없고, 관측 서버가 재전송을 자격으로 다시 매김.
- **해결**: 재전송에 `outcome` 필수(없으면 422), 관측 서버는 그대로 기록 · 잠금 계산에 넣지 않음. 서버 실측: 38초 pause 동안의 failure · success 두 건이 `replayed:true` 로 보낸 결과 그대로.
- **발생**: 실행 재현.
- **log 근거**: 11-22 09:1x · 09:2x · 10:2x · 10:4x · 11-23 22:4x · ledger A1.
- **기존 카드**: `cross-cutting/data/append-only-over-snapshot/` · `cross-cutting/reliability/idempotent-retry-design/` → 같은 원리인지 본문 확인 필요(ⓐ 가능성도 있음).

### 15. 재전송 대기열의 머리 막힘 — 영구 실패만 버린다
- **한 문장 원리**: 순서대로 재전송하는 대기열에서 다시 보내도 같은 실패(422)를 받는 항목을 남겨 두면 뒤의 항목이 영영 못 나간다 — 영구 실패만 버리고 건수를 남기며, 일시 실패(401 · 429 · 5xx · 시간 초과)는 남긴다.
- **증상**: `queue_size=2`(리뷰어 실행, 가정된 422).
- **원인**: 실패 분류 없이 전부 남김.
- **해결**: 422 만 버리고 `queue_discarded` 로그. 함께: 대기열이 다음 로그인 전까지 재전송하지 않던 것(C4) → 30초 주기 · 한 번에 하나.
- **발생**: 실행 재현(가정한 422 로).
- **log 근거**: 11-22 11:1x · ledger B9 · C4.
- **기존 카드**: `cross-cutting/reliability/retry-policy-design/`(영구 실패 · poison 메시지) → ⓑ 가능성 큼. 인접: `cross-cutting/concurrency/event-loop-head-of-line-blocking/`.

### 16. 프레임워크의 본문 해석이 인증보다 먼저 돈다
- **한 문장 원리**: 핸들러 인자로 본문을 받게 하면 프레임워크가 핸들러(그 안의 인증 검사)보다 먼저 본문을 해석해, 인증 없는 깨진 요청도 프레임워크의 400 · 415 를 받는다 — 인증을 먼저 하려면 원문을 직접 읽는다.
- **증상**: 관측 서버가 깨진 JSON 에 Spring 기본 400(해석할 수 없는 본문 11가지 × 두 POST 경로 — 테스트가 지금 구현에서 400 을 확인).
- **원인**: `@RequestBody` 바인딩이 핸들러 진입 전에 일어남.
- **해결**: 두 경로가 원문을 직접 읽음(비밀값 먼저 → Content-Type · 16KiB · JSON 꼴 → 422). 전역 예외 처리는 다른 경로에 번질 수 있어 고르지 않음. 서버 실측: 깨진 본문도 비밀값 없이 401.
- **발생**: 실행 재현(테스트).
- **log 근거**: 11-22 11:1x(B7) · 12:0x · 13:0x · 11-23 16:4x.
- **기존 카드**: `python/fastapi/response-normalization-framework-boundary/`(프레임워크가 핸들러 밖에서 만드는 응답이 계약의 구멍) → 같은 원리 · 다른 프레임워크 → ⓒ 후보. 인접: `cross-cutting/security/authorization-gate-placement/`(부작용 이전에 판정).

## 약한 후보 (실행 재현이 없거나 정보가 적음 — 쓸지 판단 필요)

| # | 원리(한 문장) | 증상 · 원인 · 해결 | 발생 | log 근거 | 기존 카드(인덱스 기준) |
|---|---|---|---|---|---|
| W1 | 잠금 판정을 "조회 뒤 기록" 두 호출로 나누면 동시 실패가 횟수를 겹친다 — 상태 행 `SELECT … FOR UPDATE` 한 트랜잭션 | 설계 선검증이 지적 → 처음부터 한 트랜잭션으로 구현. 뮤테이션(`FOR UPDATE` 제거) → 동시 사례 3 빨강. 운영에서 발생한 적은 없음 | 설계 단계 · 뮤테이션 | 11-22 06:1x · 08:1x | `cross-cutting/concurrency/critical-section-design/`(check-then-act 금지) → ⓑ 가능성 큼 |
| W2 | 속도 제한 표가 가득 차면 활성 항목을 지우는 축출은 제한 우회가 된다 — 활성은 남기고 새 키를 거절(닫힌 쪽) | 표 포화 시 제한 중인 IP 가 지워짐 → 활성 보존 · 새 IP 429 · 건수 로그 | 코드로만(B4) | 11-22 11:1x | `cross-cutting/reliability/fail-closed-guard/` · `cross-cutting/reliability/resource-bounding-last-defense/` |
| W3 | 없는 ID 와 틀린 비밀번호의 검증 시간이 같아야 한다 — 더미 해시의 비용 매개변수가 실제와 다르면 시간이 갈린다 | 비용 불일치면 로그인 전부 거절(감사로 강화) | 코드로만(A9) | 11-22 09:1x · 09:2x | 인덱스에 타이밍 부채널 카드 없어 보임 → ⓐ 후보 |
| W4 | 거절마다 로그 1줄은 공유 로그 스트림을 밀어낸다 — 이유별 창 집계 | 이유별 60초 1줄, 창 끝 · 종료 때 남은 건수 | 코드로만(C6) | 11-22 14:4x | `cross-cutting/reliability/resource-bounding-last-defense/` |
| W5 | 바인드 마운트의 원본 디렉터리가 없으면 도커가 root 소유 빈 디렉터리를 만든다 — clone 을 먼저 | `.158` 에 root 소유 빈 폴더가 생김(예상대로). 리뷰에서는 기존 관례로 기각(G10 · H10) | 서버에서 관측 | 11-23 19:5x | `cross-cutting/infra/effective-uid-file-access/` · `cross-cutting/infra/compose-variable-resolution-timing/` |
| W6 | git 의 patch 출력은 형 바뀜(파일↔심볼릭 링크)을 두 조각으로 낸다 — 순서로 파일과 짝짓지 말고 `-z` 로 경로를 읽는다 | 형 바뀜 커밋 상세 500(G2 — 메인 재현), 짝을 확정 못 하면 patch 비움 | 실행 재현 | 11-23 14:0x · ledger G2 | `cross-cutting/data/ad-hoc-parsing-of-structured-text/` · `cross-cutting/infra/git-pitfalls/` — 후보 9 · 1 과 한 카드로 묶을지 판단 |
| W7 | 하네스 훅이 명령 문자열 속 낱말을 발행 본문으로 오인해 차단 | 스캔 명령 속 낱말 → 1회 차단 → 명령 분리. log 는 한 줄뿐 | 실행(1회) | 11-23 16:2x | `cross-cutting/security/regex-is-not-a-shell-parser/`(문자열 패턴 검사의 오탐) → ⓑ 가능성 |
| W8 | 테스트 러너 버전의 런타임 하한 | vitest 4 가 호스트 기본 node 18 에서 안 뜸 → node 20 | 실행 | 11-22 07:0x | `cross-cutting/infra/dependency-and-toolchain-compat/` → ⓑ 가능성 큼 |

## 뺀 것 (§1 제외 기준)

- 도메인 · 계약 결정: 잠금 수치 · 세션 12시간 · 거절 이유 낱말 · 화면 구성 · 커밋 순서 · `relation` 낱말 · B 하나로 물러서기(12.11 — 요구 원문에서 나온 표시 규칙).
- 절차: explorer 가 열지 말라던 파일을 염 · 메인 제안이 앞선 기록과 어긋남(별도 앱 · 포트 10000) · 감사가 종합을 뒤집음 · 리뷰 한도 초과 승인 · main 직접 push 를 자동 모드가 막음 · 출력 가림 누락(가림 규칙 보강은 절차).
- 해결되지 않은 것: `/deploys` 화면 테스트의 병렬 부하 시간 초과(약 2.9초 / 5초 — 후보로만 남음).
- K1 의 도커 포트 공개(userland-proxy) 우려: 실측 결과 문제가 없었다(공인 주소가 그대로 보임) — 발생한 문제가 아님.
