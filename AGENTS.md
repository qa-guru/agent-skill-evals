# QA automation agent

One JUnit 6 / Selenide test covers successful login on the local `login.html` fixture.
Respond in English.

## Skills
- [Run existing tests](.agents/skills/run-tests/SKILL.md).
- [Diagnose and fix a failing test](.agents/skills/fix-failing-test/SKILL.md).

If your client does not discover `.agents/skills/`, read the relevant `SKILL.md` directly.

## References
- [Commands and prerequisites](knowledge/testing/run-tests.md): read before running any test.
- [Project map](knowledge/architecture/overview.md) and [test data](knowledge/architecture/test-data.md).
- [Assertions](knowledge/testing/assertions.md) and [failure diagnosis](knowledge/testing/debugging.md).
- [Version sources](knowledge/stack/versions.md).

## Safeguards
- Read the failing test and the relevant application or fixture first. Preserve the test's intent and style. For the login lesson, that means inline Selenide steps and one retrying assertion.
- Do not add dependencies, sleeps, or weaker assertions to get a pass. Do not edit the fixture to repair a test.
- Ask before downloads, installs, browser execution, external SUT access, CI jobs, uploads, integration writes, or destructive cleanup.
- Preserve other work and failure evidence. Do not expose secrets or commit/push without an explicit request.
- Use the smallest authorized scope. Report the command, versions, exit code, and executed/passed/failed/skipped counts.
- Compilation is not a test run. If blocked, name the missing prerequisite or permission instead of repairing infrastructure.
