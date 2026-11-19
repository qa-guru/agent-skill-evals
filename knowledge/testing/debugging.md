# Debugging failures

1. Before rerunning, record the command, scope, versions, and failure output.
2. Find the first failing phase: dependency resolution, compilation, discovery,
   browser startup, UI action, assertion, or teardown.
3. Compare the [test](../../src/test/java/tests/LoginTest.java) and
   [fixture](../../login.html) with the expected and actual values in the
   [reports](run-tests.md#evidence). Check whether a Selenide screenshot exists
   under `build/reports/tests/` before reporting one.

## Classify Before Changing Anything

- **Test defect:** a stale locator, demo credential, or greeting after an
  intended change. Fix the smallest proven mismatch in the test.
- **Product defect:** valid credentials no longer produce a successful login.
  Keep the test red and report the regression. Ask if the intended behavior is unclear.
- **Environment or data issue:** missing dependency or driver, incompatible
  version, or unavailable prerequisite data. Report what's missing.
- **Suspected flake:** compare repeated runs of the same scope before calling
  the issue intermittent or fixed.

After an authorized test fix, rerun the same scope and report what executed.
Do not manufacture a failure, change the fixture, or weaken the assertion as
part of diagnosing a failing test.
