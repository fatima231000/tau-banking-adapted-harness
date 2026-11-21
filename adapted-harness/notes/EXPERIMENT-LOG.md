# DEV iteration log

One entry per iteration: one question, one baseline, one controlled change, one
evaluation, one result. Label every score with its split. TEST only at milestones,
with harness + memory frozen (record the commit hash).

## Framing (fill before iteration 1)

The pack's question: *when should the agent rely on what it knows vs. investigate
further, and how does its knowledge stay current?*

Keep three things apart for each line of work:

| | |
|---|---|
| What the field knows | _(τ-Knowledge paper, arXiv 2603.04370, unverified until read: terminal vs. retrieval results, discoverable-tool difficulty)_ |
| What the field lists as open | _(from the paper's limitations / future-work section, once read)_ |
| What is only new to us | |

Why it matters beyond τ-Banking (one line): ...

## Iteration 0: baseline (DEV, given)

- Config: `claude-sonnet-5-5` agent + customer, `terminal_use`, `{}` llm args, 1 trial, `19f13ea3`.
- Result: **DEV 11/24**, $49.92. Run: `baseline/dev-sonnet55-terminal/`.
- All 13 failures ended by `user_stop`, so none hit max_steps (200), max_errors (10) or the timeout.
- Grading basis of the failures: 11 `DB`, 2 `ACTION` (task_014, task_083).
- Observed in grading (facts, not yet causes):
  - task_014 (ACTION): DB matched; the single gold action `transfer_to_human_agents(reason="unconfirmed_external_communication")` was never called.
  - task_083 (ACTION): all unlocks + `log_verification` matched; the 4 dispute filings missed.
    See the grader note below: at least part of this is formatting, not behavior.
  - task_081 (DB): the action check reports all 37 gold actions matched, but that over-counts:
    the matcher doesn't use up a predicted call once matched, so 3 transfer requests covered
    4 gold entries. The DB diff shows the missing `transfer_request_4` (the agent transferred
    on request 3; gold transfers after 4).
  - Recurring tools among misses: `open_bank_account_4821` (066, 070, 071),
    `file_debit_card_transaction_dispute_6281` (082, 083, 084, 087),
    `give/call_discoverable_user_tool` (015, 026), `get_bank_account_transactions_9173` (078, 087).

### Grader note: ACTION matching on JSON-string arguments

`call_discoverable_agent_tool(arguments=<JSON string>)` is compared with plain `==`
(`Action.compare_with_tool_call`, `src/tau2/data_model/tasks.py:178`; `compare_args` is
`None` in task_083). Checked: the gold dispute call re-serialized as compact JSON, with
identical content, **does not match**. The gold also writes `150.00`, which a standard JSON
serializer emits as `150.0`.

- Affects the ACTION-graded tasks: DEV task_014, task_083; TEST task_004, 033, 034, 035.
- For DB-graded tasks, `action_checks` are only diagnostics, so `call:` misses there over-count.
- Open decision (yours): keep grading as-is and report it, or normalize JSON args in a
  *separate, labeled* scorer. Teaching the agent to imitate the gold's formatting would be
  a Goodhart move; avoid it.

## Iteration 0b: SMOKE pipeline check (2026-11-20, unchanged baseline config)

- Run: `data/simulations/smoke-baseline-sonnet55-terminal/` (traces exported). **SMOKE 4/6**, $10.48.
  0 agent/user errors; all ended `user_stop`. The pipeline works end to end.
- Against the given DEV run on the same 6 ids: 5 agree; **task_087 flipped FAIL→PASS with
  no change**. One trial does not settle a task's outcome, so in later iterations a single
  flip does not count as evidence of improvement.
- Setup changes from the README, environment only: `uv sync --extra knowledge --extra dev`,
  `brew install ripgrep`, `srt@0.0.23`; commented out the `<placeholder>` lines in `.env`,
  which broke `run.sh`'s `. ./.env`.

## Iteration 1

- Question:
- Failure(s) addressed (task ids, evidence from trace):
- Hypothesis: why the baseline fails here, specifically:
- Change (one, controlled; commit):
- Evaluation: which tasks rerun, and what counts as fixed vs. noise
  (single trial: one flip is weak evidence; rerun the unchanged baseline on the same ids
  to see how much it varies):
- Result (DEV k/n on the targeted ids; any regressions):
- What changed in our understanding:
- Next:
