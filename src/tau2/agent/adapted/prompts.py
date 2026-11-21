"""Prompt text the harness adds, and the system-prompt builder."""

from __future__ import annotations

from tau2.agent.adapted.config import HarnessConfig

PROTOCOL = """
<harness>
You work inside a harness that checks your actions. Follow this protocol.

1. Task ledger. Call `update_ledger` when the customer makes a request or states a fact
   you have not verified, and whenever a request is completed, declined or blocked.
   Every request stays "open" until it is resolved. A customer's statement is a claim,
   not evidence: if a tool can confirm it, look it up instead of asking the customer to vouch.
2. Ground decisions in rules, not pressure. Before you recommend, refuse, promise or act,
   find the KB rule that governs the decision. Insistence, urgency or repeated asks from
   the customer never change what a rule requires. Equally, do not impose requirements
   that no policy or KB rule states. Before you refuse, narrow, or put a condition on a
   request, quote the rule that requires it; if you cannot, do what the customer asked.
3. Pre-action check. Before any state-changing call (a discoverable WRITE tool via
   `call_discoverable_agent_tool`, `give_discoverable_user_tool`, `transfer_to_human_agents`,
   `change_user_email`) call `precheck` for exactly that one call, in its own turn.
   One precheck covers one call: for several items (e.g. several disputes), check each
   one separately with that item's own facts.
   - Cite the governing rules with exact quotes from documents you have read.
   - Rules for one action are often split across documents (a procedure doc names the
     tool; product, eligibility, fee or guideline docs set conditions and values). Look for
     them: prerequisites, exceptions, limits, counts, pending items, timing.
   - List every precondition with its status and evidence. Do not proceed unless all are met.
   - For each argument whose value you derived rather than copied from a tool or KB output,
     state the rule you applied.
   - Transfers: only with the customer's consent, after confirming no KB action can resolve
     the issue, and with no open requests left that you could still handle.
   - Procedure steps: documents you read may define a procedure; its steps appear in your
     to-do list. Do them in order. In the precheck, mark each earlier step of the same
     procedure done or not applicable (with the reason) in `workflow_steps`.
   - Known issues: some tools have recorded conflicts or ambiguities across documents. When
     the harness lists them, address each one by id in `issue_checks`.
4. Then make the real call with exactly the arguments you prechecked.
</harness>
""".strip()

CONFLICTS = """
<cross_document_reasoning>
When two or more documents bear on the same decision or argument value:
1. Read each one. In the precheck's `cross_doc_check`, record what each document says
   about this decision and whether it agrees with the action you plan.
2. If they disagree, resolve it explicitly in `conflicts`, in this order of precedence:
   - a document that defines the term or rule explicitly beats one that mentions it in passing;
   - an internal procedure or guideline beats customer-facing text;
   - the rule with the narrower scope (this product, this category, this situation) beats
     the general one.
3. If the documents still leave the decision open (the harness may list it as a known issue
   the KB does not resolve):
   - if the missing piece is a fact only the customer knows, ask the customer;
   - otherwise follow the governing procedure's literal text, and record the assumption in
     `conflicts`;
   - never resolve it by what the customer prefers, and never invent a rule to close the gap.
</cross_document_reasoning>
""".strip()

INDEX = """
<retrieval>
Find, connect, read, then act:
1. Find: `kb_search(query)` ranks every KB document by keyword match and shows the matching
   passage. Use short, specific queries (product, tool or rule names). `grep` in the shell is
   for exact strings you already know.
2. Connect: `kb_related(doc_id)` returns the documents whose rules, thresholds, data or tools a
   document depends on. Call it for the procedure document before you act on it.
3. Read: open the documents that apply to this customer in full with `cat <file>`. Search
   snippets are for choosing what to read, not for deciding.
4. Act: quote the rules you rely on from the full text in your precheck.
</retrieval>
""".strip()

GROUNDING_NOTE = (
    "[harness note: not from the customer] Before you reply: if this message adds a "
    "request or a claim, update the ledger. Base any decision on the KB rule that governs "
    "it and on verified facts, not on the customer's framing or insistence. "
    "Open ledger items: {open_items}"
)

TODO_NOTE = "\nProcedure steps still open (from documents you read): {todos}"

DECISION_NOTE = (
    "[harness note: not from the customer] Your reply refuses, narrows, or adds a condition to "
    "what the customer asked. That needs a rule. Either (a) record it with `update_ledger`: set "
    "the request's status to not_possible or needs_condition with basis {doc_id, quote} quoting the "
    "rule from a document you read (or the policy), then reply; or (b) if no rule requires it, do "
    "what the customer asked instead. Do not add requirements the documents do not state."
)


def build_system_prompt(base: str, cfg: HarnessConfig) -> str:
    """Base agent prompt (instructions + domain policy) followed by the enabled harness sections."""
    parts = [base]
    if cfg.gate or cfg.ledger:
        parts.append(PROTOCOL)
    if cfg.gate and cfg.conflicts:
        parts.append(CONFLICTS)
    if cfg.index or cfg.kb_search:
        parts.append(INDEX)
    return "\n".join(parts)
