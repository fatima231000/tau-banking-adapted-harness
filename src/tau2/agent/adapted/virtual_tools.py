"""Harness tools exposed to the model. Schemas only: the agent handles them internally and
they never reach the environment, so they cannot affect DB-state grading."""

from __future__ import annotations


def precheck(
    action_tool: str,
    planned_arguments: dict,
    governing_rules: list[dict],
    preconditions: list[dict],
    derived_arguments: list[dict] = None,
    cross_doc_check: list[dict] = None,
    workflow_steps: list[dict] = None,
    issue_checks: list[dict] = None,
    conflicts: list[dict] = None,
    open_subtasks: list[str] = None,
    customer_consent_for_transfer: bool = False,
    transfer_basis: str = None,
) -> str:
    """Pre-action check for ONE state-changing call. Must pass before the call is executed.

    Args:
        action_tool: Exact name of the tool you will call next: the discoverable tool name
            (e.g. "close_debit_card_4721") when using call_discoverable_agent_tool, otherwise
            "give_discoverable_user_tool:<user tool name>", "transfer_to_human_agents" or
            "change_user_email".
        planned_arguments: The exact arguments you will pass to that tool (for a
            discoverable agent tool: the inner arguments, not the JSON string wrapper).
        governing_rules: Rules that govern this action. Each item:
            {"doc_id": "<document id, or 'policy'>", "quote": "<exact text>"}.
        preconditions: Every condition the rules impose. Each item: {"condition": str,
            "rule_doc_id": str,
            "status": "met" | "not_met" | "unknown" | "customer_attested" (the customer's
            statement stands because no available tool can confirm it, or the lookup made
            does not cover it),
            "evidence_source": "tool_result" | "kb_doc" | "customer_statement",
            "evidence": str, "verifying_tool": "<tool that can confirm it, or null>"}.
        derived_arguments: For each planned argument whose value was derived rather than
            copied from a tool/KB output. Each item: {"argument": str,
            "basis": "kb_rule" | "customer_statement", "doc_id": str, "quote": str,
            "reasoning": str}.
        cross_doc_check: Required when you cite two or more documents. One item per cited
            document: {"doc_id": str, "says": "<what it says about this decision>",
            "consistent": true | false (does it agree with the planned action)}.
        workflow_steps: Earlier steps of a procedure you are following (ids from your to-do list,
            e.g. "doc_x#2"). Each item: {"id": str, "status": "done" | "not_applicable",
            "why": str}.
        issue_checks: One item per known issue the harness listed for this tool:
            {"id": "I1", "applies": true | false, "handling": "how you handled it"}.
        conflicts: Documents that disagree, and how you resolved it. Each item:
            {"doc_ids": [str], "resolution": str}. Required if any cross_doc_check item is
            not consistent.
        open_subtasks: Customer requests still unresolved after this action.
        customer_consent_for_transfer: For transfers only: the customer agreed to be transferred.
        transfer_basis: For transfers only: "customer_request" (the customer insists on a human),
            "outside_capabilities" (no KB action can resolve it), or "kb_scenario_rule" (a KB
            document prescribes a transfer for this situation; cite it in governing_rules).

    Returns:
        "PRECHECK PASSED" or a list of problems to fix before trying again.
    """
    return ""


def update_ledger(requests: list[dict], customer_claims: list[dict] = None) -> str:
    """Replace the task ledger: the customer's requests and unverified claims.

    Args:
        requests: Every request the customer has made in this conversation. Each item:
            {"id": str, "description": str,
             "status": "open" | "done" | "declined_by_customer" | "not_possible" |
                       "needs_condition",
             "customer_quote": str  (required for declined_by_customer: the customer's own
                       words declining it)}.
            A request, once recorded, stays in the ledger: change its status, never drop it.
            not_possible and needs_condition need a decision_record first.
        customer_claims: Facts the customer stated. Each item: {"claim": str,
            "status": "unverified" | "verified" | "contradicted", "how": str}.

    Returns:
        The stored ledger.
    """
    return ""


def kb_related(doc_id: str) -> str:
    """Find the knowledge-base documents a document depends on, and those that depend on it.

    Uses a precomputed index of the knowledge base: for each document, what it needs from
    elsewhere (rules, data, thresholds, tools, definitions) matched to the documents that
    provide them, plus documents that use the same tools. Call it after reading a procedure
    document, before acting on it, to find the rules in other documents that also apply.

    Args:
        doc_id: The document id, as shown in search results or file listings.

    Returns:
        Related documents with the reason for each link.
    """
    return ""


def kb_search(query: str, k: int = 8) -> str:
    """Search the whole knowledge base by keywords (BM25) and get the best-matching documents.

    Returns, for each document, its title, id, file name and the passage that best matches the
    query. Use short, specific queries (product names, tool names, rule terms). Then read the
    documents you need in full with the shell (cat <file>).

    Args:
        query: Keywords to search for, e.g. "close debit card pending transactions".
        k: Number of documents to return (default 8).

    Returns:
        Ranked documents with id, file name and a matching passage.
    """
    return ""


def decision_record(
    kind: str,
    request: str,
    rules: list[dict],
    trigger_evidence: list[dict] = None,
    criteria: list[dict] = None,
    candidates: list[dict] = None,
) -> str:
    """Record a decision BEFORE you tell it to the customer. Required for: refusing or narrowing a
    request, adding a condition to it, giving an eligibility verdict, or recommending an option.

    Args:
        kind: "refuse" | "narrow" | "condition" | "eligible" | "not_eligible" | "recommend".
        request: The customer request this decision is about (as in your ledger).
        rules: Rules that decide it. Each item: {"doc_id": "<document id, or 'policy'>",
            "quote": "<exact text>"}.
        trigger_evidence: For refuse / narrow / condition / not_eligible: why the rule applies NOW.
            Each item: {"source": "tool_result" | "customer", "text": "<verbatim text from a tool
            result or the customer's message>"}.
        criteria: For eligible / not_eligible: every eligibility criterion the rules state. Each
            item: {"criterion": str, "status": "met" | "not_met", "evidence_source":
            "tool_result" | "kb_doc" | "customer_statement", "evidence": str,
            "verifying_tool": "<tool that can confirm it, or null>"}.
        candidates: For recommend: every option from the documents you read that could satisfy
            the request. Each item: {"option": str, "doc_id": str, "assessment": "<value net of
            fees, and which stated requirements it meets or misses>"}.

    Returns:
        "DECISION RECORDED" or the problems to fix first.
    """
    return ""


VIRTUAL_TOOLS = {
    "precheck",
    "update_ledger",
    "kb_related",
    "kb_search",
    "decision_record",
}
