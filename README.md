# agent-skill-evals

Self-healing login-test pipeline for a QA demo project
(Java / Gradle / JUnit / Selenide; the SUT is the repo-local `login.html`).

## Layout

- `login.html` — the application under test; the `en` welcome message is the
  contract the login test asserts on
- `src/test/java/tests/LoginTest.java` — the browser login test
- `tools/` — POSIX entry points (`versions`, `compile-tests`, `run-tests`,
  `git`, `heal-agent` — the LLM healer loop)
- `AGENTS.md`, `.agents/skills/`, `knowledge/` — the agent harness: operating
  contract, skills (`run-tests`, `fix-failing-test`) and knowledge docs the
  healing agent follows

## Local

```bash
sh tools/versions.sh                                  # pins: java/javac 21, gradle 9.6.0, git
sh tools/compile-tests.sh                             # offline compile
sh tools/run-tests.sh --allow-sut one login-success   # real browser run (authorized)
```

## CI — `.github/workflows/ai-pipeline.yml` (`ai-pipeline`)

Runs on every push to `main` and manually via `workflow_dispatch`; runs are
serialized per ref via `concurrency`. Four jobs, each visible as its own
stage; `test`/`heal`/`verify` share the browser-test environment via the
`test-env` composite action (Gradle dist + Selenium caches + headless):

1. **test** — `gradle test --tests 'tests.LoginTest.successfulLoginTest'`.
   A green run ends the pipeline here: zero paid calls. A red test is data,
   not a run failure — it arms the heal stage via a job output and hands
   the failure log downstream as an artifact.
2. **heal** (paid, only on red) — `tools/heal-agent.py` runs the LLM as a
   coding agent **inside the repo harness**: it reads `AGENTS.md` and the
   `fix-failing-test` skill (both injected into its prompt), opens the
   knowledge docs they reference, reproduces via `tools/run-tests.sh`,
   applies the minimal correction to `LoginTest.java` and self-verifies —
   through `read_file`, `write_file` and `run_command` on an
   OpenAI-compatible chat endpoint. Env: `OPENAI_API_KEY` (repo secret),
   optional `HEAL_API_BASE`, `HEAL_MODEL` (default `gpt-4.1-mini`). A guard
   fails the job if anything outside `LoginTest.java` changed or the file
   is untouched; the healed file leaves the job as an artifact.
3. **verify** — a fresh runner applies only the artifact file and runs
   `gradle cleanTest test`. The rerun is the sole authority — the agent's
   report never counts; red stays red: the SUT itself is broken.
4. **commit** — only on verified green: `github-actions[bot]` commits the
   healed test to `main` with `[skip ci]`.

Edit `login.html`, push: green when the agent can honestly heal the test,
red when the SUT no longer provides what the scenario needs.
