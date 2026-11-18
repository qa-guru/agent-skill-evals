# Architecture

Generated stack: Java / Gradle / JUnit 6 / Selenide.
The project contains browser tests against the configured application; no API client, mock server or separate API test layer is generated.

## System under test

- Current SUT: project-local [login.html](../../login.html), opened with a `file:` URI.
- Testing model: browser UI actions and assertions. The local HTML/JavaScript is available for contract inspection.
- Test layers:
  - manual — manual checklists
  - ui — browser UI scenarios — generated in this project

## Source map
- Build/dependencies: [build.gradle](../../build.gradle).
- Test modules: [src/test/java/tests/LoginTest.java](../../src/test/java/tests/LoginTest.java).
- No shared base/fixture file: setup is local to tests or provided by the selected runner. Inspect the linked tests.
- No Page Object layer is generated. Locators/actions remain in the tests; do not invent a new layer for one scenario.
- No shared lifecycle file is generated.
- Data/environment: [test-data.md](test-data.md).
- Test commands: [../testing/run-tests.md](../testing/run-tests.md).
- Checks placement: [../testing/assertions.md](../testing/assertions.md).
- No remote-farm contract is generated for `embedded`.

## Existing scenarios
- Successful login.

Canonical test shape: [LoginTest.successfulLoginTest](../../src/test/java/tests/LoginTest.java).
It submits the inline credentials and performs one terminal retrying text assertion on the authorized banner.
Read current source rather than copying an older locator, URL or expected message from documentation.

## Checks and synchronization
Selectors, browser operations and assertions are inline in test modules.
Reuse Selenide conditions and their retrying shouldHave/shouldBe checks.
Each check is a single terminal retrying assertion on the expected outcome — never prepend weaker precondition checks (e.g. visibility) or append state re-verification after it.
No component-object layer is generated; do not document nonexistent components.

## Configuration and CI
No CI configuration is generated.
Integration files, if present, are templates, not evidence of live TestOps/Jira/Confluence integration.
Do not import the course pack's Gradle wrappers, tags, mock environments or testE2e task: they are not configured in this project.
