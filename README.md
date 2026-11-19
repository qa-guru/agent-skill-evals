# Login Testing with Selenide

One login page, one browser test, and one question: when the page changes, does
the test need a fix, or did the application break?

## Run It Locally

You need JDK 21, Gradle 9.6.0, Git, and Chrome with a compatible driver. There is
no Gradle wrapper. The local scripts use cached Gradle dependencies; see the
[prerequisites](knowledge/testing/run-tests.md) for a new machine.

Open [login.html](login.html) in Chrome and sign in with `user1` / `password1`.
These are demo credentials. No server, database, or API key is needed.

```sh
sh tools/versions.sh
sh tools/compile-tests.sh
sh tools/run-tests.sh list
```

To run the browser test once the local scope is approved:

```sh
sh tools/run-tests.sh --allow-sut one login-success
```

Open `build/reports/tests/test/index.html` for the result. Compilation alone
does not run the browser test.

## Lesson: Diagnose a Red Test

1. Run `login-success` as a baseline. Read [LoginTest.java](src/test/java/tests/LoginTest.java):
   it fills the form, submits it, and checks the full welcome message.
2. In your lesson copy, change the English welcome template in `login.html`,
   keeping `{login}`. Rerun the same test and compare the expected and actual
   messages in the report.
3. Ask your coding agent to use the
   [fix-failing-test skill](.agents/skills/fix-failing-test/SKILL.md). An intended
   copy change calls for updating the stale expectation, not weakening the check
   or undoing the page change.
4. Inspect the diff and rerun `login-success`. If the page no longer signs in
   with valid credentials, that's a different problem; don't make the test
   accept a failed login.

## GitHub Actions Demo

The [workflow](.github/workflows/ai-pipeline.yml) runs on pushes to `main` and on
manual dispatch. Chrome runs headless.

1. **test** runs the full suite with `gradle test --rerun`. A pass or a build
   error without a failing JUnit test case makes no model calls.
2. **heal** reads the reports and reruns the failing classes. If the same
   failures reproduce, the agent uses the skill to inspect the code and fix
   proven test defects. It can edit Java test code under `src/test/java`, not
   the application or build. The paid step needs the `OPENAI_API_KEY` secret.
3. **verify** applies the candidate on a fresh runner without the API key,
   runs the full suite, and checks that the original tests still execute and
   pass. The diff is also available as the `verified-test-patch` artifact.
4. **publish** commits the verified Java test changes to `main` as
   `github-actions[bot]`. Only this job has write access, and it runs no tests.
   If `main` has moved since the run started, it refuses to push the old fix.
   Runs on other branches do not publish.

Add a new JUnit class under `src/test/java` and Gradle discovers it. The healer
uses the class names in the reports, not a list of registered tests.

See [AGENTS.md](AGENTS.md) for the agent instructions and
[Running tests](knowledge/testing/run-tests.md) for the commands and reports.
