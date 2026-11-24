# claude-bridge — PC에서 실행하는 에스컬레이션 브리지

backend(홈랩)가 PC의 `claude -p`를 쓰게 해주는 최소 HTTP 서버. PC↔홈랩이 서브넷
분리라 역방향으로 노출한다.

## 기동 (PC)
1. `export BRIDGE_SECRET=<docs/secrets.md의 값>`
2. `python3 server.py &`  — 127.0.0.1:15100 (인증·동시1)
3. `ssh -N -R 15101:localhost:15100 jun@<LAN>.158 &`  — 역터널(루프백)
4. .158에서 socat 릴레이:
   `docker run -d --name claude-bridge-relay --network host --restart unless-stopped alpine/socat tcp-listen:15100,fork,reuseaddr tcp:127.0.0.1:15101`
5. backend .env: `CLAUDE_BRIDGE_URL=http://<LAN>.158:15100` + `BRIDGE_SECRET=<동일>`

## 보안 (codex 리뷰 F2~F8)
공유 시크릿 상수시간 인증 · 동시 1건 · 프롬프트 60KB/출력 20KB 상한 · Content-Length 검증 ·
도구 차단(아래) · stderr 비노출 · 전송은 역터널+socat(backend만).

### 도구 차단 (2026-11-25 고침)
- **왜 바꿨나**: 전에는 `--allowedTools ""` 로 도구를 막았다고 여겼지만, 그 옵션은 묻지 않고
  실행할 도구를 미리 승인하는 목록일 뿐 쓸 수 있는 도구를 줄이지 않는다. 실측에서 통로를 띄운
  폴더의 파일이 질문 하나로 읽혀 답에 실렸다. 첫 수정(`--tools ""` + 빈 폴더)도 모자랐다 —
  질문이 옵션으로 읽혔고(질문 `--version` → 버전 글자), 계정에 연결된 MCP 도구가 남았고,
  요청마다 세션 기록이 PC 에 쌓였다. 그 뒤에도 질문 `/context` 가 명령으로 실행됐다.
- **무엇을 쓰나** (`claude` 는 `-p --output-format text --tools "" --strict-mcp-config --restricted
  --no-session-persistence --disable-slash-commands --safe-mode` 의 고정 인자로 돈다). 옵션마다의 뜻은
  `claude` 의 설명을 옮긴 것이다:
  - 질문은 **표준 입력**으로 준다 — 인자는 고정 목록뿐이라 질문 글이 옵션으로 읽히지 않는다.
  - `--tools ""` — 내장 도구(파일 읽기 · 명령 실행 · 웹 포함)를 비운다.
  - `--strict-mcp-config` — `--mcp-config` 로 준 것 말고의 MCP 설정을 싣지 않는다.
  - `--restricted` — 사용자 · 프로젝트 · 로컬 설정 파일을 무시한다.
  - `--no-session-persistence` — 질문과 답을 PC 의 `~/.claude/projects/` 에 남기지 않는다.
  - `--disable-slash-commands` — `/` 로 시작하는 질문을 명령 · 스킬로 처리하지 않는다.
  - `--safe-mode` — 지시 파일(CLAUDE.md) · 스킬 · 플러그인 · 훅 등 PC 의 꾸밈을 끈다.
  - `claude` 는 요청마다 새로 만든 **빈 임시 폴더**에서 돌고, 요청이 끝나면 그 폴더를 지운다
    (지우기에 실패해도 응답은 바뀌지 않는다). 이것이 막는 것은 **상대 경로와 작업 폴더의 기본 탐색뿐**이고,
    도구가 살아 있다면 절대 경로 읽기는 막지 못한다.
  - `claude` 의 환경에서 `BRIDGE_SECRET` 를 뺀다.
  - UTF-8 로 바꿀 수 없는 질문(짝 없는 대리쌍)은 `claude` 를 부르지 않고 422 로 거절한다.
- **실측 결과** (이 PC, `claude` 2.1.331, 위 옵션을 **함께** 쓴 상태): 쓸 수 있는 도구(MCP 포함)가 없었고,
  통로를 띄운 폴더의 표식 파일이 답에 실리지 않았고, 질문 `--version` · `/context` 가 옵션 · 명령으로
  처리되지 않았고, 세션 기록 폴더가 늘지 않았고, 구독 로그인으로 정상 답했다. 어느 옵션이 어느 결과를
  낳았는지는 하나씩 갈라 재지 않았다(예: MCP 가 없어진 것을 `--strict-mcp-config` 하나의 효과로 단정하지
  않는다). **`claude` 의 판이 바뀌면 다시 재야 한다.**
- **답의 성격**: 도구가 없는 모델은 파일 읽기 · 명령 실행을 요구하는 질문에 지어낸 내용(없는 파일의
  내용 · 하지 않은 실행의 결과)을 답하거나 빈 답을 낼 수 있다(실측에서 관찰). 그것은 실제 PC 의 내용이 아니다.
- **남는 한계**:
  - 지시 파일: `--safe-mode` 의 설명에 CLAUDE.md 가 들어 있다. 실측에서 작업 폴더의 CLAUDE.md 지시를
    따르지 않았다(한 번 — 읽지 않은 것인지, 읽고 따르지 않은 것인지까지는 가르지 못했다). `~/.claude` 와
    임시 폴더의 윗 경로(`tempfile` 의 기본 위치와 그 위)에 놓인 지시 파일도 이 옵션에 기댄다.
  - `BRIDGE_SECRET` 말고의 환경은 그대로 물려준다(구독 로그인에 필요하다) — 통로를 띄운 셸의
    다른 환경 변수도 `claude` 에 넘어간다.
  - 시간 초과 때 `claude` 본체는 죽이지만, 그것이 띄운 자식 프로세스까지는 죽이지 않는다(도구가 없어
    띄울 일은 거의 없다).
  - Claude 를 전용 컨테이너로 옮기면 PC 의 설정 · 파일과 떨어진다.
- **기록**: 통로 자체는 이용 기록을 남기지 않는다. 다만 **고치기 전의 통로는 `claude` 의 세션 기록을
  띄운 폴더 이름으로 `~/.claude/projects/` 아래에 남겼을 수 있다**(지금은 `--no-session-persistence` 로
  남기지 않는다). 그 밖에 고치기 전에 누가 이용했는지는 확인할 수 없다.
