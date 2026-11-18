# agent-skill-evals

Self-healing login-test pipeline for a QA demo project
(Java / Gradle / JUnit / Selenide; the SUT is the repo-local `login.html`).

## Layout

- `login.html` — the application under test; the `en` welcome message is the
  contract the login test asserts on
- `src/test/java/tests/LoginTest.java` — the browser login test
- `tools/` — POSIX entry points (`versions`, `compile-tests`, `run-tests`)

## Local

```bash
sh tools/versions.sh                                  # pins: java/javac 21, gradle 9.6.0, git
sh tools/compile-tests.sh                             # offline compile
sh tools/run-tests.sh --allow-sut one login-success   # real browser run (authorized)
```

## CI — `.github/workflows/ai-pipeline.yml` (`ai-pipeline`)

Runs on every push to `main` and manually via `workflow_dispatch`; runs are
serialized per ref via `concurrency`.

One job (Java + pinned Gradle 9.6.0; the Gradle dist, dependency/Selenium
caches and the Codex CLI are restored via `actions/cache`):

1. **First pass** — `gradle test --tests 'tests.LoginTest.successfulLoginTest'`
   runs the real browser login flow. A green run ends here: zero paid calls,
   nothing to heal.
2. **Heal** (paid, only on red) — the Codex agent reads `login.html`, the
   test and the failure log, and minimally rewrites **only**
   `LoginTest.java` so it matches what the SUT now provides — renamed
   selectors, new credentials, new copy, restructured markup. Because the
   agent reasons over the live contract, it is not limited to a fixed list
   of patterns. Requires the `OPENAI_API_KEY` (or `CODEX_ACCESS_TOKEN`)
   repository secret.
3. **Verify** — the same browser test is re-run independently. Green → the
   healed file is committed back as `github-actions[bot]` with `[skip ci]`.
   A guard fails the run if the agent touched anything outside
   `LoginTest.java`, and a red rerun stays red — the SUT itself is broken.

Edit `login.html`, push: green when the agent can honestly heal the test,
red when the SUT no longer provides what the scenario needs.
