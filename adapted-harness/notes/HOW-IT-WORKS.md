# How a τ-Banking run works (orchestrator → evaluator)

Code at `19f13ea3`. Paths are relative to the repo root. Statements marked *(checked)*
were run or read directly; the rest come from code reading.

## 1. The run loop: `src/tau2/orchestrator/orchestrator.py`

```
initialize()                      env.set_state(initial_state)  ← task's initial DB
                                  first message = agent greeting (DEFAULT_FIRST_AGENT_MESSAGE)
while not done:
    step()                        route self.message from_role → to_role
    _check_termination()          max_steps / max_errors / wall-clock (skipped while a tool call is pending)
_finalize()                       → SimulationRun(messages, termination_reason, costs)
evaluate_simulation()             → reward_info  (runner, after the run)
```

`step()` (`:840`) is a three-way router:

| from → to | what happens |
|---|---|
| agent/env → **user** | `user.generate_next_message`; the user simulator may stop (`###STOP###` → `USER_STOP`) or call user tools (→ env) |
| user/env → **agent** | `agent.generate_next_message`; a text reply goes to the user, a tool call goes to the env |
| agent/user → **env** | `_execute_tool_calls` → `environment.get_response` per call; an error increments `num_errors`; the result goes back to the caller |

- Half-duplex: exactly one party acts per step. A message with both text and tool calls,
  or an empty message, is a communication error → `AGENT_ERROR`/`USER_ERROR` (`:715`).
- Limits: `max_steps=200`, `max_errors=10` (tool errors, so failed shell greps count if
  they return an error), `max_steps_seconds=1200` (`src/tau2/config.py`).
- `environment.sync_tools()` runs after every step. That is how the toolkit state
  (unlocked tools) and the DB stay in sync between agent and user.
- Baseline DEV: every failure ended `user_stop`. Failures come from wrong behavior, not
  from running out of budget *(checked)*.

**Where the harness plugs in.** The agent is anything implementing
`HalfDuplexAgent.generate_next_message(message, state) -> (AssistantMessage, state)`,
registered in `src/tau2/registry.py`. The orchestrator, user simulator, environment and
evaluator stay untouched. That boundary is what keeps grader-only data out of the agent.

## 2. What the agent gets: `src/tau2/agent/llm_agent.py`, `domains/banking_knowledge/`

- System prompt = `<instructions>` (generic agent rules) + `<policy>`. The policy comes from
  `data/tau2/domains/banking_knowledge/prompts/agentic_search.md`, assembled from the
  components `policy_header`, `shell_instructions` and `additional_instructions`.
  No KB content goes into the prompt.
- 14 initial tools: user lookups, `log_verification`, `transfer_to_human_agents`,
  `get_current_time` (fixed at 2025-11-14 03:40 EST), and the discoverable-tool trio
  (`unlock_discoverable_agent_tool`, `call_discoverable_agent_tool`, `give_discoverable_user_tool`)
  plus `list_discoverable_agent_tools`, and `shell`.
- Shell (`terminal_use`): a read-only `srt` sandbox, working directory = the KB as 698 `<doc_id>.md`
  files plus `INDEX.md`. 30 s timeout, **no output truncation** (one `grep -r` can flood
  context), and commands with `..`, absolute paths or `~` are blocked. The tool docstring says
  `INDEX.txt`; the file is `INDEX.md`.
- KB: 698 docs, about 195K tokens, Markdown, median about 930 chars. Tool names appear in prose
  (`*_NNNN` suffixes), which is how the agent discovers them.

## 3. Discoverable tools: the dependency chain

```
find name in KB ──► unlock_discoverable_agent_tool(name) ──► call_discoverable_agent_tool(name, arguments=<JSON string>)
                                                       └──► give_discoverable_user_tool(name) ──► user calls it
```

- `unlock` checks only that the name exists, not that the agent read the doc.
- Calling before unlocking returns an error string.
- Unlocks, gives and (logged) calls are written to DB tables. **The DB hash includes them**, so
  an unneeded unlock, or a wrong give, breaks a DB-graded task even when the "real" state is
  right. The policy warns: "do not unlock tools you do not plan on using".
- Raw-name bypass *(checked)*: the environment executes a discoverable tool called by its raw
  name with no unlock and no log row. Keep the adapted harness from doing that.
- 45 agent-side and 4 user-side discoverable tools. `downgrade_credit_card_3847` is named in 3
  docs but not implemented.

## 4. Grading: `src/tau2/evaluator/evaluator.py`

1. If `termination_reason` is not `agent_stop` or `user_stop` → reward 0.
2. Otherwise run the evaluators the task's `reward_basis` lists, and **multiply** the results.

| basis | tasks (of 97) | how it is scored |
|---|---|---|
| `DB` | 87 | Replay the trajectory's tool calls on a fresh env (predicted); replay the gold `actions` on another fresh env (gold); compare hashes of the agent DB **and** the user DB. Any trajectory reaching the same end state passes. |
| `ACTION` | 9 | Every gold action must appear among the predicted calls; args compared with `==`, restricted to `compare_args` when set. Order is ignored and extra calls are allowed. |
| `DB`+`NL_ASSERTION` | 1 (task_102, removed: OpenAI grader) | |

Split exposure: ACTION is DEV task_014 and task_083; TEST task_004, 033, 034, 035.

**Caveat on ACTION grading** *(checked)*: the nested `arguments` of `call_discoverable_agent_tool`
is a JSON *string* compared byte for byte. Identical content in compact formatting fails, and
the gold writes `150.00`. See `EXPERIMENT-LOG.md` § Grader note.

**Reading baseline traces.** On DB tasks, `action_checks` (OK/MISS in the traces) are diagnostic
only, and they mislead in two directions:
- The `call:` MISSes over-count, for the same string-compare reason.
- The OKs over-count too. The matcher doesn't use up a predicted call once matched, so one
  call satisfies every identical gold action (task_081: 3 transfer requests showed as 4 OK).

Use `adapted-harness/diagnostics/db_diff.py` (gold-replayed vs. predicted tables) to see what
actually differs.

## 5. Information-boundary rule (the pack's one hard rule)

Never let these reach the agent: `evaluation_criteria` (gold actions), `description` (its
`notes` contain the answer, e.g. task_099), `required_documents`, `annotations`,
`user_scenario` (customer-only), and the backend DB beyond what tools return. Memory built
from earlier runs must come from the agent's own observations; grading output (reward, MISS
lists, DB diffs) is for us, never for the agent.
