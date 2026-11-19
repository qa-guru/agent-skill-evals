# Running tests

Run these commands from the project root with a POSIX shell.

## Preflight and Compilation

```sh
sh tools/versions.sh
sh tools/compile-tests.sh
sh tools/run-tests.sh list
```

The [toolchain check](../stack/versions.md) does not verify Gradle caches,
Chrome, or the driver. Compilation runs `gradle --offline testClasses`;
it neither discovers nor executes browser tests. On a new machine,
`gradle testClasses` can populate the dependency cache without running a
browser. Ask before installs or downloads, including dependencies and drivers.

## Browser Execution

```sh
sh tools/run-tests.sh --allow-sut one 'login-success'
sh tools/run-tests.sh --allow-sut group 'login'
sh tools/run-tests.sh --allow-sut all
```

Use `one login-success` for the lesson. The broader scopes currently select
the same test; `list` shows the fixed selectors, not test discovery.

Verify Chrome and the driver are available, then get approval for the selected
scope against local `login.html`. `--allow-sut` records that approval; it is not
a sandbox. Gradle dependency resolution is offline, but Selenium may still
try to download a driver unless it is already configured for offline use.
External targets require separate approval.

The wrapper uses `gradle --offline test --rerun` so a cached result doesn't
stand in for a new run. Preserve any earlier failure evidence you need before
rerunning. `CI=true` selects headless Chrome.

Script exit codes: 64 = invalid arguments, 69 = missing/mismatched tools,
77 = browser scope not approved. Gradle returns its own exit status.

## Evidence

- JUnit XML: `build/test-results/test/`.
- Gradle HTML: `build/reports/tests/test/index.html`.
- Git inspection: `sh tools/git.sh status`, `diff`, or `check`.

Record the exact command, scope, tool versions, exit code, and
executed/passed/failed/skipped counts. A run with no executed tests is not a pass.
The [CI demo](../../README.md#github-actions-demo) is separate from a local test
run. It uses Python 3.9+; the paid healing step also needs an API key.
