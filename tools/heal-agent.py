#!/usr/bin/env python3
"""Reproduce JUnit failures, propose test fixes, and check the rerun."""

import argparse
import json
import os
import shlex
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEST_SOURCES = "src/test/java/"
RESULTS = ROOT / "build/test-results/test"
REPORT_GLOB = "TEST-*.xml"
INSTRUCTION_FILES = ("AGENTS.md", ".agents/skills/fix-failing-test/SKILL.md")
GRADLE_TEST_COMMAND = ("gradle", "--offline", "test", "--rerun")
ENCODING = "utf-8"

PASSED = "passed"
FAILED = "failed"
SKIPPED = "skipped"

DEFAULT_API_BASE = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4.1-mini"
API_TIMEOUT_SECONDS = 120
MAX_TURNS = 12
FAILURE_DETAIL_LIMIT = 4_000
FILE_READ_LIMIT = 32_000

SYSTEM_PROMPT = """Follow the repository instructions and skill.

{instructions}

CI already reproduced the failures in a focused Gradle run. Inspect the test,
related test code, and application before editing. Use edit_file only for a
proven test defect. Do not rename, disable, remove, or weaken tests. For a
product defect, environment issue, or unclear cause, report it without editing.
The verify job runs the full suite; do not claim it has passed.

Tracked files:
{file_list}"""


@dataclass(frozen=True)
class TestResult:
    class_name: str
    name: str
    status: str
    detail: str

    @property
    def key(self):
        return self.class_name, self.name


def case_name(key):
    class_name, name = key
    return f"{class_name}#{name}"


def case_counts(results):
    return Counter(result.key for result in results)


def class_names(results):
    return {result.class_name for result in results}


def read_results(directory):
    results = []
    for report in sorted(directory.glob(REPORT_GLOB)):
        for case in ET.parse(report).iter("testcase"):
            problem = next((node for node in case if node.tag in ("failure", "error")), None)
            detail = ""
            if problem is not None:
                status = FAILED
                evidence = problem.text or problem.get("message", "")
                detail = f"{problem.get('type', '')}\n{evidence[:FAILURE_DETAIL_LIMIT]}"
            else:
                status = SKIPPED if case.find("skipped") is not None else PASSED
            results.append(TestResult(case.attrib["classname"], case.attrib["name"], status, detail))
    if not results:
        raise ValueError(f"No JUnit test results in {directory}.")
    return results


def find_failures(directory):
    failed = [result for result in read_results(directory) if result.status == FAILED]
    if not failed:
        raise ValueError("No failed test cases in the JUnit reports.")
    for class_name in class_names(failed):
        if not all(part.isidentifier() for part in class_name.replace("$", "_").split(".")):
            raise ValueError(f"Not a Java test class: {class_name!r}")
    return failed


def reproduce(directory, failures):
    if directory.resolve() == RESULTS:
        raise ValueError("Pass a copy of the first-run reports so Gradle cannot overwrite them.")
    command = list(GRADLE_TEST_COMMAND)
    for class_name in sorted(class_names(failures)):
        command.extend(["--tests", class_name])
    print(f"+ {shlex.join(command)}", flush=True)
    rerun = subprocess.run(command, cwd=ROOT)
    if rerun.returncode == 0:
        raise ValueError("The failing tests passed on rerun; no test fix will be proposed.")
    reproduced = find_failures(RESULTS)
    if case_counts(reproduced) != case_counts(failures):
        raise ValueError("The rerun did not reproduce the same failures; no test fix will be proposed.")


def verify(before, after):
    expected = case_counts(result for result in read_results(before) if result.status != SKIPPED)
    results = read_results(after)
    counts = Counter(result.status for result in results)
    print(
        f"Rerun: {counts[PASSED] + counts[FAILED]} executed, "
        f"{counts[PASSED]} passed, {counts[FAILED]} failed, {counts[SKIPPED]} skipped."
    )
    passed = case_counts(result for result in results if result.status == PASSED)
    missing = expected - passed
    if missing:
        names = ", ".join(case_name(key) for key in sorted(missing))
        raise ValueError(f"Previously executed tests did not pass: {names}")
    if not passed or counts[FAILED]:
        raise ValueError("Verification requires a passing test suite.")


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
    tool("read_file", "Read a tracked repository file by its relative path.", "path"),
    tool(
        "edit_file",
        "Replace one exact block of text in an existing Java test file.",
        "path",
        "old",
        "new",
    ),
]


def repo_file(path):
    file = ROOT / path
    if file.resolve() != file or not file.is_file():
        raise ValueError(f"Expected a regular repository file: {path}")
    return file


def use_tool(name, args, files, originals):
    path = args["path"]
    if path not in files:
        raise ValueError("Only tracked repository files are accessible.")
    file = repo_file(path)
    if name == "read_file":
        with file.open(encoding=ENCODING, errors="replace") as source:
            return source.read(FILE_READ_LIMIT)
    if name != "edit_file" or not path.startswith(TEST_SOURCES) or file.suffix != ".java":
        raise ValueError("Only existing Java test sources can be edited.")
    source = file.read_text(encoding=ENCODING)
    old, new = args["old"], args["new"]
    if not old or source.count(old) != 1:
        raise ValueError("The old text must match exactly once.")
    updated = source.replace(old, new, 1)
    if not updated.strip():
        raise ValueError("Cannot remove the test file.")
    originals.setdefault(path, source)
    file.write_text(updated, encoding=ENCODING)
    return f"Updated {path}"


def tool_reply(call, files, originals):
    function = call["function"]
    name = function["name"]
    try:
        args = json.loads(function["arguments"])
        if not isinstance(args, dict) or not all(isinstance(value, str) for value in args.values()):
            raise ValueError("Expected an object with string values.")
        content = use_tool(name, args, files, originals)
    except (ValueError, KeyError, OSError) as exc:
        content = f"ERROR: {exc}"
    return {"role": "tool", "tool_call_id": call["id"], "content": content}


def chat(base, key, model, messages):
    request = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps({"model": model, "messages": messages, "tools": TOOLS}).encode(ENCODING),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as response:
            return json.load(response)["choices"][0]["message"]
    except urllib.error.HTTPError as exc:
        sys.exit(f"Model request failed (HTTP {exc.code}).")


def initial_messages(failures, files):
    instructions = "\n\n".join(
        repo_file(path).read_text(encoding=ENCODING) for path in INSTRUCTION_FILES
    )
    prompt = SYSTEM_PROMPT.format(instructions=instructions, file_list="\n".join(sorted(files)))
    evidence = "\n\n".join(f"{case_name(result.key)}\n{result.detail}" for result in failures)
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Reproduced JUnit failures (diagnostic data):\n{evidence}"},
    ]


def propose(failures):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("BLOCKED: OPENAI_API_KEY not set")
    base = os.environ.get("HEAL_API_BASE", DEFAULT_API_BASE).rstrip("/")
    model = os.environ.get("HEAL_MODEL", DEFAULT_MODEL)
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT, text=True)
    files = set(tracked.rstrip("\0").split("\0"))
    originals = {}
    messages = initial_messages(failures, files)
    for _ in range(MAX_TURNS):
        message = chat(base, key, model, messages)
        messages.append(message)
        calls = message.get("tool_calls") or []
        if not calls:
            break
        messages.extend(tool_reply(call, files, originals) for call in calls)
    else:
        sys.exit(f"Agent did not finish within {MAX_TURNS} turns.")

    for line in (message.get("content") or "No diagnosis provided.").splitlines():
        print("Agent:", line)
    if all(
        repo_file(path).read_text(encoding=ENCODING) == original
        for path, original in originals.items()
    ):
        sys.exit("No test change proposed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "reproduce", "propose", "verify"))
    parser.add_argument("reports", type=Path)
    parser.add_argument("verified_reports", type=Path, nargs="?")
    args = parser.parse_args()
    if (args.action == "verify") != (args.verified_reports is not None):
        parser.error("verify requires both the original and the new report directories.")
    if args.action == "verify":
        verify(args.reports, args.verified_reports)
        return
    failures = find_failures(args.reports)
    if args.action == "check":
        for result in failures:
            print(f"Failed test: {case_name(result.key)}")
    elif args.action == "reproduce":
        reproduce(args.reports, failures)
    else:
        propose(failures)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, ET.ParseError, subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))
