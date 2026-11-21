"""Pre-action gate: which calls are gated, and the mechanical checks a precheck must pass."""

from __future__ import annotations

import json
from typing import Any, Optional

from tau2.agent.adapted import kb as K
from tau2.agent.adapted.config import HarnessConfig
from tau2.agent.adapted.context import AdaptedAgentState
from tau2.data_model.message import ToolCall

# Lookups that satisfy each other as prerequisites (same purpose, different key).
_EQUIVALENT = {
    "get_user_information_by_id": "identity",
    "get_user_information_by_name": "identity",
    "get_user_information_by_email": "identity",
    "log_verification": "identity",
}
_FREE_TEXT_ARGS = {"summary", "arguments", "notes", "description"}
_TRANSFER_BASES = ("customer_request", "outside_capabilities", "kb_scenario_rule")
_POLICY_RULE_6 = (
    "'If the user asks for a human agent 4 times, then you may invoke the "
    "transfer_to_human_agents tool.'"
)


def gated_key(tc: ToolCall) -> Optional[str]:
    if tc.name == "call_discoverable_agent_tool":
        inner = tc.arguments.get("agent_tool_name", "")
        return inner if inner in K.kb().write_tools else None
    if tc.name == "give_discoverable_user_tool":
        return f"give_discoverable_user_tool:{tc.arguments.get('discoverable_tool_name', '')}"
    if tc.name in ("transfer_to_human_agents", "change_user_email"):
        return tc.name
    return None


def call_args(tc: ToolCall) -> dict:
    if tc.name == "call_discoverable_agent_tool":
        raw = tc.arguments.get("arguments", "{}")
        try:
            return json.loads(raw) if isinstance(raw, str) else dict(raw or {})
        except Exception:
            return {"__unparseable__": raw}
    if tc.name == "give_discoverable_user_tool":
        return {}
    return dict(tc.arguments)


def canon(obj: Any) -> str:
    """Order- and number-format-insensitive form (the env parses every number as float)."""

    def fix(x):
        if isinstance(x, bool) or x is None:
            return x
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, dict):
            return {k: fix(v) for k, v in x.items()}
        if isinstance(x, list):
            return [fix(v) for v in x]
        return x

    return json.dumps(fix(obj), sort_keys=True, default=str)


class Gate:
    def __init__(self, cfg: HarnessConfig, system_prompt: str):
        self.cfg = cfg
        self.policy = K.norm(system_prompt)

    def quote_problem(
        self, doc_id: str, quote: str, state: AdaptedAgentState
    ) -> Optional[str]:
        if len(K.norm(quote)) < 12:
            return f"quote from {doc_id} is too short to check; quote the rule itself"
        if doc_id == "policy":
            return (
                None
                if K.norm(quote) in self.policy
                else "quote not found in the policy"
            )
        q = K.md_norm(quote)
        if q in K.md_norm(
            state.seen_kb
        ):  # shown to the model by shell, KB_search or grep
            return None
        did = K.kb().resolve(doc_id) or doc_id
        if did not in state.opened_docs:
            return f"{doc_id} has not been read in this conversation; read it and quote the rule"
        if q not in K.md_norm(K.kb().docs[did]["content"]):
            return f"quote not found in {doc_id}; quote it exactly"
        return None

    def check(self, args: dict, state: AdaptedAgentState) -> list[str]:
        problems: list[str] = []
        tool = args.get("action_tool", "")
        rules = args.get("governing_rules") or []
        derived = {d.get("argument"): d for d in (args.get("derived_arguments") or [])}
        problems += self._prerequisites(tool, state)
        if not rules:
            problems.append(
                "governing_rules is empty: cite the rule(s) that govern this action"
            )
        problems += [
            f"governing rule: {p}"
            for r in rules
            if (
                p := self.quote_problem(
                    str(r.get("doc_id", "")), str(r.get("quote", "")), state
                )
            )
        ]
        problems += self._preconditions(args, state)
        if self.cfg.derived:
            problems += self._derived(args, derived, state)
        if self.cfg.conflicts:
            problems += self._cross_doc(args, rules, derived)
        if tool == "transfer_to_human_agents":
            problems += self._transfer(args, rules, state)
        if self.cfg.workflows:
            problems += self._workflow(tool, args, state)
        if self.cfg.known_issues:
            problems += self._issues(tool, args)
        if self.cfg.arg_rules:
            problems += self._arg_rules(tool, args)
        if self.cfg.decisions:
            problems += optional_free_text(
                tool, args.get("planned_arguments") or {}, state
            )
        return problems

    @staticmethod
    def _workflow(tool: str, args: dict, state: AdaptedAgentState) -> list[str]:
        """Earlier tool steps of a procedure the model read must be done, or marked n/a with a reason."""
        name = tool.split(":")[-1]
        marked = {str(w.get("id")): w for w in (args.get("workflow_steps") or [])}
        done = set(state.called_tools)
        out = []
        for here in [t for t in state.todos if t.get("tool") == name]:
            for t in state.todos:
                if (
                    t["doc"] != here["doc"]
                    or t["order"] >= here["order"]
                    or not t.get("tool")
                    or t["tool"] in done
                ):
                    continue
                m = marked.get(t["id"])
                if not m:
                    out.append(
                        f"procedure step {t['id']} comes before this one and is not done: "
                        f"'{t['step']}' [{t['tool']}]. Do it first, or mark it in workflow_steps "
                        "as not_applicable with the reason"
                    )
                elif m.get("status") == "done":
                    out.append(
                        f"workflow step {t['id']} is marked done but {t['tool']} was not called"
                    )
                elif (
                    m.get("status") == "not_applicable"
                    and not str(m.get("why", "")).strip()
                ):
                    out.append(
                        f"workflow step {t['id']} is marked not_applicable without a reason"
                    )
        return out

    def _issues(self, tool: str, args: dict) -> list[str]:
        items = K.issues_for(self.cfg, tool)
        checks = {str(c.get("id")): c for c in (args.get("issue_checks") or [])}
        missing = [
            i["id"]
            for i in items
            if i["id"] not in checks
            or not str(checks[i["id"]].get("handling", "")).strip()
        ]
        if not missing:
            return []
        topics = "; ".join(
            f"{i['id']}: {i['topic']}" for i in items if i["id"] in missing
        )
        return [
            f"known issues not addressed in issue_checks ({topics}). For each give "
            '{"id", "applies": true|false, "handling": how you handled it}'
        ]

    def _arg_rules(self, tool: str, args: dict) -> list[str]:
        planned = args.get("planned_arguments") or {}
        out = []
        for r in K.arg_rules(self.cfg.arg_rules_path):
            if r["tool"] != tool or r["argument"] not in planned:
                continue
            v = str(planned[r["argument"]]).strip()
            if r.get("must_end_with") and not v.endswith(r["must_end_with"]):
                out.append(
                    f'argument {r["argument"]}={v!r} breaks a KB rule: {r["doc_id"]}: "{r["quote"]}"'
                )
        return out

    def _prerequisites(self, tool: str, state: AdaptedAgentState) -> list[str]:
        if not self.cfg.contracts:
            return []
        done = set(state.called_tools) | {
            _EQUIVALENT[t] for t in state.called_tools if t in _EQUIVALENT
        }
        return [
            f'prerequisite not done: call {p["tool"]} first ({p["purpose"]}). KB {p["doc_id"]}: "{p["quote"]}"'
            for p in K.contracts(self.cfg.contracts_path)
            .get(tool, {})
            .get("prerequisite_calls", [])
            if p["tool"] not in done and _EQUIVALENT.get(p["tool"]) not in done
        ]

    @staticmethod
    def _preconditions(args: dict, state: AdaptedAgentState) -> list[str]:
        out = []
        for c in args.get("preconditions") or []:
            cond, vt, status = (
                c.get("condition", "?"),
                c.get("verifying_tool"),
                c.get("status"),
            )
            has_tool = bool(vt) and vt not in ("null", "None")
            unverified = (
                c.get("evidence_source") == "customer_statement"
                and has_tool
                and vt not in state.called_tools
            )
            if status == "customer_attested":
                # Allowed once verification was tried, or when no tool can check the claim:
                # a lookup that finds nothing must not block a claim it cannot cover.
                if c.get("evidence_source") != "customer_statement":
                    out.append(
                        f"precondition '{cond}': customer_attested needs evidence_source customer_statement"
                    )
                elif unverified:
                    out.append(
                        f"precondition '{cond}' rests on the customer's word but {vt} can verify it: call it first"
                    )
                continue
            if status != "met":
                out.append(
                    f"precondition '{cond}' is {status}: resolve it (look it up, ask, or do not proceed). "
                    "If no available tool can confirm the customer's statement, or the lookup you made "
                    "does not cover it, use status customer_attested"
                )
            if unverified:
                out.append(
                    f"precondition '{cond}' rests on the customer's word but {vt} can verify it: call it first"
                )
        return out

    def _derived(
        self, args: dict, derived: dict, state: AdaptedAgentState
    ) -> list[str]:
        out = [
            f"derived argument '{d.get('argument')}': {p}"
            for d in derived.values()
            if d.get("basis") == "kb_rule"
            and (
                p := self.quote_problem(
                    str(d.get("doc_id", "")), str(d.get("quote", "")), state
                )
            )
        ]
        seen = state.seen_tools + state.seen_kb
        for k, v in (args.get("planned_arguments") or {}).items():
            if k in _FREE_TEXT_ARGS or k in derived or len(str(v).split()) >= 6:
                continue
            forms = K.value_forms(v)
            if (
                forms
                and not any(f in seen for f in forms)
                and not any(f in state.seen_customer for f in forms)
            ):
                out.append(
                    f"argument '{k}'={v!r} does not appear in any tool or KB output: add it to "
                    "derived_arguments with the rule you applied (or basis customer_statement)"
                )
        return out

    @staticmethod
    def _cross_doc(args: dict, rules: list, derived: dict) -> list[str]:
        cited = {
            K.kb().resolve(str(r.get("doc_id", ""))) or str(r.get("doc_id", ""))
            for r in rules
        }
        cited |= {
            K.kb().resolve(str(d.get("doc_id", ""))) or str(d.get("doc_id", ""))
            for d in derived.values()
            if d.get("basis") == "kb_rule"
        }
        cited -= {"policy", "", "None"}
        if len(cited) < 2:
            return []
        checks = args.get("cross_doc_check") or []
        covered = {
            K.kb().resolve(str(c.get("doc_id", ""))) or str(c.get("doc_id", ""))
            for c in checks
        }
        out = []
        if missing := sorted(cited - covered):
            out.append(
                f"you cite {len(cited)} documents: add a cross_doc_check entry for each "
                f"(what it says about this decision, and whether it is consistent): missing {missing}"
            )
        if any(c.get("consistent") is False for c in checks) and not args.get(
            "conflicts"
        ):
            out.append(
                "cross_doc_check marks a document as inconsistent: record the conflict and its "
                "resolution in `conflicts` before acting"
            )
        return out

    @staticmethod
    def _transfer(args: dict, rules: list, state: AdaptedAgentState) -> list[str]:
        out = []
        if not args.get("customer_consent_for_transfer"):
            out.append("transfer needs the customer's consent: ask first")
        if not state.offered_transfer:
            out.append("you have not offered a transfer to the customer yet")
        basis = args.get("transfer_basis")
        if basis not in _TRANSFER_BASES:
            out.append("set transfer_basis: " + " | ".join(_TRANSFER_BASES))
        elif basis == "customer_request" and state.human_requests < 4:
            out.append(
                f"the customer has asked for a human {state.human_requests} time(s); policy: "
                f"{_POLICY_RULE_6} Help with what is within your capabilities first"
            )
        elif basis == "kb_scenario_rule" and not any(
            str(r.get("doc_id", "")) != "policy" for r in rules
        ):
            out.append(
                "kb_scenario_rule needs a governing rule quoted from a KB document (not the policy)"
            )
        if args.get("open_subtasks"):
            out.append(
                f"open requests remain {args['open_subtasks']}: handle what you can before transferring"
            )
        open_items = [
            r.get("description")
            for r in state.ledger.get("requests", [])
            if r.get("status") == "open"
        ]
        if len(open_items) > 1:
            out.append(
                f"ledger has open requests {open_items}: resolve or confirm them before transferring"
            )
        return out

    def match(
        self, tc: ToolCall, key: str, state: AdaptedAgentState, taken: set
    ) -> Optional[int]:
        planned = canon(call_args(tc))
        for i, p in enumerate(state.passed_prechecks):
            if i in taken or p.get("action_tool") not in (key, key.split(":")[-1]):
                continue
            if key.startswith("give_") or tc.name == "transfer_to_human_agents":
                return i
            if canon(p.get("planned_arguments") or {}) == planned:
                return i
        return None

    def block_hint(self, key: str) -> str:
        hint = ""
        if self.cfg.derived and ":" not in key:
            hint = (
                f" Documents that name {key}: {K.kb().tool_docs.get(key, [])}; documents its "
                f"description refers to: {K.kb().tool_refs.get(key, [])}."
            )
        if self.cfg.contracts and (ct := K.contract_text(self.cfg, key)):
            hint += f"\n{ct}\nYour precheck must cover these."
        if self.cfg.known_issues and (it := K.issues_text(self.cfg, key)):
            hint += f"\n{it}"
        return hint[:6000]


# ---- v8: decision records (negative / verdict / recommendation prechecks) ---------------

_DECISION_KINDS = (
    "refuse",
    "narrow",
    "condition",
    "eligible",
    "not_eligible",
    "recommend",
)
_NEEDS_TRIGGER = ("refuse", "narrow", "condition", "not_eligible")


def check_decision(gate: "Gate", args: dict, state: AdaptedAgentState) -> list[str]:
    """A decision told to the customer must rest on a rule that applies now, with evidence."""
    out = []
    kind = args.get("kind")
    if kind not in _DECISION_KINDS:
        return ["kind must be one of " + " | ".join(_DECISION_KINDS)]
    rules = args.get("rules") or []
    if not rules:
        out.append("rules is empty: quote the rule that decides this")
    out += [
        f"rule: {p}"
        for r in rules
        if (
            p := gate.quote_problem(
                str(r.get("doc_id", "")), str(r.get("quote", "")), state
            )
        )
    ]
    if kind in _NEEDS_TRIGGER:
        ev = args.get("trigger_evidence") or []
        ok = []
        for e in ev:
            text = K.md_norm(e.get("text", ""))
            pool = (
                state.seen_customer
                if e.get("source") == "customer"
                else state.seen_tools
            )
            if len(text) >= 12 and text in K.md_norm(pool):
                ok.append(e)
        if not ok:
            out.append(
                "trigger_evidence: quote, verbatim, the tool result or customer message showing that "
                "the rule applies to this customer now. If nothing shows it, the restriction does not "
                "apply: do what the customer asked"
            )
    if kind in ("eligible", "not_eligible"):
        crit = args.get("criteria") or []
        if not crit:
            out.append(
                "criteria is empty: list every eligibility criterion the rules state, with evidence"
            )
        for c in crit:
            name, vt = c.get("criterion", "?"), c.get("verifying_tool")
            if c.get("status") not in ("met", "not_met"):
                out.append(
                    f"criterion '{name}' is {c.get('status')}: check it before giving a verdict"
                )
            if (
                c.get("evidence_source") == "customer_statement"
                and vt
                and vt not in ("null", "None")
                and vt not in state.called_tools
            ):
                out.append(
                    f"criterion '{name}' rests on the customer's word but {vt} can check it: call it first"
                )
            if (
                c.get("evidence_source") == "tool_result"
                and vt
                and vt not in ("null", "None")
                and vt not in state.called_tools
            ):
                out.append(
                    f"criterion '{name}' cites {vt} as evidence but it has not been called"
                )
    if kind == "recommend":
        cand = args.get("candidates") or []
        if len(cand) < 2:
            out.append(
                "candidates: list every option the documents you read offer for this request (at "
                "least two), each with its value net of fees and the stated requirements it meets"
            )
        for c in cand:
            d = K.kb().resolve(str(c.get("doc_id", ""))) or str(c.get("doc_id", ""))
            if d not in state.opened_docs and d != "policy":
                out.append(
                    f"candidate '{c.get('option')}' cites {c.get('doc_id')}, which you have not read"
                )
    return out


def optional_free_text(tool: str, planned: dict, state: AdaptedAgentState) -> list[str]:
    """Optional free-text arguments the customer did not supply change stored records needlessly."""
    import inspect

    from tau2.domains.banking_knowledge import tools as T

    fn = getattr(T.KnowledgeTools, tool, None)
    if fn is None:
        return []
    out = []
    for name, p in inspect.signature(fn).parameters.items():
        if (
            name == "self"
            or p.default is inspect.Parameter.empty
            or name not in planned
        ):
            continue
        v = planned[name]
        if (
            isinstance(v, str)
            and len(v.split()) >= 3
            and K.md_norm(v) not in K.md_norm(state.seen_customer)
        ):
            out.append(
                f"optional argument '{name}' is free text you wrote ({v!r}): leave it out unless the "
                "customer supplied this wording; the default applies"
            )
    return out
