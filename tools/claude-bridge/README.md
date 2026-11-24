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

### 도구 차단 — 두 겹 (2026-11-25 고침)
- **왜 바꿨나**: 전에는 `--allowedTools ""` 로 도구를 막았다고 여겼지만, 그 옵션은 묻지 않고
  실행할 도구를 미리 승인하는 목록일 뿐 쓸 수 있는 도구를 줄이지 않는다. 실측에서 통로를 띄운
  폴더의 파일이 질문 하나로 읽혀 답에 실렸다.
- **지금의 두 겹**: ① `--tools ""` — 쓸 수 있는 도구의 집합을 비운다(파일 읽기 · 명령 실행 · 웹 포함).
  ② `claude` 는 요청마다 새로 만든 빈 임시 폴더에서 돌고, 요청이 끝나면 그 폴더를 지운다 —
  도구 차단이 풀리는 일이 생겨도 작업 폴더에 읽을 것이 없게. 또 `claude` 의 환경에서
  `BRIDGE_SECRET` 를 뺀다(나머지 환경은 구독 로그인에 필요해 그대로 물려준다).
- **알려진 한계**: `claude` 는 통로를 띄운 PC 의 개인 설정(`~/.claude` 의 지시 · 훅)을 읽고 돈다.
  Claude 를 전용 컨테이너로 옮기면 풀린다.
- **기록 없음**: 통로는 요청 기록을 남기지 않는다. 고치기 전에 통로가 떠 있던 동안 누가 이용했는지는
  확인할 수 없다.
