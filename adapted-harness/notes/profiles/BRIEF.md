# Shared brief: τ-Banking failure profiling (read-only analysis, no code changes, no runs)

Repo: /Users/pchandran/Desktop/Solve/tau-banking-adapted-harness (τ²-bench, banking_knowledge domain, terminal_use).
An LLM agent (claude-sonnet-5-5) serves a simulated bank customer (also an LLM). It searches a 698-doc Markdown KB with a read-only
`shell` tool, verifies identity (`log_verification`), finds tool names in the KB, unlocks them (`unlock_discoverable_agent_tool`),
calls them (`call_discoverable_agent_tool`, args as a JSON string) or hands user tools to the customer (`give_discoverable_user_tool`).
Grading: 87/97 tasks compare final DB hash vs. gold-actions replay (any path to the same end state passes; extra unlocks/gives/writes
also change the hash). A few grade on ACTION (exact calls; note nested JSON-string args are byte-compared, a known grader artifact).

## Inputs
- Readable traces: adapted-harness/baseline/dev-sonnet55-terminal/traces/<task>.md (given DEV run) and
  data/simulations/smoke-baseline-sonnet55-terminal/traces/<task>.md (SMOKE rerun, same config). Each has a grading section + transcript with [n] message numbers.
- DB diffs (what actually differs from gold, per record): adapted-harness/diagnostics/out/dev-baseline.dbdiff.md and .../smoke-baseline-sonnet55-terminal.dbdiff.md
- Task ground truth: data/tau2/domains/banking_knowledge/tasks/<task>.json — `user_scenario.instructions` (what the customer was told),
  `evaluation_criteria.actions` (gold), `description` (purpose/notes), `required_documents` (doc ids).
- KB docs: data/tau2/domains/banking_knowledge/documents/<doc_id>.json. READ the required documents to establish what the correct procedure was.
- Agent policy: data/tau2/domains/banking_knowledge/prompts/components/*.md

## What to produce per task (be evidence-first; cite [n] message numbers and doc ids)
1. One-line outcome: what the customer wanted, what the gold did, what the agent did.
2. **First divergence**: the earliest message [n] where the trajectory departed from what the KB procedure required. Quote the minimal evidence.
3. Did the agent find the relevant doc(s)? (searched for / read / never opened — list doc ids read vs. required)
4. Root cause, coded with ONE primary + optional secondary from:
   - R1 retrieval-miss: never located the governing doc/rule
   - R2 cross-doc dependency (H1): read the relevant docs but failed to combine a rule in one doc with a condition/exception/prerequisite in another
   - R3 customer over-trust (H2): acted on a customer claim that policy required verifying, or that the tools/DB contradicted
   - R4 sub-task order (H3): steps done in the wrong order, or a prerequisite step skipped, against an order the KB implies
   - R5 tool mechanics: wrong unlock/give, wrong arguments/format, wrong tool chosen despite right understanding
   - R6 premature end / under-completion: stopped before finishing all of the customer's requests
   - R7 simulator fault: the simulated customer deviated from its instructions in a way that made success impossible
   - R8 grader artifact: behavior was arguably correct but grading failed it
   - R9 other (describe)
5. Evidence AGAINST the coded cause (what would make you wrong). If H1/H2/H3 do not fit, say so plainly — do not stretch them.
6. Would a harness change plausibly fix it? Name the kind of support (e.g. pre-action checklist, doc-dependency map, state ledger, verification gate), not an implementation.

Keep each task section ≤ 250 words. End with a 3-line summary across your tasks.
Write your full report to the output path you were given, and return the same report as your final message.
Never quote the hidden customer instructions as if the agent could see them; they are for diagnosis only.
