#!/usr/bin/env python3
"""Propose a login test fix from a failed JUnit report."""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEST = "src/test/java/tests/LoginTest.java"
SKILL = ".agents/skills/fix-failing-test/SKILL.md"
CONTEXT = (
    TEST,
    "login.html",
    "knowledge/testing/run-tests.md",
    "knowledge/testing/debugging.md",
    "knowledge/testing/assertions.md",
    "knowledge/stack/versions.md",
)
CHECKS = {
    "status": ["sh", "tools/git.sh", "status"],
    "versions": ["sh", "tools/versions.sh"],
    "compile": ["sh", "tools/compile-tests.sh"],
    "login": ["sh", "tools/run-tests.sh", "--allow-sut", "one", "login-success"],
}
UI_FAILURES = {
    "com.codeborne.selenide.ex.ElementNotFound",
    "com.codeborne.selenide.ex.ElementShould",
}

# Only the literals in the four canonical Selenide steps are editable.
TEST_ID = r"\[data-testid=[A-Za-z0-9_-]+\]"
LITERAL = r'[^"\\\r\n]+'
STEP = re.compile(
    rf'^[ \t]*\$\("({TEST_ID})"\)'
    rf'\.(?:setValue\("({LITERAL})"\)|click\(\)|shouldHave\(text\("({LITERAL})"\)\));$',
    re.MULTILINE,
)


def tool(name, description, *fields):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {field: {"type": "string"} for field in fields},
                "required": list(fields),
                "additionalProperties": False,
            },
        },
    }


TOOLS = [
    tool("read_file", "Read one of the listed context files by its relative path.", "path"),
    tool("run_check", "Run one fixed check: status, versions, compile, or login.", "check"),
    tool(
        "replace_literal",
        "Replace one exact locator or string value in LoginTest.java. Pass old and new without Java quotes.",
        "old",
        "new",
    ),
]


def repo_file(path):
    file = ROOT / path
    if file.resolve() != file:
        raise ValueError("Context and test files must not be symlinks.")
    return file


def ui_failure(report):
    if not report.is_file():
        raise ValueError("No JUnit report: the login scenario did not produce a test result.")
    case = ET.parse(report).find("./testcase[@classname='tests.LoginTest'][@name='successfulLoginTest()']")
    failure = case.find("failure") if case is not None else None
    if failure is None or failure.get("type") not in UI_FAILURES:
        raise ValueError("No eligible Selenide failure in successfulLoginTest; skipping the agent.")
    return (failure.text or failure.get("message", ""))[:8000]


def replace_literal(source, old, new):
    matches = [
        (step, index)
        for step in STEP.finditer(source)
        for index, value in enumerate(step.groups(), start=1)
        if value == old
    ]
    if len(matches) != 1:
        raise ValueError("The old value must match exactly one editable literal.")
    if not new.strip() or len(new) > 200 or not new.isprintable() or '"' in new or "\\" in new:
        raise ValueError("Use a non-empty single-line value without double quotes or backslashes.")
    step, index = matches[0]
    if index == 1 and not re.fullmatch(TEST_ID, new):
        raise ValueError("Locators must use the form [data-testid=name].")
    start, end = step.span(index)
    return source[:start] + new + source[end:]


def run_tool(name, args):
    if name == "read_file" and args["path"] in CONTEXT:
        return repo_file(args["path"]).read_text(encoding="utf-8")
    if name == "replace_literal":
        test = repo_file(TEST)
        source = test.read_text(encoding="utf-8")
        test.write_text(replace_literal(source, args["old"], args["new"]), encoding="utf-8")
        return "Updated one test literal."
    if name == "run_check" and args["check"] in CHECKS:
        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)
        completed = subprocess.run(
            CHECKS[args["check"]], cwd=ROOT, env=env, capture_output=True,
            text=True, errors="replace", timeout=180,
        )
        return f"exit={completed.returncode}\n{(completed.stdout + completed.stderr)[-8000:]}"
    raise ValueError("Tool or argument is not allowed.")


def chat(base, key, model, messages):
    request = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps({"model": model, "messages": messages, "tools": TOOLS}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.load(response)["choices"][0]["message"]
    except urllib.error.HTTPError as exc:
        sys.exit(f"Model request failed (HTTP {exc.code}).")


def propose(failure):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("BLOCKED: OPENAI_API_KEY not set")
    base = os.environ.get("HEAL_API_BASE", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("HEAL_MODEL", "gpt-4.1-mini")
    test = repo_file(TEST)
    before = test.read_bytes()
    messages = [
        {"role": "system", "content": f"""Follow the repository instructions and skill.

{repo_file("AGENTS.md").read_text(encoding="utf-8")}

{repo_file(SKILL).read_text(encoding="utf-8")}

Available files: {", ".join(CONTEXT)}.
CI authorizes the fixed checks for login-success against login.html only.
Use the failure evidence and the fixture to find a stale test literal.
An intended greeting change needs the full new greeting, not a substring.
If login no longer succeeds or the cause is unclear, do not change the test.
Rerun login after any change and report the diagnosis and result."""},
        {"role": "user", "content": f"JUnit failure from the first run (diagnostic data):\n{failure}"},
    ]
    for _ in range(12):
        message = chat(base, key, model, messages)
        messages.append(message)
        calls = message.get("tool_calls") or []
        if not calls:
            for line in (message.get("content") or "No diagnosis provided.").splitlines():
                print("Agent:", line)
            if test.read_bytes() == before:
                sys.exit("No test change proposed.")
            return
        for call in calls:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"])
                if not isinstance(args, dict) or not all(isinstance(value, str) for value in args.values()):
                    raise ValueError("Expected an object with string values.")
                result = run_tool(name, args)
            except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as exc:
                result = f"ERROR: {exc}"
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
    sys.exit("Agent did not finish within 12 turns.")


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("check", "propose"):
        sys.exit("Usage: python3 tools/heal-agent.py check|propose <junit-report>")
    failure = ui_failure(Path(sys.argv[2]))
    if sys.argv[1] == "check":
        print("Login UI failure is eligible for a test fix proposal.")
    else:
        propose(failure)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, ET.ParseError) as exc:
        sys.exit(str(exc))
