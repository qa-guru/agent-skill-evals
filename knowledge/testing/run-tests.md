# Running tests

POSIX shell commands, run from the project root.
Opening the project does not install dependencies, launch services or run tests. Commands execute only when explicitly called.

## Prerequisites and permissions
Read [../stack/versions.md](../stack/versions.md) and verify the installed versions:
```bash
java -version
javac -version
gradle --version
git --version
```
Verify dependencies, browser/driver availability and SUT readiness before execution; first use may download or resolve them — ask before installs/downloads, network access or environment repair.
The current SUT is local `login.html`. Browser execution requires approval for the selected scope; external SUT access additionally requires explicit authorization. Registration, if added, writes persistent server data.

## Tools
Run the scripts with `sh` — no exec bit needed; POSIX sh and standard Unix file/text utilities required, PowerShell unsupported.
The LLM healing agent additionally needs Python 3.9+ (standard library only) and `OPENAI_API_KEY` in the environment.
Scripts resolve the project root relative to themselves, including paths with spaces.
- [tools/versions.sh](../../tools/versions.sh): verify selected CLI pins. Git has no separate pin; only its availability/version command is checked.
- [tools/compile-tests.sh](../../tools/compile-tests.sh): compile or collect, never a browser-test PASS.
- [tools/run-tests.sh](../../tools/run-tests.sh): list selected case IDs and groups; execute only an explicit scope.
- [tools/git.sh](../../tools/git.sh): status, staged/unstaged diff, and whitespace checks in this project; no add/commit/push/reset or repository initialization.
```bash
sh tools/git.sh status
sh tools/versions.sh
sh tools/compile-tests.sh
sh tools/run-tests.sh list
```
```bash
sh tools/run-tests.sh --allow-sut one 'login-success'
sh tools/run-tests.sh --allow-sut group 'login'
sh tools/run-tests.sh --allow-sut all
```
`--allow-sut` acknowledges approval for the selected target and any registration writes; it is not a sandbox and does not replace client permissions.
Gradle commands use offline dependency resolution; a missing cached dependency is BLOCKED, not permission to install it.
Build scripts, plugins and driver managers can execute code or use the network — offline flags do not sandbox them; verify permissions separately.
Preflight checks CLI versions only — not dependency, browser or SUT readiness.
Wrapper gate codes: 64 = invalid arguments/scope, 69 = missing/mismatched prerequisites, 77 = selected SUT/agent approval not acknowledged. Underlying commands preserve native output and failure codes.
Test-selection wrappers never interpret shell text or forward runner flags; after adding/renaming tests, update the explicit selectors from source — this is a snapshot, not runtime discovery.
Git tools disable external diff/textconv helpers, fsmonitor and index-refresh writes; existing Git configuration and repository boundaries still apply.
No hooks are installed or activated.

## Bootstrap reference
Only execute setup commands after authorization. Wrappers are not supplied.

## Compile / syntax / discovery only
```bash
gradle --offline testClasses
```
These checks do not execute the browser scenarios. Discovery for the full selection should contain 1 tests; a focused filter intentionally selects fewer.

## Focused execution
One test:
```bash
gradle --offline test --tests 'tests.LoginTest.successfulLoginTest'
```
One class/module:
```bash
gradle --offline test --tests 'tests.LoginTest'
```

## All selected tests
Use the full suite only when that scope is requested and the target/data changes are authorized:
```bash
gradle --offline test
```
No tags, categories/groups or custom testE2e task are configured. Do not guess tag filters from another project.
Commands omit clean so the previous failure evidence is not silently deleted.

## Evidence
JUnit-style XML: `build/test-results/test/`; Gradle HTML: `build/reports/tests/test/` after an actual test run.
Record command, scope, actual versions, exit code and executed/passed/failed/skipped counts. A zero exit code with no executed tests is not a test pass.
Reusing results from an earlier run is not verification of the current changes.

## CI and integrations
CI lives in `.github/workflows/ai-pipeline.yml`: on every push to `main` the
login test runs first, and on red an LLM healing agent (`tools/heal-agent.py`)
follows `AGENTS.md` + the `fix-failing-test` skill to correct the test; the
independent browser rerun decides green and the bot commits the healed file.
CI jobs and TestOps/Jira/Confluence writes are separate permission-gated actions, not part of a local test request by default.
No TestOps upload is selected.
