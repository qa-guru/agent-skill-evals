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
serialized per ref via `concurrency`. A `schedule` block is present but
commented out — uncomment deliberately.

One job, one toolchain (Java + pinned Gradle 9.6.0; the distribution and the
dependency/Selenium caches are restored via `actions/cache`):

1. **Sync** — renders the expected welcome text from `login.html` (the `en`
   template with the test's login, whitespace normalized like DOM `getText`),
   writes it into `LoginTest.java`, and commits the change back as
   `github-actions[bot]` with `[skip ci]` — no second pipeline pass, the
   browser run below already verifies the synced file.
2. **Verify** — `gradle test --tests 'tests.LoginTest.successfulLoginTest'`
   runs the real browser login flow against the SUT; it also warms the Gradle
   runtime classpath and `~/.cache/selenium` on a cold cache.

Edit `login.html`, push, and the run stays green while `LoginTest.java`
catches up by itself. A failure after the sync means the login flow itself is
broken — that is an honest red, not a stale expectation.
