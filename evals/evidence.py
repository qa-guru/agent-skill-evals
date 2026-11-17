"""Checks the observed Codex JSONL schema and this project's small test fixture."""

import json
import re
import shlex
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def invocations(command):
    """Recognize direct commands, shell -c wrappers and simple shell lists."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    parts = [[]]
    for token in lexer:
        if token and all(char in ";&|\n" for char in token):
            parts.append([])
        else:
            parts[-1].append(token)
    for args in parts:
        while args and (args[0] in {"command", "exec", "env"} or re.match(r"^\w+=", args[0])):
            args = args[1:]
        if not args:
            continue
        if Path(args[0]).name in {"sh", "bash", "zsh"}:
            option = next((i for i, arg in enumerate(args[1:], 1) if arg.startswith("-") and "c" in arg), None)
            if option is not None:
                if option + 1 >= len(args):
                    raise ValueError("shell -c has no command")
                yield from invocations(args[option + 1])
                continue
            args = args[1:]
            while args and args[0].startswith("-"):
                args = args[1:]
        if args:
            yield args


def command_actions(item, completed):
    actions = []
    output = item.get("aggregated_output", "")
    login_run = False
    for args in invocations(item["command"]):
        program = args[0].removeprefix("./")
        script = re.search(r"(?:^|/)tools/(run-tests|versions|compile-tests)\.sh$", program)
        if script:
            name = script[1]
            if name == "versions" and completed:
                actions.append("versions")
            elif name == "compile-tests" and completed and "Compilation/collection completed;" in output:
                actions.append("compile")
            elif name == "run-tests":
                if args[1:] == ["list"] and completed:
                    if "login-success [login] Successful login" in output.splitlines():
                        actions.append("list")
                if "--allow-sut" in args[1:]:
                    actions.append("test")
                    login_run |= args[1:] == ["--allow-sut", "one", "login-success"]
        elif Path(program).name in {"gradle", "gradlew"}:
            if any(arg.rsplit(":", 1)[-1] == "test" for arg in args[1:]):
                actions.append("test")
    if login_run and completed:
        for section in re.split(r"(?m)(?=^\+ gradle )", output):
            if not section.startswith("+ gradle --offline test --tests 'tests.LoginTest.successfulLoginTest'\n"):
                continue
            if "1 test completed, 1 failed" in section and "ElementShould" in section:
                actions.append("login-failure")
            elif "BUILD SUCCESSFUL" in section:
                actions.append("login-pass")
    return actions


def extract(out):
    for name in ("commands.txt", "actions.txt", "report.txt"):
        (out / name).write_text("", encoding="utf-8")
    events = [json.loads(line) for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    if not all(isinstance(event, dict) for event in events):
        raise ValueError("event must be a JSON object")
    types = {event.get("type") for event in events}
    if not {"thread.started", "turn.started", "turn.completed"} <= types or types & {"error", "turn.failed"}:
        raise ValueError("missing successful session lifecycle; not a validated agent run")
    commands = {}
    messages = []
    for event in events:
        if event["type"] not in {"item.started", "item.completed"}:
            continue
        item = event["item"]
        kind = item["type"]
        if kind == "command_execution":
            if not isinstance(item["command"], str) or not isinstance(item["id"], str):
                raise ValueError("invalid command item")
            completed = event["type"] == "item.completed"
            if completed and (type(item["exit_code"]) is not int or item["status"] not in {"completed", "failed"}):
                raise ValueError("invalid command completion")
            commands[item["id"]] = (item, completed)
        elif kind == "agent_message" and event["type"] == "item.completed":
            messages.append(item["text"])
        elif kind not in {"agent_message", "file_change", "reasoning", "plan", "todo_list"}:
            raise ValueError(f"unverified item type: {kind}")
    report = (out / "last-message.txt").read_text(encoding="utf-8")
    if not report.strip() or not messages or report.rstrip("\n") != messages[-1].rstrip("\n"):
        raise ValueError("missing or inconsistent final message")
    actions = []
    for item, completed in commands.values():
        actions.extend(command_actions(item, completed))
    (out / "commands.txt").write_text("".join(item["command"] + "\n" for item, _ in commands.values()), encoding="utf-8")
    (out / "actions.txt").write_text("".join(action + "\n" for action in actions), encoding="utf-8")
    (out / "report.txt").write_text(report, encoding="utf-8")


def check_source(expected, actual, test, sut=None):
    def files(root):
        paths = {}
        for path in root.rglob("*"):
            if path.is_symlink():
                raise ValueError("symlink in source tree")
            if path.is_file():
                paths[path.relative_to(root).as_posix()] = path.read_bytes()
        return paths

    before, after = files(expected), files(actual)
    if before.keys() != after.keys() or test not in before:
        raise ValueError("source files added, removed or missing")
    # Preserve literals, identifiers and comments; ignore formatting whitespace only.
    tokens = r'"(?:\\.|[^"\\])*"|[A-Za-z_$][\w$]*|\d+|[^\s]'
    for path in before:
        if path == test:
            want = before[path].decode()
            if sut is not None:
                # The SUT is the contract: derive the expected literal from
                # login.html and the login used by the test, not from the
                # committed source, which may legitimately be stale.
                welcome = re.search(r"en:\s*\{\s*welcome:\s*'([^']*)'", sut.read_text(encoding="utf-8"))
                login = re.search(r'login-input[^;]*?setValue\("([^"]*)"\)', want)
                literal = r'text\("(?:\\.|[^"\\])*"\)'
                if not welcome or not login or len(re.findall(literal, want)) != 1:
                    raise ValueError("cannot derive expected literal from SUT and test")
                expected_literal = re.sub(r"\{[A-Za-z_]+\}", login.group(1), welcome.group(1))
                want = re.sub(literal, lambda _: f'text("{expected_literal}")', want, count=1)
            if re.findall(tokens, want) != re.findall(tokens, after[path].decode()):
                raise ValueError("test is not the minimal stale-text correction")
        elif before[path] != after[path]:
            raise ValueError(f"unexpected source change: {path}")


def check_results(actions_path, xml):
    actions = actions_path.read_text(encoding="utf-8").splitlines()
    if "login-failure" not in actions or "login-pass" not in actions[actions.index("login-failure") + 1:]:
        raise ValueError("agent did not demonstrate a failing assertion followed by a successful run")
    suite = ET.parse(xml).getroot()
    counts = tuple(int(suite.get(key, "0")) for key in ("tests", "failures", "errors", "skipped"))
    cases = suite.findall("testcase")
    if suite.tag != "testsuite" or suite.get("name") != "tests.LoginTest" or counts != (1, 0, 0, 0):
        raise ValueError(f"expected one passing, non-skipped login test; got {counts}")
    if len(cases) != 1 or cases[0].get("name") != "successfulLoginTest()" or cases[0].get("classname") != "tests.LoginTest":
        raise ValueError("unexpected JUnit selection")
    if any(cases[0].find(tag) is not None for tag in ("failure", "error", "skipped")):
        raise ValueError("JUnit testcase did not pass")
    print("Executed/passed/failed/skipped: 1/1/0/0")


def check_verdict(path):
    text = path.read_text(encoding="utf-8")
    verdicts = re.findall(r"(?m)^VERDICT:[ \t]*(PASS|FAIL|UNCLEAR)[ \t]*$", text)
    if len(verdicts) != 1:
        raise ValueError(f"expected exactly one VERDICT line, got {len(verdicts)}")
    if not re.search(r"(?m)^RUBRIC[ \t]+\S", text):
        raise ValueError("no per-item RUBRIC lines")
    if verdicts[0] != "PASS":
        raise ValueError(f"judge verdict is {verdicts[0]}")
    print("judge verdict: PASS")


def main():
    try:
        mode, *args = sys.argv[1:]
        if mode == "extract" and len(args) == 1:
            extract(Path(args[0]))
        elif mode == "source" and len(args) in (3, 4):
            check_source(Path(args[0]), Path(args[1]), args[2], Path(args[3]) if len(args) == 4 else None)
        elif mode == "results" and len(args) == 2:
            check_results(Path(args[0]), Path(args[1]))
        elif mode == "verdict" and len(args) == 1:
            check_verdict(Path(args[0]))
        else:
            raise ValueError(
                "usage: evidence.py extract OUT | source EXPECTED ACTUAL TEST [SUT_HTML] | results ACTIONS XML | verdict JUDGE_MESSAGE"
            )
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
        print(f"FAIL evidence: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
