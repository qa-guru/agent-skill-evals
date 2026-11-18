# Test data and environment

Fixed inputs and expected messages are inline in [src/test/java/tests/LoginTest.java](../../src/test/java/tests/LoginTest.java).
No runtime data generator file is emitted for this selection.

## Lifecycle and isolation
Follow the lifecycle in the test modules and the selected runner's built-in fixtures.
Closing the browser is not server-side cleanup. No account deletion, database reset or API cleanup fixture is generated.
Registration changes persistent application data; a repeated username may already exist. Do not delete users or weaken expected results to obtain a pass.
Do not assume parallel isolation or a clean database; establish the actual SUT state before diagnosing a data failure.

## Environment
Current target: project-local [login.html](../../login.html), opened with a `file:` URI.
Configuration locations: [src/test/java/tests/LoginTest.java](../../src/test/java/tests/LoginTest.java).
The harness adds no BASE_URL env override, dotenv loader, Docker stand or remote-browser service.
Before changing a target, inspect the linked configuration. A local browser-test request does not authorize switching to an external SUT.
External targets require separate authorization; the scope wrapper still requires `--allow-sut` for the selected local or external target.
Keep secrets in approved environment/CI secret storage; never copy credentials or tokens into knowledge files.
