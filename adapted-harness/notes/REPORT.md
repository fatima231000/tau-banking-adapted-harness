# τ-Banking adapted harness: what we did, what we found, where it stands

All results here are on **DEV** (24 tasks, one trial per task) unless a line says otherwise.
TEST was not run. Model, customer simulator and retrieval are the pinned baseline configuration
(`claude-sonnet-5-5`, `terminal_use`).

## 1. Summary

- **The agent's problem is not finding documents. It is deciding.** With every required document
  placed in the prompt, the plain agent scores 13/24, against 11 and 12 with the shell. The
  failures we can fix are decisions where the agent's own caution overrides what the procedure
  says or what the customer asked.
- **Four DEV tasks cannot be won.** In 082, 083, 084 and 087 the expected dispute liability is
  not determined by the documents. A stronger model given only the right documents disagrees
  with the expected answer.
- **Eleven harness runs built around gates, a connected index and compiled rules all landed
  between 9 and 12**, the same as the baseline (11 and 12).
- **A small harness evolved from root causes scored 14, 13 and 12 on three DEV runs.**
  It is the baseline agent plus one prompt section, one state line and one self-check. Task 015,
  which failed in all 13 earlier runs, passes in all three.
- **The gain is about one to two tasks on 24 and is not yet proven to generalise.** The harness
  text was written from six DEV tasks. On decision points from the other failing tasks it shows
  no gain in replay. TEST is the check that is still missing.
- **Cost fell by about four times.** Prompt caching brings the agent's spend for a DEV run from
  about $48 to about $11 with the evolved harness.

## 2. What the harness is now

The baseline agent, its tools and the shell retrieval are unchanged. The harness adds three
elements, all loaded from one file, `adapted-harness/evolve/out/best.json`:

| Element | What it does | Where in the code |
|---|---|---|
| Prompt section | Nine short principles: reasoning, grounding, gates, confirmation, scope, recommendations, arguments, conflicts, handoff | `prompts.build_system_prompt` appends it after the bank's policy |
| State line | Tells the agent how many times the customer has asked for a human agent | `context.ContextBuilder` appends it to customer messages |
| Self-check | Before a reply is sent, the agent re-reads its own draft once against five checks and revises it | `agent.generate_next_message`; one extra model call per reply; nothing is blocked |

Prompt caching is on. There are no gates, no extra tools and nothing compiled from the knowledge
base. A candidate is a JSON file, so changing the harness means changing a file, not code.

The earlier components (precheck gate, ledger, decision records, checker, connected index, skill
cards and rulings, search tool) are still in `src/tau2/agent/adapted/` behind flags. The
`evolved` preset turns all of them off. They are kept only so the earlier runs can be reproduced.

## 3. How to run and test it

Setup is the same as the baseline (`adapted-harness/README.md`). Then:

```bash
# pipeline check, then DEV, with the evolved harness (the default preset)
adapted-harness/run_adapted.sh smoke smoke-evolved
adapted-harness/run_adapted.sh dev   dev-evolved

# rerun only the tasks a change affects
adapted-harness/run_adapted.sh dev rerun-015 --task-ids task_015

# comparisons
HARNESS_PRESET=plain adapted-harness/run_adapted.sh dev dev-plain        # baseline agent + caching
HARNESS_PRESET=plain HARNESS_CANDIDATE=adapted-harness/evolve/candidates/method.json \
  adapted-harness/run_adapted.sh dev dev-method                          # any candidate file

# one table of every recorded DEV run (also writes evolve/out/dev_results.json)
uv run --frozen python adapted-harness/diagnostics/dev_table.py

# why a task failed: agent's final database against the expected one
uv run --frozen python adapted-harness/diagnostics/db_diff.py data/simulations/<run> task_015
```

Testing a harness change before spending a DEV run (needs `ANTHROPIC_API_KEY`):

```bash
# score candidates on frozen decisions: wrong ones to fix, correct ones to keep
UV_FROZEN=1 uv run --with anthropic python adapted-harness/evolve/replay.py \
  --candidates plain,method,g1c1_final --split all

# rebuild the decision points from recorded runs, and evolve a candidate
UV_FROZEN=1 uv run --with anthropic python adapted-harness/evolve/points.py
UV_FROZEN=1 uv run --with anthropic python adapted-harness/evolve/evolve.py --parent method
```

The replay reads three recorded runs of the plain agent. One is in the repo
(`adapted-harness/baseline/`). The other two are under `data/simulations/`, which is not
committed: `adapted-harness/run.sh dev dev-baseline-rerun1-sonnet55-terminal` and
`HARNESS_PRESET=plain HARNESS_RETRIEVAL=golden_retrieval adapted-harness/run_adapted.sh dev dev-plain-golden-retrieval`
recreate them.

TEST has not been run. To run it once on the frozen harness:
`adapted-harness/run_adapted.sh test milestone-1`.

## 4. What we diagnosed

### How the traces were read

1. **Outcome across runs.** Pass/fail per task over every DEV run separates tasks that pass in
   nearly every run (9), never pass, and flip. A task that flips with no change is noise, not signal.
2. **What changed in the database.** `db_diff.py` rebuilds the agent's final database and the
   expected one and prints the records that differ. This locates the divergence.
3. **Why, at the turn where it diverged.** We read the conversation, the model's thinking and
   the governing document at that turn.
4. **Agent's fault or the benchmark's?** Two oracles. One puts the required documents in the
   prompt (is retrieval the problem?). The other gives a stronger model the documents and asks
   for the correct calls (can the expected answer be derived at all?).

All four use grader data. None of it is given to the agent.

### Root causes

| Tasks | What the agent does | Kind |
|---|---|---|
| 082, 083, 084, 087 | Dispute liability differs from the expected value | Not winnable: the documents do not determine it. The expected values are also inconsistent with each other (a $47.50 dispute gets $50, a $412.88 one is capped at its amount); 083's expected calls omit a required argument |
| 015 | Demands identity verification before giving a self-service tool. The internal procedure lists three pre-checks; this is not one | Adds a condition |
| 070, 071 | Treats "confirm your company is within 4 years", from a customer-facing guide, as something it must verify, then switches the customer to another account | Adds a condition |
| 026 | Finds four wrong transactions, steers the customer to dispute three | Narrows the request |
| 078 | Customer asks to freeze the cards; agent recommends closing and skips the freeze | Replaces the request |
| 066 | Adds a free-text reason the procedure does not ask for; uses a label from a document instead of the tool's value | Wrong or unrequested argument |
| 081 | Transfers to a human on the third request; the policy says four | Ignores a countable rule |
| 014 | Does not make a transfer the policy allows, or picks the wrong reason code | Handoff |
| 099 | Skips the lookup that proves eligibility | Skips a check |
| 075 | Picks the wrong account when comparing fees | Wrong comparison |
| 048 | Re-asks about a closure the customer had moved past; the simulated customer then agrees | Fragile; depends on the simulator |

The common pattern in the winnable failures: the agent has read the right document and then
puts its own judgement ahead of it. This is the pack's exploration and exploitation question
seen from the failure side. The agent investigates when no rule asks it to (015), does not
investigate when a rule does (099), and trusts its prior over the document (070).

### What did not hold up

- **"The agent does not find the documents."** Passing and failing baseline tasks opened the
  same share of their required documents (about 0.6). The required-documents oracle only reaches 13.
- **"Most failures are expected answers the documents do not determine."** We believed this for
  a while and put the ceiling at 14 to 16. The derivability oracle showed only four tasks are out
  of reach. The ceiling is about 20.

## 5. What we tried, in order, and what each taught us

| Step | What it was | DEV | What we learned |
|---|---|---|---|
| Baseline | Pinned configuration | 11, 12 | One-task swing between identical runs |
| v6 to v8 | A precheck form before every state-changing call, tool contracts, a task ledger, decision records, an independent checker | 11, 12, 10 | The gated decisions were already right. A replay of the checker on 57 decision records upheld 91% and missed the decisive errors |
| Connected index | A graph over the documents built from shared tools, entities and "needs/provides" matches | no gain | See below |
| Skill cards and rulings | 30 cards with 180 compiled conflict rulings | 12, 11 | Rulings freeze a guess where the documents are silent. Two are wrong on fields that decide tasks |
| Working method and a search tool | One prompt section, no gates | 11, 9 | No gain; the search tool is not needed |
| Hand-written decisions section | "Only the policy, an internal procedure or a tool error can stop a request" | 9 | Fixed wrong decisions and broke correct refusals. The replay predicted this before the DEV run |
| Evolved candidate | Section, state line and self-check, rewritten from root causes | 14, 13, 12 | Two of three runs score above every earlier arm |

**Why the connected index did not help.** In the 90-document index 42% of all possible document
pairs are linked, and a typical document links to 39 of the other 89. Starting from a document a
DEV task needs, 8 to 13% of the links lead to another document that task needs. The knowledge
base has almost no explicit cross-references (9 of 698 documents), so every link was inferred,
and the inferred links are plumbing ("this procedure needs an account id, that document
describes the lookup") that nearly every procedure shares. The links that decide tasks are rule
against rule, and retrieval was not the bottleneck anyway.

**Why the rulings did not help.** Of 180 "issues", 79 are ambiguities and 71 are dependencies;
30 are conflicts. Issues were searched per tool, so the conflict that decides 070 and 071 (a
product guide against the internal eligibility procedure) was never found. The liability ruling
and the "pass the name with an Account suffix" ruling both contradict the expected answers.

**The mistake behind both.** They were built before the failures were diagnosed, and they were
judged only by full DEV runs, which cannot separate a one-task effect from noise.

## 6. How the evolved harness was built

1. **Root-cause records** (`evolve/points.py`). A model reads each failing run of the plain agent
   with the expected calls and the database difference, and records the turn of the first wrong
   decision, what a correct reply does there, the kind of error and the rule. Result: 24
   wrong-decision points (the four unwinnable tasks left out) and 70 correct-decision controls
   from passing runs.
2. **Split by task.** Six tasks form the evolve half (015, 026, 066, 070, 078, 081). The proposer
   only ever sees these. The other failing tasks (014, 048, 071, 099) are held out.
3. **Replay** (`evolve/replay.py`). A point freezes the conversation just before the decision.
   The decision is regenerated several times under a candidate, through the harness's real turn
   loop, and a judge compares it with the reference. A wrong-decision point counts when the new
   reply takes the correct decision. A control counts as broken only when the new reply takes a
   contrary decision.
4. **Evolution** (`evolve/evolve.py`). A model sees the decisions the current candidate gets
   wrong and the correct ones it breaks, and rewrites the three elements in general terms. A
   lint rejects product names, tool identifiers, amounts and dates. A child replaces its parent
   only if it fixes more wrong decisions and keeps the controls.
5. **Check on DEV**, then freeze.

Replay results on the evolve half (51 samples of wrong decisions, 26 of correct ones):

| Candidate | Wrong decisions fixed | Correct decisions broken |
|---|---|---|
| Plain agent | 2/51 | 0 |
| Working-method section (seed) | 7/51 | 1 |
| Evolved, first child | 24/51 | 1 |
| Evolved, second child (chosen) | 29/51 | 1 |

On the held-out half the chosen candidate fixes 0 of 21 samples (plain: 1 of 21) and breaks no
more correct decisions than plain (5 contrary of 60, against 6).

Three things to know about how this was run:

- **The evolution ran one generation.** Its acceptance rule first rejected both children,
  because the judge counted a reply that paused to look something up as a broken decision.
  We re-judged those replies, corrected the judge to a three-way verdict, and chose the stronger
  child by hand. The corrected rule is in the code; a second generation has not been run.
- **A wording defect was fixed after two DEV runs.** In 19 of 218 self-checked replies the check's
  own wording reached the customer ("I rechecked the draft..."). The evolved text had dropped the
  sentence "do not mention this check". With it restored, 0 of 104 replies leak. The third DEV
  run uses the fixed text, which is `best.json`.
- **The principles are general in wording but were shaped by six tasks.** The lint removes task
  content; it cannot remove that influence. Only held-out tasks and TEST can measure it.

## 7. Results

DEV, tasks passed out of 24, one trial each. "Evolve 6" are the tasks the candidate was written
from; "not derivable" are the four unwinnable tasks. Regenerate with `diagnostics/dev_table.py`.

| Arm | Passed | Evolve 6 | Other 14 | Not derivable 4 | Agent cost |
|---|---|---|---|---|---|
| Baseline, given run | 11 | 0 | 11 | 0 | $47.83 |
| Baseline, rerun | 12 | 1 | 11 | 0 | $51.61 |
| Gates v6 | 11 | 1 | 10 | 0 | $99.30 |
| Gates v7 + caching | 12 | 2 | 10 | 0 | $14.26 |
| Gates v8 + decision records | 10 | 0 | 10 | 0 | $15.68 |
| Skill cards + rulings, run 1 | 12 | 2 | 10 | 0 | $5.79 |
| Skill cards + rulings, run 2 | 11 | 1 | 10 | 0 | $5.82 |
| Working method + search tool, run 1 | 11 | 1 | 10 | 0 | $5.91 |
| Working method + search tool, run 2 | 9 | 0 | 9 | 0 | $6.06 |
| Oracle: required documents in the prompt | 13 | 0 | 13 | 0 | $3.43 |
| Hand-written decisions section | 9 | 1 | 8 | 0 | $7.87 |
| Seed: working-method section | 12 | 1 | 11 | 0 | $8.59 |
| Seed: working-method + self-check | 11 | 2 | 9 | 0 | $10.97 |
| **Evolved, run 1** | **14** | 2 | 12 | 0 | $11.09 |
| **Evolved, run 2** | **13** | 2 | 11 | 0 | $11.26 |
| **Evolved, final wording** | **12** | 1 | 11 | 0 | $10.41 |

How to read the evolved runs:

- **Gained against both baseline runs:** 015 in all three runs. 071, 081 and 099 in run 1.
- **Gained against one baseline run:** 048 in runs 1 and 2; 014 in runs 2 and 3; 026 in run 2.
- **Lost:** 101 in run 1 and 018 in run 2. The baseline passes both in both runs. In 018 the
  agent corrected rewards on four transactions the expected solution leaves alone.
- **Targeted but still failing in all three runs:** 066, 070, 078.
- **015 passes late, not cleanly.** The agent still asks for verification at first. After the
  customer pushes back, its self-check concludes no rule requires it and it hands over the tool.

How much to trust it: three evolved runs average 13.0 against 11.5 for the baseline, and the
third run (12) only equals the baseline rerun. With 24 tasks and a one-task swing between
identical runs, this is an encouraging difference and not yet a proven one. The one result that
repeats in every run is task 015.

## 8. What is not solved

- **Four tasks are out of reach** without rules fitted to the expected answers, which we chose
  not to write.
- **Three targeted failures still fail** (066, 070, 078). In replay the candidate changes those
  decisions in some samples, but not reliably through a whole conversation.
- **No evidence of transfer yet.** Held-out replay shows no gain; the held-out DEV gains appear
  in one run each.
- **The self-check costs one model call per reply** and raised the agent's cost from about $8.60
  (section alone) to about $11 a run. Whether it earns that needs more runs than we have.
- **This work ran more full DEV runs than the pack asks for.** The pack says to rerun the tasks a
  change affects. The replay was built to stop doing that; from here, changes should be tested
  on replay and on targeted reruns.

## 9. Running this for real customers

- **Every harness change is a file, tested before release.** A candidate is a JSON file. Before it
  ships it is replayed against a regression set of recorded decisions: ones that must change and
  ones that must not. This is the same loop used here, fed by production conversations instead of
  DEV.
- **The regression set has to come from real outcomes.** Here the reference is the benchmark's
  expected state. In production it would be decisions reviewed by the bank's own staff, including
  the refusals that were correct.
- **Keep the harness small.** Each added principle fixed some decisions and risked others (the
  "scope" principle is the likely cause of the 018 failure). A short text with a measured effect
  is easier to change safely than gates and compiled rules that nobody can test in isolation.
- **Fix the knowledge base, not the harness, where documents disagree.** The four unwinnable
  tasks come from documents that do not determine an answer. A harness rule there hides the gap.
  The report of conflicts (`kb_index/out/known_issues.json`) is more useful as a list for the
  policy owner than as agent input.
- **Watch the self-check.** It is the one element that can change what a customer sees, as the
  wording leak showed. It needs its own check in the regression set.
- **Things a state line can carry.** Counts and facts the model tracks badly over a long
  conversation (requests for a human, steps already done) are cheap and exact for the harness to
  supply.

## 10. What we would do next

1. Run TEST once on the frozen `best.json`, next to the TEST baseline.
2. Run a second generation of the evolution with the corrected acceptance rule, and add control
   points from 018 and 101, the two tasks that regressed.
3. For 066, 070 and 078, find out from the traces why the decision changes in replay but not in
   the full conversation.
4. Delete the switched-off components once these results are recorded.

## 11. File map

| Path | What it is |
|---|---|
| `src/tau2/agent/adapted/` | The harness: `config.py` (presets, candidate file), `prompts.py`, `context.py` (state line), `agent.py` (turn loop, self-check). Older components are behind flags |
| `adapted-harness/evolve/out/best.json` | The evolved candidate the `evolved` preset loads |
| `adapted-harness/evolve/candidates/` | Every candidate tried, including rejected ones, with the reason |
| `adapted-harness/evolve/points.py`, `replay.py`, `evolve.py` | Root-cause labelling, decision replay, evolution |
| `adapted-harness/evolve/out/` | Decision points, replay rows, and `dev_results.json` (per-task DEV results of every arm) |
| `adapted-harness/diagnostics/` | `db_diff.py`, `dev_table.py`, `derivability.py` (the derivability oracle), and earlier analyses |
| `adapted-harness/kb_index/` | The connected index, contracts, rulings and skill cards. Not used by the evolved preset |
| `adapted-harness/run_adapted.sh` | Runner; `HARNESS_PRESET` and `HARNESS_CANDIDATE` select the harness |
| `src/tau2/utils/llm_utils.py` | One opt-in addition, off by default: sending the model's thinking blocks back each turn. Not used by the evolved preset |
