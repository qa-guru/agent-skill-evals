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
The eval runner additionally needs `mktemp`, Python 3.9+ (standard library only) and an authenticated Codex CLI.
Scripts resolve the project root relative to themselves, including paths with spaces.
- [tools/versions.sh](../../tools/versions.sh): verify selected CLI pins. Git has no separate pin; only its availability/version command is checked.
- [tools/compile-tests.sh](../../tools/compile-tests.sh): compile or collect, never a browser-test PASS.
- [tools/run-tests.sh](../../tools/run-tests.sh): list selected case IDs and groups; execute only an explicit scope.
- [tools/git.sh](../../tools/git.sh): status, staged/unstaged diff, and whitespace checks in this project; no add/commit/push/reset or repository initialization.
- [tools/evals.sh](../../tools/evals.sh): list or execute the explicit agent-behavior fixtures; permissions and evidence are described below.
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
Wrapper gate codes: 64 = invalid arguments/scope, 69 = missing/mismatched prerequisites or no selected eval cases, 77 = selected SUT/agent approval not acknowledged. Underlying commands preserve native output and failure codes.
Test-selection wrappers never interpret shell text or forward runner flags; after adding/renaming tests, update the explicit selectors from source — this is a snapshot, not runtime discovery.
Git tools disable external diff/textconv helpers, fsmonitor and index-refresh writes; existing Git configuration and repository boundaries still apply.
No hooks are installed or activated.

## Agent-behavior evals
```bash
sh tools/evals.sh list
sh tools/evals.sh --allow-agent one run-tests-list-scopes
sh tools/evals.sh --allow-agent group run-tests
sh tools/evals.sh --allow-agent all
python3 -B -m unittest discover -s evals -p 'test_*.py'
```
Only `EVAL_AGENT=codex` is validated. Other backend values return 69; no Devin export schema is assumed.
`--allow-agent` acknowledges paid model calls and network access to the model, not installs, external SUT access or integration writes.
`LLM_JUDGE=1` adds a second paid Codex call per case: a read-only judge grades the transcript against `evals/judge/<rubric>` (case field `JUDGE`); the verdict must follow the strict RUBRIC/VERDICT protocol and is fail-closed via `evals/evidence.py verdict`. Without it the judge check is reported as SKIP.
The authorized fix fixture also runs the selected local browser scope independently after the agent's correction.

Case files are trusted shell code, sourced even for `list` and selection. Do not load untrusted `.case` files.
ID, GROUP, TITLE and PROMPT are required; other fields default to empty for each case, without inheriting the previous fixture.
`EXPECT_EXEC`/`FORBID_EXEC` contain action names from [evals/evidence.py](../../evals/evidence.py), not command regexes:
`list`, `versions`, `compile`, `test`, `login-failure`, `login-pass`.
`EXPECT_REPORT` contains space-separated EREs; use `[[:space:]]` within a pattern.
`FILES_UNCHANGED` protects files/directories. `FIX_TEST` allows only the seeded expectation correction in the original source tree, ignoring formatting whitespace outside literals.
The fix outcome requires observed red/green runs, the retained assertion and a fresh independent JUnit result of 1 executed, 1 passed, 0 failed, 0 skipped. The verifier uses a new build directory and `gradle --offline --no-build-cache --rerun-tasks test --tests 'tests.LoginTest.successfulLoginTest'` after preflight/compilation, so cached test output cannot count as execution. BLOCKED is not a verified fix.

The adapter parses JSON, preserves decoded commands, includes unfinished test attempts in forbidden-action checks, and uses only the final message for report checks.
It recognizes direct commands, shell `-c` wrappers and simple command lists; it is not a general shell interpreter or a security boundary.
Unknown tool-item types and incomplete/malformed transcripts fail evidence validation. Command/text checks do not prove native skill activation or full semantic compliance.

Each run retains its case, runner, evidence adapter, CLI versions and workdir path in `evals/runs/`.
Copied workspaces and verification builds are retained; no destructive cleanup is performed.
Gradle/Selenium caches are shared writable host state, so the runs are not hermetic. Network access also permits Gradle's local sockets and is not SUT consent.
Selenium Manager receives `SE_OFFLINE=true` and `SE_AVOID_STATS=true`: a missing cached browser/driver is BLOCKED, not permission to download it.
The eval exit is 0 only when all selected cases pass, otherwise 1. A failed outcome is not automatically proof of an agent defect; inspect the exact stage and evidence.

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
No CI file is generated.
CI jobs and TestOps/Jira/Confluence writes are separate permission-gated actions, not part of a local test request by default.
No TestOps upload is selected.
