# Debugging failures

Start with [run-tests.md](run-tests.md) and the existing example [src/test/java/tests/LoginTest.java](../../src/test/java/tests/LoginTest.java).

1. Preserve the original command, scope, tool versions, timestamps and failure output before re-running.
2. Identify the failing phase: dependency resolution, compilation, discovery, setup, browser action, assertion, teardown, or reporting.
3. Follow the first relevant cause in the stack trace into the actual test/page/fixture source. Inspect the expected and actual state.
4. Inspect the run's artifacts — report locations are listed under Evidence in [run-tests.md](run-tests.md). Screenshots/attachments are not guaranteed; verify the files instead of inventing them.

Selenide may save failure diagnostics under `build/reports/tests/`; inspect the actual files before claiming screenshot capture.

## Triage
- test defect: incorrect test implementation, locator, wait, assertion or fixture behavior — including an expectation made stale by an intended application change; update the expected value to the application's current contract.
- product defect: the requester confirms the application violates its requirement. Never modify the application/SUT (including project-local files such as login.html) to force a pass; when unsure whether new behavior is intended, ask rather than guessing.
- environment issue: missing dependency/browser, incompatible version, unavailable service or denied authorization.
- test data issue: missing prerequisite account, persisted registration, replay collision or shared mutable state.
- suspected flaky behavior: collect repeated isolated runs and compare timing/state before calling it flaky or fixed.

For missing tools or access, report BLOCKED and ask for the smallest required action; do not provision infrastructure.
Make a minimal test-code fix only after evidence establishes test ownership and the task authorizes that change.
Do not weaken assertions, add arbitrary sleeps, delete evidence, alter production logic or clean server accounts as a shortcut.
Re-run the same smallest scope after a fix and report what was actually executed.

Do not introduce a failure yourself for a demonstration. If no failure exists, describe the diagnostic route as unexecuted.
