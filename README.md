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

## CI — `.github/workflows/evals.yml`

Manual only (`workflow_dispatch`): evals spend paid model tokens and are
nondeterministic — no per-PR gating. A `schedule` block is present but
commented out; uncomment deliberately.

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
  driver mid-run. The workflow warms `~/.cache/selenium` with one authorized
  `login-success` browser run, after an online `gradle testClasses` (the tool
  wrappers resolve with `gradle --offline` and cannot fetch dependencies on a
  cold cache). Both directories are restored via `actions/cache`.
- `evals/runs/` is uploaded as a workflow artifact on every outcome
  (`if-no-files-found: warn`, 30-day retention). Evidence is never cleaned.
