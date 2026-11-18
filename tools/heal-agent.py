#!/usr/bin/env python3
"""LLM agent healer — runs inside the repo harness (AGENTS.md, skills,
knowledge, tools/*) instead of a bare one-shot completion.

The model gets three tools — read_file, write_file, run_command — and
works the fix-failing-test skill like a coding agent: open the skill doc,
pull the knowledge pages it references, reproduce via tools/run-tests.sh,
apply the minimal correction, re-run to verify. The workflow's independent
browser rerun is still the final authority.

Env: OPENAI_API_KEY (required)
     HEAL_API_BASE  — default https://api.openai.com/v1
     HEAL_MODEL     — default gpt-4.1-mini
     HEAL_MAX_ITERS — default 25
Usage: python3 tools/heal-agent.py <failure-log>
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEST_REL = "src/test/java/tests/LoginTest.java"
TEST = ROOT / TEST_REL
MAX_ITERS = int(os.environ.get("HEAL_MAX_ITERS", "25"))

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file inside the repository workspace.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Repo-relative path"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": f"Overwrite a file. The ONLY writable path is {TEST_REL}.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string", "description": "Complete new file content"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a POSIX shell command in the repo root — tools/*.sh wrappers, gradle, grep.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
]


def resolve(p):
    try:
        r = (ROOT / p).resolve()
        r.relative_to(ROOT)
        return r
    except (ValueError, OSError):
        return None


def exec_tool(name, args):
    if name == "read_file":
        f = resolve(args.get("path", ""))
        if f is None or not f.is_file():
            return f"ERROR: cannot read {args.get('path')}"
        return f.read_text(encoding="utf-8", errors="replace")[:40000]
    if name == "write_file":
        if args.get("path") != TEST_REL:
            return f"ERROR: write allowed only to {TEST_REL}"
        TEST.write_text(args["content"], encoding="utf-8")
        return f"wrote {TEST_REL} ({len(args['content'])} chars)"
    if name == "run_command":
        try:
            p = subprocess.run(
                ["sh", "-c", args["command"]],
                cwd=ROOT, capture_output=True, text=True, timeout=180,
            )
            out = (p.stdout + p.stderr)[-8000:]
            return f"exit={p.returncode}\n{out}"
        except subprocess.TimeoutExpired:
            return "ERROR: command timed out after 180s"
    return f"ERROR: unknown tool {name}"


def chat(base, key, model, messages):
    body = {
        "model": model,
        "temperature": 0.2,
        "messages": messages,
        "tools": TOOLS,
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())["choices"][0]["message"]
    except urllib.error.HTTPError as e:
        sys.exit(f"LLM request failed: HTTP {e.code} {e.read()[:400]!r}")


def main():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("BLOCKED: OPENAI_API_KEY not set")
    base = os.environ.get("HEAL_API_BASE", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("HEAL_MODEL", "gpt-4.1-mini")
    fail_log = sys.argv[1] if len(sys.argv) > 1 else ""

    system = f"""You are the QA automation agent working inside this repository.
Your operating contract is AGENTS.md:

<AGENTS.md>
{(ROOT / 'AGENTS.md').read_text(encoding='utf-8')}
</AGENTS.md>

The browser test tests.LoginTest.successfulLoginTest just failed. Work the
fix-failing-test skill end to end, using the tools provided:
- read_file — the skill doc, the knowledge pages it references, login.html,
  the failing test, {fail_log}
- run_command — tools/*.sh wrappers and gradle test runs
- write_file — the minimal correction; the ONLY writable path is {TEST_REL}

The SUT is the contract: never modify login.html. Do not weaken assertions.
Verify by re-running the test yourself before finishing.
Final message: classification, what you changed, verification result."""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "Heal the failing login test. The failure log is at " + fail_log},
    ]

    for i in range(MAX_ITERS):
        msg = chat(base, key, model, messages)
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            print(msg.get("content", "(empty final message)"))
            return
        for c in calls:
            name = c["function"]["name"]
            try:
                args = json.loads(c["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            print(f"[{i}] {name}({json.dumps(args)[:120]})", flush=True)
            messages.append({
                "role": "tool",
                "tool_call_id": c["id"],
                "content": exec_tool(name, args),
            })
    sys.exit(f"agent did not finish within {MAX_ITERS} iterations")


if __name__ == "__main__":
    main()
