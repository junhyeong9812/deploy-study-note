#!/usr/bin/env python3
"""Claude 브리지 — PC에서 실행. POST /ask {prompt} -> claude -p -> {answer}. (chat-design 5-b)

보안(codex 리뷰 F2~F8 반영): 공유 시크릿 상수시간 검증·동시 1건·출력 상한·프롬프트 주입 완화.
claude 에게 질문은 표준 입력으로만 주고(인자는 고정 목록), 내장 도구(--tools "")와 MCP(--strict-mcp-config)를
비우고, 설정 파일을 무시하고(--restricted), 세션 기록을 남기지 않는다(--no-session-persistence).
요청마다 새로 만든 빈 임시 폴더에서 돌고, 환경에서 BRIDGE_SECRET 만 뺀다.
전송 경계: 역 SSH 터널(PC->.158 루프백) + .158 socat이 backend에서만 접근 — LAN 광노출 아님.
"""
import hmac
import json
import os
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 15100
CLAUDE = "/home/jun/.local/bin/claude"
TIMEOUT_S = 150
MAX_PROMPT = 60_000
MAX_OUTPUT = 20_000
SECRET = os.environ.get("BRIDGE_SECRET", "")
# 고정 인자 — 질문에서 나온 글은 하나도 넣지 않는다(질문은 표준 입력: 인자로 주면 '-' 로 시작하는 글이 옵션으로 읽힌다).
# --tools "" 는 내장 도구(파일 읽기·명령 실행·웹 포함)를, --strict-mcp-config 는 계정에 연결된 MCP 도구를 비운다 (F3)
# --allowedTools 는 묻지 않고 실행할 목록일 뿐이라 도구를 막지 못했다(실측: 띄운 폴더의 파일이 읽힘)
CLAUDE_ARGS = ["-p", "--output-format", "text", "--tools", "", "--strict-mcp-config",
               "--restricted", "--no-session-persistence"]

_inflight = threading.Semaphore(1)   # 동시 1건 — 단일 요청이 전체를 점유하지 않게 즉시 거절 (F4)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/ask":
            return self._json(404, {"error": "not_found"})
        provided = self.headers.get("X-Bridge-Secret", "")
        if not SECRET or not hmac.compare_digest(provided, SECRET):   # 인증·상수시간 (F2)
            return self._json(401, {"error": "unauthorized"})
        if self.headers.get("Transfer-Encoding"):                      # chunked 거부 (F7)
            return self._json(411, {"error": "length_required"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._json(400, {"error": "bad_length"})
        if not (1 <= length <= MAX_PROMPT + 1024):                     # 범위 강제 (F7)
            return self._json(413, {"error": "bad_length"})
        if not _inflight.acquire(blocking=False):                      # 동시 1건 (F4)
            return self._json(503, {"error": "busy"})
        try:
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                return self._json(422, {"error": "bad_body"})
            prompt = str(body.get("prompt", ""))[:MAX_PROMPT]
            if not prompt.strip():
                return self._json(422, {"error": "empty_prompt"})
            # 요청마다 빈 임시 폴더에서 돌리고 끝나면 지운다(시간 초과 땐 자식이 끝난 뒤) — 지우기의 실패는 응답을 바꾸지 않는다.
            # 프로세스 전체의 chdir 대신 cwd= — 서버가 여러 스레드다. 비밀값은 물려주지 않는다.
            with tempfile.TemporaryDirectory(prefix="claude-bridge-", ignore_cleanup_errors=True) as empty_directory:
                result = subprocess.run(
                    [CLAUDE, *CLAUDE_ARGS], input=prompt, encoding="utf-8",
                    capture_output=True, timeout=TIMEOUT_S, cwd=empty_directory,
                    env={key: value for key, value in os.environ.items() if key != "BRIDGE_SECRET"},
                )
            if result.returncode != 0:
                return self._json(502, {"error": "claude_failed"})     # stderr 비노출 (F8)
            self._json(200, {"answer": result.stdout.strip()[:MAX_OUTPUT]})   # 출력 상한 (F6)
        except subprocess.TimeoutExpired:
            self._json(504, {"error": "timeout"})
        except Exception:
            self._json(500, {"error": "internal"})
        finally:
            _inflight.release()

    def _json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    if not SECRET:
        raise SystemExit("BRIDGE_SECRET required")
    print(f"[bridge] listening 127.0.0.1:{PORT} (auth on, concurrency 1)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
