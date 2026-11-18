# agent-skill-evals

Agent-behavior eval harness for a QA automation project
(Java / Gradle / JUnit / Selenide, agent under test: Codex CLI).

## Layout

- `tools/` — POSIX entry points (`versions`, `compile-tests`, `run-tests`, `evals`, `git`)
- `evals/` — `.case` fixtures, fail-closed evidence adapter (`evidence.py`), judge rubrics, setup scripts; run evidence lands in `evals/runs/` (gitignored, uploaded as CI artifact)
- `knowledge/`, `.agents/skills/`, `src/`, `login.html` — the project the agent is evaluated on; the SUT is the local `login.html`

## Local

```bash
sh tools/versions.sh                                  # pins: java/javac 21, gradle 9.6.0, git
sh tools/compile-tests.sh                             # offline compile
sh tools/run-tests.sh --allow-sut one login-success   # real browser run (authorized)
python3 -B -m unittest discover -s evals -p 'test_*.py'
sh tools/evals.sh list
sh tools/evals.sh --allow-agent all                   # paid model calls, codex only
```

Details and the permission contract: [knowledge/testing/run-tests.md](knowledge/testing/run-tests.md).

## CI — `.github/workflows/ai-pipeline.yml` (`ai-pipeline`)

Runs on every push to `main` and manually via `workflow_dispatch`: evals
spend paid model tokens and are nondeterministic, so the main-branch run is a
post-merge signal, not a per-PR gate. Runs are serialized per ref via
`concurrency` — a merge burst queues rather than overlapping paid runs. A
`schedule` block is present but commented out; uncomment deliberately.

Two jobs on the free/paid boundary, both provisioning the same environment
via the composite action `.github/actions/eval-env`:

- `verify` installs the toolchain, warms the shared caches with one online
  `login-success` browser run, then runs every free check fully offline
  (compile, wrapper, evidence unit tests, case listing).
- `evals` logs Codex in once, runs the `run-tests` cases, then the
  `fix-failing-test` case (agent fix plus an independent browser
  verification), and commits the verified fix back to `main` as
  `github-actions[bot]` (a `[skip ci]` commit — the fix is already
  JUnit-verified, so no second pipeline pass burns eval tokens). Setting
  the `LLM_JUDGE` repository variable to `1` adds a judged re-run of every
  case. One `evals/runs/` evidence artifact is uploaded on every outcome.

A failed step stops the chain before any further spend. Exception: a failed
login TEST warns and continues — SUT/test mismatch is a valid signal this
pipeline exists to measure; only a run that never executes (no JUnit XML)
is an infra failure worth stopping for.

Required configuration (Settings → Secrets and variables → Actions):

| Kind     | Name                 | Required | Purpose                                        |
|----------|----------------------|----------|------------------------------------------------|
| Secret   | `OPENAI_API_KEY`     | yes      | `codex login --with-api-key`                   |
| Secret   | `CODEX_ACCESS_TOKEN` | fallback | `codex login --with-access-token`              |
| Variable | `LLM_JUDGE`          | no       | `1` enables the judged pass (see below)        |

Notes:

- The judge pass re-runs every case with `LLM_JUDGE=1` — a second set of agent
  calls plus one judge call per case — because `LLM_JUDGE` is only honored
  while a case executes.
- `SE_OFFLINE=true` inside the eval means Selenium Manager cannot download a
  driver mid-run. The workflow warms `~/.cache/selenium` and the Gradle
  runtime classpath with one online `gradle test` (the tool wrappers resolve
  with `gradle --offline` and cannot fetch dependencies on a cold cache).
  Both directories plus the pinned Gradle distribution and the Codex CLI
  install are restored via `actions/cache`.
- `evals/runs/` is uploaded as a workflow artifact on every outcome
  (`if-no-files-found: warn`, 30-day retention). Evidence is never cleaned.
