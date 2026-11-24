"""claude-bridge 통로(server.py)의 테스트 — 실제 claude 를 부르지 않는다.

가짜 claude 실행 파일이 받은 인자 · 작업 폴더 · 그 폴더의 파일 목록을 기록 파일에 적는다.
통로는 임시 포트(0 번)로 루프백에 띄워 HTTP 로 부른다.
실행: cd tools/claude-bridge && python3 -m unittest -v
"""
import http.client
import importlib.util
import io
import json
import os
import runpy
import shutil
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stdout
from http.server import ThreadingHTTPServer
from unittest import mock

BRIDGE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
# 고장 내기 확인용으로 사본을 가리킬 수 있게 한다 — 평소에는 같은 폴더의 server.py
SERVER_PATH = os.environ.get("BRIDGE_SERVER_UNDER_TEST") or os.path.join(BRIDGE_DIRECTORY, "server.py")
PLANTED_KEY = "BRIDGE_TEST_PLANTED_KEY"
PLANTED_VALUE = "planted-value"
TEST_SECRET = "test-secret-value"
FAKE_ANSWER = "  fake answer  \n"
STDERR_MARKER = "STDERR-LEAK-MARKER"

FAKE_CLAUDE_TEMPLATE = """#!{python} -I
import json, os, sys, time
RECORD = {record!r}
CONTROL = {control!r}
RELEASE = {release!r}
working_directory = os.getcwd()
entry = {{
    "argv": sys.argv[1:],
    "cwd": os.path.realpath(working_directory),
    "listing": sorted(os.listdir(working_directory)),
    # 환경 변수의 값은 남기지 않는다 — 있는지 여부와, 테스트가 심은 키의 값만
    "secret_in_env": "BRIDGE_SECRET" in os.environ,
    "home_in_env": "HOME" in os.environ,
    "path_in_env": "PATH" in os.environ,
    "planted_value": os.environ.get({planted_key!r}),
}}
with open(RECORD, "a", encoding="utf-8") as record_file:
    record_file.write(json.dumps(entry) + "\\n")
mode = "ok"
if os.path.exists(CONTROL):
    with open(CONTROL, encoding="utf-8") as control_file:
        mode = control_file.read().strip()
if mode == "ok":
    sys.stdout.write({answer!r})
elif mode == "fail":
    sys.stderr.write({stderr_marker!r})
    sys.exit(3)
elif mode == "sleep":
    time.sleep(10)
elif mode == "block":
    deadline = time.time() + 10
    while not os.path.exists(RELEASE) and time.time() < deadline:
        time.sleep(0.02)
    sys.stdout.write("released")
elif mode == "big":
    sys.stdout.write("x" * 25000)
elif mode == "badbytes":
    sys.stdout.flush()
    sys.stdout.buffer.write(b"\\xff\\xfe\\xfa\\n")
"""


def load_server_module():
    """server.py 를 경로로 새로 불러온다 — 테스트마다 새 모듈(세마포어 상태 포함)."""
    specification = importlib.util.spec_from_file_location("claude_bridge_server_under_test", SERVER_PATH)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class BridgeTestCase(unittest.TestCase):
    def setUp(self):
        self.work_root = os.path.realpath(tempfile.mkdtemp(prefix="bridge-test-"))
        self.addCleanup(shutil.rmtree, self.work_root, True)

        # 통로를 "띄운 자리" — 파일이 있는 폴더. claude 가 여기서 돌면 안 된다.
        self.launch_directory = os.path.join(self.work_root, "launch")
        os.mkdir(self.launch_directory)
        with open(os.path.join(self.launch_directory, "marker.txt"), "w", encoding="utf-8") as marker_file:
            marker_file.write("MARKER-SHOULD-NOT-BE-READ")
        original_directory = os.getcwd()
        os.chdir(self.launch_directory)
        self.addCleanup(os.chdir, original_directory)

        # 통로가 tempfile 로 만드는 임시 폴더가 이 폴더 아래에 생기게 한다 — 요청 뒤 비었는지 본다.
        self.bridge_temp_root = os.path.join(self.work_root, "bridge-tmp")
        os.mkdir(self.bridge_temp_root)
        original_tempdir = tempfile.tempdir
        tempfile.tempdir = self.bridge_temp_root
        self.addCleanup(setattr, tempfile, "tempdir", original_tempdir)

        self.record_path = os.path.join(self.work_root, "record.jsonl")
        self.control_path = os.path.join(self.work_root, "control")
        self.release_path = os.path.join(self.work_root, "release")
        self.fake_claude_path = os.path.join(self.work_root, "fake-claude")
        with open(self.fake_claude_path, "w", encoding="utf-8") as fake_file:
            fake_file.write(FAKE_CLAUDE_TEMPLATE.format(
                python=sys.executable, record=self.record_path, control=self.control_path,
                release=self.release_path, answer=FAKE_ANSWER, stderr_marker=STDERR_MARKER,
                planted_key=PLANTED_KEY,
            ))
        os.chmod(self.fake_claude_path, 0o755)

        self.server_module = load_server_module()
        self.server_module.CLAUDE = self.fake_claude_path
        self.server_module.SECRET = TEST_SECRET
        self.server_module.TIMEOUT_S = 0.5

        self.http_server = ThreadingHTTPServer(("127.0.0.1", 0), self.server_module.Handler)
        self.port = self.http_server.server_address[1]
        serving_thread = threading.Thread(target=self.http_server.serve_forever, daemon=True)
        serving_thread.start()
        self.addCleanup(serving_thread.join, 5)
        self.addCleanup(self.http_server.server_close)
        self.addCleanup(self.http_server.shutdown)

    # --- 도움 함수 ---
    def set_mode(self, mode):
        with open(self.control_path, "w", encoding="utf-8") as control_file:
            control_file.write(mode)

    def records(self):
        if not os.path.exists(self.record_path):
            return []
        with open(self.record_path, encoding="utf-8") as record_file:
            return [json.loads(line) for line in record_file if line.strip()]

    def raw_request(self, path="/ask", body=b"", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=15)
        try:
            connection.putrequest("POST", path, skip_accept_encoding=True)
            for name, value in (headers or {}).items():
                connection.putheader(name, value)
            connection.endheaders()
            if body:
                connection.send(body)
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()

    def ask(self, prompt="hello", secret=TEST_SECRET, path="/ask"):
        body = json.dumps({"prompt": prompt}).encode()
        headers = {"Content-Type": "application/json", "Content-Length": str(len(body))}
        if secret is not None:
            headers["X-Bridge-Secret"] = secret
        status, data = self.raw_request(path, body, headers)
        return status, json.loads(data)

    def ask_and_get_record(self, prompt="hello"):
        status, payload = self.ask(prompt)
        entries = self.records()
        self.assertEqual(len(entries), 1, "가짜 claude 가 정확히 한 번 불려야 한다")
        return status, payload, entries[0]

    def assert_temp_root_empty(self):
        self.assertEqual(os.listdir(self.bridge_temp_root), [], "통로가 만든 임시 폴더가 남아 있다")


# ---------------------------------------------------------------- 명세 ② (가) 인자
class ClaudeArgumentsTest(BridgeTestCase):
    def test_tools_flag_with_empty_value_is_passed(self):
        _, _, entry = self.ask_and_get_record()
        arguments = entry["argv"]
        self.assertIn("--tools", arguments, f"--tools 가 인자에 없다: {arguments}")
        self.assertEqual(arguments[arguments.index("--tools") + 1], "", "--tools 의 값이 빈 글자가 아니다")

    def test_allowed_tools_flag_is_absent(self):
        _, _, entry = self.ask_and_get_record()
        self.assertNotIn("--allowedTools", entry["argv"])

    def test_output_format_text_is_kept(self):
        _, _, entry = self.ask_and_get_record()
        arguments = entry["argv"]
        self.assertIn("--output-format", arguments)
        self.assertEqual(arguments[arguments.index("--output-format") + 1], "text")

    def test_hostile_prompt_is_a_single_argument_after_p(self):
        hostile = "a'b\"c; rm -rf / $(id) `id`\nline2 --tools Read --allowedTools Bash"
        _, _, entry = self.ask_and_get_record(hostile)
        arguments = entry["argv"]
        self.assertEqual(arguments.count("-p"), 1)
        self.assertEqual(arguments[arguments.index("-p") + 1], hostile)
        # 같은 통로에 평범한 질문을 보냈을 때와 인자 개수가 같다 — 질문이 인자를 늘리지 않는다.
        os.remove(self.record_path)
        _, _, benign_entry = self.ask_and_get_record("plain")
        benign_entry_arguments = benign_entry["argv"]
        self.assertEqual(len(arguments), len(benign_entry_arguments))
        self.assertEqual(arguments.count("--tools"), benign_entry_arguments.count("--tools"))


# ---------------------------------------------------------------- 명세 ② (나) 빈 임시 폴더
class WorkingDirectoryTest(BridgeTestCase):
    def test_claude_runs_in_an_empty_directory(self):
        _, _, entry = self.ask_and_get_record()
        self.assertEqual(entry["listing"], [], f"claude 의 작업 폴더가 비어 있지 않다: {entry['cwd']}")

    def test_claude_does_not_run_in_launch_directory(self):
        _, _, entry = self.ask_and_get_record()
        self.assertNotEqual(entry["cwd"], self.launch_directory)

    def test_claude_does_not_run_in_bridge_directory(self):
        # 통로를 자기 폴더에서 띄운 경우(README 의 기동 순서 그대로)
        os.chdir(BRIDGE_DIRECTORY)
        _, _, entry = self.ask_and_get_record()
        self.assertNotEqual(entry["cwd"], BRIDGE_DIRECTORY)


# ---------------------------------------------------------------- 명세 ② (나) 요청마다 지움
class TemporaryDirectoryCleanupTest(BridgeTestCase):
    def assert_cwd_removed_after(self, mode, expected_status):
        self.set_mode(mode)
        status, _, entry = self.ask_and_get_record()
        self.assertEqual(status, expected_status)
        self.assertNotEqual(entry["cwd"], self.launch_directory, "통로가 임시 폴더를 만들지 않았다(띄운 자리에서 돎)")
        self.assertFalse(os.path.exists(entry["cwd"]), f"요청 뒤 작업 폴더가 남아 있다: {entry['cwd']}")
        self.assert_temp_root_empty()

    def test_directory_removed_after_success(self):
        self.assert_cwd_removed_after("ok", 200)

    def test_directory_removed_after_claude_failure(self):
        self.assert_cwd_removed_after("fail", 502)

    def test_directory_removed_after_timeout(self):
        self.assert_cwd_removed_after("sleep", 504)

    def test_directory_removed_after_exception(self):
        # 표준 출력이 UTF-8 이 아니면 디코딩 예외 → 500
        self.assert_cwd_removed_after("badbytes", 500)

    def test_two_requests_use_different_directories(self):
        self.ask()
        self.ask()
        entries = self.records()
        self.assertEqual(len(entries), 2)
        self.assertNotEqual(entries[0]["cwd"], entries[1]["cwd"], "두 요청이 같은 작업 폴더를 썼다")


# ---------------------------------------------------------------- 진행 중 결정 — 비밀값을 물려주지 않는다
class ClaudeEnvironmentTest(BridgeTestCase):
    def ask_with_bridge_environment(self):
        with mock.patch.dict(os.environ, {"BRIDGE_SECRET": "secret-in-bridge-env", PLANTED_KEY: PLANTED_VALUE}):
            self.assertIn("HOME", os.environ)
            self.assertIn("PATH", os.environ)
            _, _, entry = self.ask_and_get_record()
        return entry

    def test_bridge_secret_is_not_passed_to_claude(self):
        entry = self.ask_with_bridge_environment()
        self.assertFalse(entry["secret_in_env"], "BRIDGE_SECRET 가 claude 의 환경에 넘어갔다")

    def test_rest_of_environment_is_passed_to_claude(self):
        entry = self.ask_with_bridge_environment()
        self.assertTrue(entry["home_in_env"], "HOME 이 claude 의 환경에 없다")
        self.assertTrue(entry["path_in_env"], "PATH 가 claude 의 환경에 없다")
        self.assertEqual(entry["planted_value"], PLANTED_VALUE, "통로 환경의 다른 키가 그대로 넘어가지 않았다")


# ---------------------------------------------------------------- 명세 ② (다) 그대로 둘 것 (특성 테스트)
class PreservedBehaviorTest(BridgeTestCase):
    def test_missing_secret_header_is_401(self):
        status, payload = self.ask(secret=None)
        self.assertEqual((status, payload), (401, {"error": "unauthorized"}))
        self.assertEqual(self.records(), [])

    def test_wrong_secret_is_401(self):
        status, payload = self.ask(secret="wrong")
        self.assertEqual((status, payload), (401, {"error": "unauthorized"}))
        self.assertEqual(self.records(), [])

    def test_server_without_secret_rejects_everything(self):
        self.server_module.SECRET = ""
        status, _ = self.ask(secret="")
        self.assertEqual(status, 401)

    def test_unknown_path_is_404(self):
        status, payload = self.ask(path="/other")
        self.assertEqual((status, payload), (404, {"error": "not_found"}))

    def test_transfer_encoding_is_411(self):
        status, data = self.raw_request(body=b"0\r\n\r\n", headers={
            "X-Bridge-Secret": TEST_SECRET, "Transfer-Encoding": "chunked"})
        self.assertEqual((status, json.loads(data)), (411, {"error": "length_required"}))

    def test_bad_content_length_is_400(self):
        status, data = self.raw_request(headers={"X-Bridge-Secret": TEST_SECRET, "Content-Length": "abc"})
        self.assertEqual((status, json.loads(data)), (400, {"error": "bad_length"}))

    def test_zero_length_is_413(self):
        status, data = self.raw_request(headers={"X-Bridge-Secret": TEST_SECRET, "Content-Length": "0"})
        self.assertEqual((status, json.loads(data)), (413, {"error": "bad_length"}))

    def test_too_large_length_is_413(self):
        too_large = self.server_module.MAX_PROMPT + 1025
        status, data = self.raw_request(headers={"X-Bridge-Secret": TEST_SECRET, "Content-Length": str(too_large)})
        self.assertEqual((status, json.loads(data)), (413, {"error": "bad_length"}))
        self.assertEqual(self.records(), [])

    def test_non_object_json_is_422(self):
        body = b"[1, 2]"
        status, data = self.raw_request(body=body, headers={
            "X-Bridge-Secret": TEST_SECRET, "Content-Length": str(len(body))})
        self.assertEqual((status, json.loads(data)), (422, {"error": "bad_body"}))

    def test_blank_prompt_is_422(self):
        status, payload = self.ask("   \n ")
        self.assertEqual((status, payload), (422, {"error": "empty_prompt"}))
        self.assertEqual(self.records(), [])

    def test_second_concurrent_request_is_503(self):
        self.set_mode("block")
        first_result = {}

        def first_request():
            first_result["status"], first_result["payload"] = self.ask("first")

        first_thread = threading.Thread(target=first_request)
        first_thread.start()
        deadline = time.time() + 5
        while not self.records() and time.time() < deadline:
            time.sleep(0.02)
        self.assertEqual(len(self.records()), 1, "첫 요청이 claude 에 닿지 않았다")
        status, payload = self.ask("second")
        open(self.release_path, "w").close()
        first_thread.join(10)
        self.assertEqual((status, payload), (503, {"error": "busy"}))
        self.assertEqual(first_result, {"status": 200, "payload": {"answer": "released"}})
        self.assertEqual(len(self.records()), 1, "둘째 요청이 claude 를 불렀다")
        # 첫 요청이 끝나면 다시 받는다
        self.set_mode("ok")
        self.assertEqual(self.ask()[0], 200)

    def test_claude_failure_is_502_without_stderr(self):
        self.set_mode("fail")
        status, data = self.raw_request(body=json.dumps({"prompt": "x"}).encode(), headers={
            "X-Bridge-Secret": TEST_SECRET, "Content-Length": str(len(json.dumps({"prompt": "x"})))})
        self.assertEqual((status, json.loads(data)), (502, {"error": "claude_failed"}))
        self.assertNotIn(STDERR_MARKER.encode(), data)

    def test_timeout_is_504(self):
        self.set_mode("sleep")
        started = time.time()
        status, payload = self.ask()
        self.assertEqual((status, payload), (504, {"error": "timeout"}))
        self.assertLess(time.time() - started, 5)

    def test_exception_is_500(self):
        self.set_mode("badbytes")
        self.assertEqual(self.ask(), (500, {"error": "internal"}))

    def test_success_is_200_with_stripped_answer(self):
        status, payload = self.ask()
        self.assertEqual((status, payload), (200, {"answer": FAKE_ANSWER.strip()}))

    def test_output_is_capped_at_20000_characters(self):
        self.set_mode("big")
        status, payload = self.ask()
        self.assertEqual(status, 200)
        self.assertEqual(payload["answer"], "x" * 20000)

    def test_prompt_is_truncated_to_60000_characters(self):
        long_prompt = "a" * 60_010
        status, _, entry = self.ask_and_get_record(long_prompt)
        self.assertEqual(status, 200)
        arguments = entry["argv"]
        self.assertEqual(arguments[arguments.index("-p") + 1], "a" * 60_000)

    def test_main_listens_on_loopback_only(self):
        bound_addresses = []

        class RecordingServer:
            def __init__(self, address, handler):
                bound_addresses.append(address)

            def serve_forever(self):
                return None

        with mock.patch("http.server.ThreadingHTTPServer", RecordingServer), \
                mock.patch.dict(os.environ, {"BRIDGE_SECRET": "dummy"}), \
                redirect_stdout(io.StringIO()):
            runpy.run_path(SERVER_PATH, run_name="__main__")
        self.assertEqual(len(bound_addresses), 1)
        self.assertEqual(bound_addresses[0], ("127.0.0.1", 15100))

    def test_main_refuses_to_start_without_secret(self):
        environment = {key: value for key, value in os.environ.items() if key != "BRIDGE_SECRET"}
        with mock.patch.dict(os.environ, environment, clear=True), \
                mock.patch("http.server.ThreadingHTTPServer") as server_class:
            with self.assertRaises(SystemExit):
                runpy.run_path(SERVER_PATH, run_name="__main__")
        server_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
