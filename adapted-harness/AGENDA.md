# Session agenda: 2 hours

## Before the session (about 30 minutes, on your own)

1. Follow the setup in [README.md](README.md).
2. Run SMOKE to check that everything works on your machine:
   `adapted-harness/run.sh smoke my-smoke` (about $10 and 5–15 minutes).
   If anything fails, tell us before the session so we don't spend session time on setup.
3. Read [PACK.md](PACK.md) and skim the DEV baseline, starting at `baseline/dev-sonnet55-terminal/traces/index.md`.

## The session

| Time | What |
| --- | --- |
| 0:00–0:10 | **Kickoff.** Questions about the pack, and your first plan. |
| 0:10–0:30 | **Failure analysis.** Walk us through a few DEV baseline failures and what you think caused each one. |
| 0:30–1:15 | **Build and iterate.** Change the harness, rerun the affected DEV tasks, and decide what to do next. If you want a TEST milestone, freeze everything and start it by 1:05; it takes about 35–40 minutes. |
| 1:15–1:45 | **Productionizing.** What it would take to run and change your harness safely in production (PACK.md, section 5). |
| 1:45–2:00 | **Wrap-up.** Your changes, your results, what you would do next, and your questions for us. |

Use any tools you like, AI included. Work on your own branch and commit as you go.

Your API key has a spending limit. For planning: a targeted rerun of a few DEV tasks costs a few dollars, a full DEV pass about $50 (about 35 minutes), and a TEST run about $80.
