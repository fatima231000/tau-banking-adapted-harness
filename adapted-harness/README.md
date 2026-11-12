# τ-Banking harness exercise

Start with [PACK.md](PACK.md), which describes the exercise. This folder has what you need to run it.

## Setup

1. Python 3.12 or 3.13 and [uv](https://docs.astral.sh/uv/). From the repo root, run `uv sync`.
2. Node.js. Then install the sandbox that the terminal search runs in, at the version τ² expects:
   `npm install -g @anthropic-ai/sandbox-runtime@0.0.23`
3. Create `.env` at the repo root containing `ANTHROPIC_API_KEY=...`. The key is in 1Password. `.env` is git-ignored; never commit it.

## Baseline configuration

| | |
|---|---|
| Domain | `banking_knowledge` |
| Agent | `claude-sonnet-5-5` (`llm_agent`) |
| Simulated customer | `claude-sonnet-5-5` |
| Knowledge access | `terminal_use` |
| Model args | `{}` for both. Current Claude models reject τ²'s default `temperature: 0`. |
| Trials | 1 |
| Code | `tau2-bench` at `19f13ea3` |
| Splits | `splits/smoke.txt`, `splits/dev.txt`, `splits/test.txt` |

`task_102` has been removed from DEV, which is 24 tasks.

## Running

```sh
adapted-harness/run.sh smoke my-smoke                     # pipeline check, 6 tasks: about $10
adapted-harness/run.sh dev my-dev                         # full DEV pass: about $50, about 35 minutes
adapted-harness/run.sh dev rerun-015 --task-ids task_015  # targeted rerun
adapted-harness/run.sh test milestone-1                   # milestones only, everything frozen: about $80, about 40 minutes
```

Results go to `data/simulations/<save-name>/results.json`. To turn a run into readable traces:

```sh
adapted-harness/export_traces.sh data/simulations/<save-name>  # writes traces/index.md and one file per task
```

## DEV baseline

`baseline/dev-sonnet55-terminal/` holds the baseline DEV run: `results.json` and readable `traces/`. Start at `traces/index.md`. 11 of 24 tasks passed.

Each trace has a grading section. It is there for your analysis. The agent must never see it.
