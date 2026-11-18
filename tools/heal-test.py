#!/usr/bin/env python3
"""One-shot LLM healer for LoginTest.java.

Reads the SUT (login.html), the failing test and the browser failure log,
asks an OpenAI-compatible chat endpoint for the corrected test file, and
writes it back. The caller re-runs the real browser test afterwards — the
model's output is never trusted without verification.

Env: OPENAI_API_KEY (required)
     HEAL_API_BASE — default https://api.openai.com/v1
     HEAL_MODEL    — default gpt-4.1-mini
Usage: python3 tools/heal-test.py <failure-log> [<previous-attempt-log>]
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUT = ROOT / "login.html"
TEST = ROOT / "src/test/java/tests/LoginTest.java"


def read(p):
    return Path(p).read_text(encoding="utf-8", errors="replace")


def main():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("BLOCKED: OPENAI_API_KEY not set")
    base = os.environ.get("HEAL_API_BASE", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("HEAL_MODEL", "gpt-4.1-mini")
    fail_log = read(sys.argv[1]) if len(sys.argv) > 1 else ""
    prev_log = read(sys.argv[2]) if len(sys.argv) > 2 else ""

    prompt = f"""The browser test tests.LoginTest.successfulLoginTest just failed.

<SUT contract: login.html — the source of truth, never modified>
{read(SUT)}
</SUT>

<current test: src/test/java/tests/LoginTest.java>
{read(TEST)}
</current>

<failure log>
{fail_log[-4000:]}
</failure log>
"""
    if prev_log:
        prompt += f"""
<your previous fix still failed, new failure log — fix again>
{prev_log[-4000:]}
</previous attempt>
"""
    prompt += """
Task: return the COMPLETE corrected LoginTest.java.
- Fix only what is stale versus the SUT contract: element selectors
  (data-testid), credentials, the expected message. Determine the real
  contract from the SUT's own markup and JavaScript, not from the old test.
- Keep the scenario shape: fill the login field, fill the password field,
  click submit, assert the success banner text.
- Do not weaken assertions. If no honest test can pass because the SUT
  itself is broken, still return the best-matching file — verification
  decides the outcome.
- Output ONLY the file content: no prose, no markdown fences.
"""

    body = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "You are a precise test-healing engine. You output only complete source files."},
            {"role": "user", "content": prompt},
        ],
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"LLM request failed: HTTP {e.code} {e.read()[:400]!r}")

    content = data["choices"][0]["message"]["content"]
    fence = re.search(r"```(?:java)?\s*(.*?)```", content, re.S)
    if fence:
        content = fence.group(1)
    content = content.strip()
    if "class LoginTest" not in content or "shouldHave" not in content:
        sys.exit(f"LLM output is not a valid LoginTest.java: {content[:200]!r}")

    TEST.write_text(content + "\n", encoding="utf-8")
    print(f"healed LoginTest.java via {model}")


if __name__ == "__main__":
    main()
