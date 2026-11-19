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

1. **test** runs `login-success`. A pass makes no model calls. Only a Selenide UI
   failure recorded for that test is handed off; a failure to compile or start
   the browser is not a reason to edit the test.
2. **heal** uses the JUnit failure, the fixture, and the skill to propose a fix.
   The agent can run predefined checks and replace only test IDs or string
   values in the existing Selenide steps. This paid step needs the
   `OPENAI_API_KEY` repository secret and sends lesson context to the model.
3. **verify** runs the same test on a fresh checkout with the candidate. If it
   passes, download `verified-login-patch` from the run. Review the diff against
   the intended change before applying it. The workflow never pushes a commit.

See [AGENTS.md](AGENTS.md) for the agent instructions and
[Running tests](knowledge/testing/run-tests.md) for the commands and reports.
