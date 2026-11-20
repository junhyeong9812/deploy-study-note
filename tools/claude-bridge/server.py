#!/usr/bin/env python3
"""Claude 브리지 — PC에서 실행. POST /ask {prompt} -> claude -p -> {answer}. (chat-design 5-b)

보안(codex 리뷰 F2~F8 반영): 공유 시크릿 상수시간 검증·동시 1건·출력 상한·프롬프트 주입 완화.
전송 경계: 역 SSH 터널(PC->.158 루프백) + .158 socat이 backend에서만 접근 — LAN 광노출 아님.
"""
import hmac
import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 15100
CLAUDE = "/home/jun/.local/bin/claude"
TIMEOUT_S = 150
MAX_PROMPT = 60_000
MAX_OUTPUT = 20_000
SECRET = os.environ.get("BRIDGE_SECRET", "")
# 문서 내부 지시를 실행하지 못하도록 모든 도구 차단 — 순수 텍스트 응답만 (F3)
CLAUDE_ARGS = ["--output-format", "text", "--allowedTools", ""]

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
            result = subprocess.run(
                [CLAUDE, "-p", prompt, *CLAUDE_ARGS],
                capture_output=True, text=True, timeout=TIMEOUT_S,
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
