"""claude-bridge 통로(server.py)의 테스트 — 실제 claude 를 부르지 않는다.

가짜 claude 실행 파일이 받은 인자 · 작업 폴더 · 그 폴더의 파일 목록을 기록 파일에 적는다.
통로는 임시 포트(0 번)로 루프백에 띄워 HTTP 로 부른다.
실행: cd tools/claude-bridge && python3 -m unittest -v
"""
import hashlib
import http.client
import importlib.util
import io
import json
import os
import runpy
import shutil
import subprocess
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
import os
# 뜨자마자(표준 입력을 읽기 전에) 시작 표식을 남긴다 — 띄워졌다가 기록 전에 죽은 경우도 잡게
with open({started!r}, "a") as started_file:
    started_file.write("started\\n")
import hashlib, json, select, sys, time
RECORD = {record!r}
CONTROL = {control!r}
RELEASE = {release!r}
mode = "ok"
if os.path.exists(CONTROL):
    with open(CONTROL, encoding="utf-8") as control_file:
        mode = control_file.read().strip()


def read_standard_input():
    # 표준 입력이 파이프로 닫혀 오면 끝까지 읽는다. 통로가 표준 입력을 주지 않으면(물려받은 입력)
    # 처음 0.3초 안에 아무것도 없을 때 None — 테스트 실행자의 입력을 기다리며 멈추지 않게.
    chunks = []
    wait_seconds = 0.3
    while True:
        readable, _, _ = select.select([0], [], [], wait_seconds)
        if not readable:
            return None if not chunks else b"".join(chunks)
        chunk = os.read(0, 65536)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)
        wait_seconds = 3


if mode == "noread":
    standard_input = None
    os.close(0)          # 읽지 않고 닫는다 — 통로 쪽 쓰기가 깨진 파이프를 만날 수 있게
    time.sleep(0.2)
else:
    standard_input = read_standard_input()
working_directory = os.getcwd()
entry = {{
    # 표준 입력은 길이 · 해시 · 앞 4096 바이트(16진)만 — 기록 파일이 커지지 않게. 머리말 비교는 앞부분으로, 전체는 해시로.
    "stdin_bytes": None if standard_input is None else len(standard_input),
    "stdin_sha256": None if standard_input is None else hashlib.sha256(standard_input).hexdigest(),
    "stdin_head_hex": None if standard_input is None else standard_input[:4096].hex(),
    # 파일 첨부를 끄는 키 — 비밀이 아니므로 값을 남긴다
    "file_mentions_setting": os.environ.get("CLAUDE_CODE_DISABLE_FILE_MENTIONS"),
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


def replace_working_directory_with_file():
    # 지울 수 없는 것을 남긴다: 빈 작업 폴더를 같은 이름의 '파일'로 바꾼다 — 폴더를 지우는 쪽이
    # NotADirectoryError 를 만난다(권한과 무관 — root 로 돌아도 같다). 폴더가 비어 있지 않으면(띄운 자리) 손대지 않는다.
    if os.listdir(working_directory):
        return
    os.chdir("/")
    os.rmdir(working_directory)
    with open(working_directory, "w") as blocker:
        blocker.write("blocker")


if mode in ("ok", "noread"):
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
elif mode == "leave_undeletable":
    replace_working_directory_with_file()
    sys.stdout.write({answer!r})
elif mode == "leave_undeletable_sleep":
    replace_working_directory_with_file()
    time.sleep(10)
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
        self.started_path = os.path.join(self.work_root, "started")
        self.fake_claude_path = os.path.join(self.work_root, "fake-claude")
        with open(self.fake_claude_path, "w", encoding="utf-8") as fake_file:
            fake_file.write(FAKE_CLAUDE_TEMPLATE.format(
                python=sys.executable, record=self.record_path, control=self.control_path,
                release=self.release_path, answer=FAKE_ANSWER, stderr_marker=STDERR_MARKER,
                planted_key=PLANTED_KEY, started=self.started_path,
            ))
        os.chmod(self.fake_claude_path, 0o755)

        self.server_module = load_server_module()
        self.server_module.CLAUDE = self.fake_claude_path
        self.server_module.SECRET = TEST_SECRET
        # 가짜가 물려받은 표준 입력을 0.3초 기다리므로(지금 코드) 여유를 둔다
        self.server_module.TIMEOUT_S = 2.0

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

    def ask(self, prompt="hello", secret=TEST_SECRET, path="/ask", ensure_ascii=True, retry_busy=True):
        body = json.dumps({"prompt": prompt}, ensure_ascii=ensure_ascii).encode()
        headers = {"Content-Type": "application/json", "Content-Length": str(len(body))}
        if secret is not None:
            headers["X-Bridge-Secret"] = secret
        # 통로는 응답을 보낸 '뒤에' 동시 1건 표를 돌려준다 — 바로 이은 요청이 드물게 503 을 받는다.
        # 연달아 부르는 테스트가 흔들리지 않게 503 이면 잠깐 뒤 다시 부른다(503 자체를 보는 테스트는 retry_busy=False).
        for _ in range(50):
            status, data = self.raw_request(path, body, headers)
            if not (retry_busy and status == 503):
                break
            time.sleep(0.02)
        return status, json.loads(data)

    def ask_and_get_record(self, prompt="hello", ensure_ascii=True):
        status, payload = self.ask(prompt, ensure_ascii=ensure_ascii)
        entries = self.records()
        self.assertEqual(len(entries), 1, f"가짜 claude 가 정확히 한 번 불려야 한다(응답 {status} {payload})")
        return status, payload, entries[0]

    def prompt_lead(self):
        """통로가 질문 앞에 붙이는 고정 머리말 — server 모듈의 상수 PROMPT_LEAD 를 읽는다(글을 테스트에 박지 않는다)."""
        lead = getattr(self.server_module, "PROMPT_LEAD", None)
        self.assertIsInstance(lead, str, "server 모듈에 머리말 상수 PROMPT_LEAD(str)가 없다")
        return lead

    def assert_prompt_went_through_standard_input(self, entry, prompt):
        """표준 입력 = 머리말 + 질문의 UTF-8 바이트(질문은 바꾸지 않는다)."""
        self.assertIsNotNone(entry["stdin_sha256"], "claude 가 표준 입력으로 받은 것이 없다")
        lead_bytes = self.prompt_lead().encode("utf-8")
        head = bytes.fromhex(entry["stdin_head_hex"])
        self.assertTrue(head.startswith(lead_bytes), f"표준 입력이 머리말로 시작하지 않는다: {head[:60]!r}")
        expected = lead_bytes + prompt.encode("utf-8")
        self.assertEqual(entry["stdin_bytes"], len(expected), "표준 입력의 길이가 머리말 + 질문과 다르다")
        self.assertEqual(entry["stdin_sha256"], hashlib.sha256(expected).hexdigest(),
                         "머리말 뒤의 나머지가 질문의 바이트와 다르다")

    def assert_prompt_not_in_arguments(self, entry, prompt):
        for argument in entry["argv"]:
            self.assertNotIn(prompt, argument, f"질문 글이 인자에 들어 있다: {argument[:80]!r}")

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

    def fixed_arguments(self):
        """평범한 질문 하나로 본 인자 목록 — 이후 어떤 질문이든 이것과 같아야 한다."""
        _, _, entry = self.ask_and_get_record("plain question")
        os.remove(self.record_path)
        return entry["argv"]

    def test_prompt_flag_and_required_flags_are_present(self):
        _, _, entry = self.ask_and_get_record()
        arguments = entry["argv"]
        for flag in ("-p", "--strict-mcp-config", "--restricted", "--no-session-persistence",
                     "--disable-slash-commands", "--safe-mode"):
            self.assertIn(flag, arguments, f"{flag} 가 인자에 없다: {arguments}")

    def test_forbidden_flags_are_absent(self):
        _, _, entry = self.ask_and_get_record()
        for flag in ("--allowedTools", "--mcp-config", "--settings", "--add-dir", "--dangerously-skip-permissions"):
            self.assertFalse(any(argument == flag or argument.startswith(flag + "=") for argument in entry["argv"]),
                             f"{flag} 가 인자에 있다: {entry['argv']}")

    def test_arguments_are_the_same_fixed_list_for_any_prompt(self):
        baseline = self.fixed_arguments()
        _, _, entry = self.ask_and_get_record("a completely different question 두 번째")
        self.assertEqual(entry["argv"], baseline, "질문에 따라 인자 목록이 달라졌다")
        self.assert_prompt_not_in_arguments(entry, "a completely different question 두 번째")

    def test_hostile_prompt_goes_through_standard_input_unchanged(self):
        hostile = "a'b\"c; rm -rf / $(id) `id`\nline2 --tools Read --allowedTools Bash 한글 질문"
        baseline = self.fixed_arguments()
        _, _, entry = self.ask_and_get_record(hostile)
        self.assertEqual(entry["argv"], baseline, "질문이 인자 목록을 바꿨다")
        self.assert_prompt_not_in_arguments(entry, hostile)
        self.assert_prompt_went_through_standard_input(entry, hostile)

    def test_option_like_prompts_do_not_become_arguments(self):
        baseline = self.fixed_arguments()
        for prompt in ("--version", "--tools=Bash", "-p", '--settings={"a":1}', "--", "/context", "/help", "/"):
            with self.subTest(prompt=prompt):
                _, _, entry = self.ask_and_get_record(prompt)
                os.remove(self.record_path)
                self.assertEqual(entry["argv"], baseline, f"질문 {prompt!r} 이 인자 목록을 바꿨다")
                self.assert_prompt_went_through_standard_input(entry, prompt)

    def test_large_korean_prompt_within_length_limit_is_answered(self):
        # 본문 길이 상한(MAX_PROMPT+1024 바이트) 안에 드는 가장 큰 한글 질문 — UTF-8 로 60,000 바이트
        korean_prompt = "가" * 20_000
        status, payload, entry = self.ask_and_get_record(korean_prompt, ensure_ascii=False)
        self.assertEqual((status, payload), (200, {"answer": FAKE_ANSWER.strip()}))
        self.assert_prompt_went_through_standard_input(entry, korean_prompt)

    def test_claude_exiting_without_reading_input_follows_exit_code(self):
        # 보는 것: claude 가 표준 입력을 읽지 않고 닫은 채 끝나도 통로는 그 종료 코드를 따른다(0 → 200) — 500(예외)이 아니고
        # 다음 요청도 받는다. 보지 못하는 것: 깨진 파이프. 질문(본문 상한 약 61KB)이 파이프 버퍼(64KiB)보다 작아
        # 통로가 쓰기를 먼저 마칠 수 있으므로 EPIPE 가 생긴다고 보장되지 않는다.
        self.set_mode("noread")
        status, payload = self.ask("x" * 60_000)
        self.assertEqual((status, payload), (200, {"answer": FAKE_ANSWER.strip()}))
        self.set_mode("ok")
        self.assertEqual(self.ask()[0], 200, "입력을 읽지 않은 claude 뒤 통로가 다음 요청을 받지 못한다")

    def send_raw_prompt_body(self, body):
        headers = {"X-Bridge-Secret": TEST_SECRET, "Content-Type": "application/json", "Content-Length": str(len(body))}
        for _ in range(50):          # ask() 와 같은 까닭으로 503 이면 다시 부른다
            status, data = self.raw_request(body=body, headers=headers)
            if status != 503:
                break
            time.sleep(0.02)
        return status, data

    def test_unencodable_prompt_is_422_without_calling_claude(self):
        # JSON 이스케이프 그대로 보내 서버에서 짝 없는 대리쌍이 된다 — UTF-8 로 바꿀 수 없는 질문
        for raw_body in (rb'{"prompt":"hi \ud800"}', rb'{"prompt":"hi \udc80"}'):
            with self.subTest(body=raw_body):
                for leftover in (self.record_path, self.started_path):
                    if os.path.exists(leftover):
                        os.remove(leftover)
                launched_commands = []
                original_popen = subprocess.Popen

                class RecordingPopen(original_popen):
                    def __init__(self, arguments, *rest, **options):
                        launched_commands.append(arguments)
                        super().__init__(arguments, *rest, **options)

                with mock.patch.object(subprocess, "Popen", RecordingPopen):
                    status, data = self.send_raw_prompt_body(raw_body)
                self.assertEqual(status, 422, f"인코딩할 수 없는 질문의 응답: {status} {data!r}")
                payload = json.loads(data)
                self.assertIsInstance(payload, dict)
                self.assertIn("error", payload)
                # 띄운 뒤 거절하는 구현을 잡는다: 프로세스 생성 자체를 보고, 가짜의 시작 표식도 잠깐 기다려 본다
                self.assertEqual(launched_commands, [], "인코딩할 수 없는 질문에 claude 를 띄웠다")
                time.sleep(0.3)
                self.assertFalse(os.path.exists(self.started_path), "인코딩할 수 없는 질문에 claude 가 떴다(시작 표식)")
                self.assertEqual(self.records(), [], "인코딩할 수 없는 질문에 claude 가 불렸다")
                self.assertEqual(self.ask()[0], 200, "다음 요청이 200 이 아니다")

    def test_prompt_with_nul_is_passed_unchanged(self):
        status, data = self.send_raw_prompt_body(rb'{"prompt":"a\u0000b"}')
        self.assertEqual((status, json.loads(data)), (200, {"answer": FAKE_ANSWER.strip()}))
        entries = self.records()
        self.assertEqual(len(entries), 1)
        self.assert_prompt_went_through_standard_input(entries[0], "a\x00b")


# ---------------------------------------------------------------- 리뷰 루프 3 — 고정 머리말
class PromptLeadTest(BridgeTestCase):
    STARTING_CHARACTERS_PROMPTS = ("!echo hi", "/context", "--version", "-p", "# heading", "@/etc/hostname", "@README.md")

    def test_lead_is_non_empty_and_ends_with_newline(self):
        lead = self.prompt_lead()
        self.assertTrue(lead.strip(), "머리말이 비어 있다")
        self.assertTrue(lead.endswith("\n"), "머리말이 줄바꿈으로 끝나지 않는다 — 질문이 새 줄에서 시작해야 한다")

    def test_standard_input_is_lead_followed_by_prompt(self):
        _, _, entry = self.ask_and_get_record("plain question 한글")
        self.assert_prompt_went_through_standard_input(entry, "plain question 한글")

    def test_lead_is_the_same_for_different_prompts(self):
        lead_bytes = self.prompt_lead().encode("utf-8")
        heads = []
        for prompt in ("first question", "완전히 다른 두 번째 질문"):
            _, _, entry = self.ask_and_get_record(prompt)
            os.remove(self.record_path)
            heads.append(bytes.fromhex(entry["stdin_head_hex"])[:len(lead_bytes)])
        self.assertEqual(heads[0], heads[1], "질문에 따라 머리말이 달라졌다")
        self.assertEqual(heads[0], lead_bytes)

    def test_standard_input_does_not_start_with_command_characters(self):
        for prompt in self.STARTING_CHARACTERS_PROMPTS:
            with self.subTest(prompt=prompt):
                _, _, entry = self.ask_and_get_record(prompt)
                os.remove(self.record_path)
                first_byte = bytes.fromhex(entry["stdin_head_hex"])[:1]
                self.assertNotIn(first_byte, (b"!", b"/", b"-", b"#", b"@"),
                                 f"표준 입력의 첫 글자가 {first_byte!r} 이다(질문 {prompt!r})")
                self.assert_prompt_went_through_standard_input(entry, prompt)

    def test_lead_does_not_take_anything_from_the_prompt(self):
        lead_before = self.prompt_lead()
        distinctive = "UNIQUE-PROMPT-TOKEN-7f3a 고유한 질문"
        _, _, entry = self.ask_and_get_record(distinctive)
        self.assertEqual(self.prompt_lead(), lead_before, "요청 뒤 머리말 상수가 바뀌었다")
        self.assertNotIn("UNIQUE-PROMPT-TOKEN-7f3a", lead_before)
        self.assert_prompt_went_through_standard_input(entry, distinctive)


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

    def test_undeletable_leftover_keeps_200(self):
        self.set_mode("leave_undeletable")
        status, payload = self.ask()
        self.assertEqual((status, payload), (200, {"answer": FAKE_ANSWER.strip()}))

    def test_undeletable_leftover_keeps_504(self):
        self.set_mode("leave_undeletable_sleep")
        self.assertEqual(self.ask(), (504, {"error": "timeout"}))

    def test_two_requests_use_different_directories(self):
        statuses = [self.ask()[0], self.ask()[0]]
        self.assertEqual(statuses, [200, 200])
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

    def test_file_mentions_are_disabled_for_claude(self):
        entry = self.ask_with_bridge_environment()
        self.assertEqual(entry["file_mentions_setting"], "1", "CLAUDE_CODE_DISABLE_FILE_MENTIONS 가 1 이 아니다")

    def test_file_mentions_setting_overrides_bridge_environment(self):
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_DISABLE_FILE_MENTIONS": "0"}):
            _, _, entry = self.ask_and_get_record()
        self.assertEqual(entry["file_mentions_setting"], "1", "통로 환경의 CLAUDE_CODE_DISABLE_FILE_MENTIONS=0 이 1 로 덮이지 않았다")

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
        status, payload = self.ask("second", retry_busy=False)
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
        self.assert_prompt_went_through_standard_input(entry, "a" * 60_000)

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
