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
`--allowedTools ""` 로 도구 전면 차단(프롬프트 주입 완화) · stderr 비노출 · 전송은 역터널+socat(backend만).
