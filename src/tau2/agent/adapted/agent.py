"""The adapted agent: LLMAgent plus context builder, pre-action gate and harness tools.

Information boundary: the harness uses only what the agent itself saw (its tool results, the
KB the agent can read, the policy). The ``task`` passed to agent factories is ignored.
Harness tools are answered inside the agent and logged under ``raw_data["harness"]`` of the
assistant message finally returned to the orchestrator.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Optional

from loguru import logger

from tau2.agent.adapted import kb as K
from tau2.agent.adapted.config import HarnessConfig
from tau2.agent.adapted.context import AdaptedAgentState, ContextBuilder
from tau2.agent.adapted.gate import Gate, check_decision, gated_key
from tau2.agent.adapted.prompts import (
    CHECKER_PROMPT,
    DECISION_NOTE,
    build_system_prompt,
)
from tau2.agent.adapted.virtual_tools import (
    VIRTUAL_TOOLS,
    decision_record,
    kb_related,
    kb_search,
    load_skill,
    precheck,
    skill_search,
    update_ledger,
)
from tau2.agent.llm_agent import LLMAgent
from tau2.data_model.message import (
    AssistantMessage,
    MultiToolMessage,
    SystemMessage,
    ToolMessage,
    UserMessage,
)
from tau2.environment.tool import Tool, as_tool
from tau2.utils.llm_utils import generate

# Text that states a decision: refuses, narrows, adds a condition, gives a verdict, recommends.
_RESTRICTS = re.compile(
    r"\b(unable to|can(?:no|')t (?:help|do|process|provide|give|issue|open|close|offer|approve|file|"
    r"send|share|update|transfer|change|apply|add|remove|dispute|refund|credit|waive)"
    r"|not (?:eligible|able to|possible|permitted|allowed)|(?:need|have) to (?:first )?verify"
    r"|must (?:first )?(?:verify|confirm|provide)|before I can|won't be able|I'm not able"
    r"|(?:nothing|no action) (?:needs|is needed)|doesn't (?:need|qualify|apply)|instead of)\b",
    re.I,
)
_VERDICT = re.compile(
    r"\b(you(?:'re| are) (?:eligible|qualified)|you qualify|qualifies|you can (?:submit|open|apply|get|"
    r"use|have)|(?:I|I'd|I would) recommend|my recommendation|best (?:option|choice|fit|match)|"
    r"the right (?:account|card|option) for you)\b",
    re.I,
)


class AdaptedLLMAgent(LLMAgent):
    def __init__(
        self,
        tools: list[Tool],
        domain_policy: str,
        llm: str,
        llm_args=None,
        config: Optional[HarnessConfig] = None,
        **kw,
    ):
        self.cfg = config or HarnessConfig.from_env()
        virtual = []
        if self.cfg.gate:
            virtual.append(as_tool(precheck))
        if self.cfg.ledger:
            virtual.append(as_tool(update_ledger))
        if self.cfg.index:
            virtual.append(as_tool(kb_related))
        if self.cfg.kb_search:
            virtual.append(as_tool(kb_search))
        if self.cfg.decisions:
            virtual.append(as_tool(decision_record))
        if self.cfg.skills:
            virtual += [as_tool(skill_search), as_tool(load_skill)]
        super().__init__(
            tools=list(tools) + virtual,
            domain_policy=domain_policy,
            llm=llm,
            llm_args=llm_args,
            **kw,
        )
        self._candidate = self.cfg.candidate()
        self.context = ContextBuilder(self.cfg)
        self.gate = Gate(self.cfg, self.system_prompt)

    @property
    def system_prompt(self) -> str:
        return build_system_prompt(super().system_prompt, self.cfg)

    def get_init_state(self, message_history=None) -> AdaptedAgentState:
        base = super().get_init_state(message_history)
        return AdaptedAgentState(
            system_messages=base.system_messages, messages=base.messages
        )

    def _llm(self, state: AdaptedAgentState) -> AssistantMessage:
        extra = {}
        if self.cfg.replay_thinking:
            extra["replay_thinking"] = True
        if self.cfg.cache:
            # Cache the system prompt and the conversation so far: harness turns re-send the same prefix.
            extra["cache_control_injection_points"] = [
                {"location": "message", "role": "system"},
                {"location": "message", "index": -1},
            ]
        return generate(
            model=self.llm,
            tools=self.tools,
            messages=state.system_messages + state.messages,
            call_name="agent_response",
            **self.llm_args,
            **extra,
        )

    def generate_next_message(self, message, state: AdaptedAgentState):
        incoming = (
            message.tool_messages
            if isinstance(message, MultiToolMessage)
            else [message]
        )
        if isinstance(message, UserMessage):
            state.turn_grounded, state.bounced = False, False
            state.checker_rejections = 0
        # Results of harness tools that shared a turn with real calls go in the same tool-result block.
        state.messages.extend(state.pending_virtual)
        state.pending_virtual = []
        for m in incoming:
            state.messages.append(self.context.incoming(m, state))

        events, cost, usage = [], 0.0, {"prompt_tokens": 0, "completion_tokens": 0}
        for _ in range(self.cfg.max_internal_calls):
            out = self._llm(state)
            cost += out.cost or 0.0
            for k in usage:
                usage[k] += (out.usage or {}).get(k, 0) or 0
            calls = out.tool_calls or []
            virtual = [tc for tc in calls if tc.name in VIRTUAL_TOOLS]
            real = [tc for tc in calls if tc.name not in VIRTUAL_TOOLS]

            # Lean check (no forms): required lookups before a write, request count before a transfer.
            if self.cfg.lean_gate and real and (held := self._lean_block(real, state)):
                state.messages.append(out)
                for tc in calls:
                    if tc.id in held:
                        reply = held[tc.id]
                        events.append(
                            {"type": "lean_block", "tool": tc.name, "why": reply[:200]}
                        )
                    elif tc.name in VIRTUAL_TOOLS:
                        reply = self._answer(tc, [], state, events)
                    else:
                        reply = "NOT EXECUTED: another call in this turn was held. Re-issue this call."
                    state.messages.append(
                        ToolMessage(
                            id=tc.id, role="tool", content=reply, requestor="assistant"
                        )
                    )
                continue

            # Harness tools (not precheck) mixed with real calls: answer them now, send the rest.
            if (
                self.cfg.mix_virtual
                and virtual
                and real
                and not any(tc.name == "precheck" for tc in virtual)
            ):
                blocked, matched, overrides = (
                    self._screen(real, state) if self.cfg.gate else ([], {}, [])
                )
                if not blocked:
                    state.messages.append(out)
                    for tc in virtual:
                        reply = self._answer(tc, [], state, events)
                        state.pending_virtual.append(
                            ToolMessage(
                                id=tc.id,
                                role="tool",
                                content=reply,
                                requestor="assistant",
                            )
                        )
                    for idx in sorted(matched.values(), reverse=True):
                        events.append(
                            {
                                "type": "gate_pass",
                                "action": state.passed_prechecks[idx].get(
                                    "action_tool"
                                ),
                            }
                        )
                        state.passed_prechecks.pop(idx)
                    events += [
                        {"type": "gate_override", "action": k} for k in overrides
                    ]
                    sent = deepcopy(out)
                    sent.tool_calls = real
                    self.context.outgoing(sent, state)
                    sent.cost, sent.usage = cost, usage
                    sent.raw_data = {
                        **(out.raw_data or {}),
                        "harness": events
                        + [
                            {
                                "type": "mixed_turn",
                                "virtual": [tc.name for tc in virtual],
                            }
                        ],
                    }
                    return sent, state

            # Self-check from an evolved candidate: the agent re-reads its own draft reply once
            # before it is sent. Nothing is blocked; the second answer goes out whatever it says.
            if (
                (review := self._candidate.get("review"))
                and not calls
                and not state.bounced
            ):
                state.bounced = True
                state.messages.append(out)
                state.messages.append(UserMessage(role="user", content=review))
                events.append(
                    {"type": "self_check", "draft": (out.content or "")[:300]}
                )
                continue

            # Decision gate: a refusal or added condition needs a rule behind it (one bounce per turn).
            if (
                self.cfg.decision_gate
                and not calls
                and not state.bounced
                and not state.turn_grounded
                and (
                    _RESTRICTS.search(out.content or "")
                    or (self.cfg.decisions and _VERDICT.search(out.content or ""))
                )
            ):
                state.bounced = True
                state.messages.append(out)
                state.messages.append(UserMessage(role="user", content=DECISION_NOTE))
                events.append(
                    {"type": "decision_bounce", "text": (out.content or "")[:300]}
                )
                continue

            blocked, matched, overrides = (
                self._screen(calls, state)
                if (self.cfg.gate and not virtual)
                else ([], {}, [])
            )
            if not virtual and not blocked:
                for idx in sorted(
                    matched.values(), reverse=True
                ):  # consume only when all pass
                    events.append(
                        {
                            "type": "gate_pass",
                            "action": state.passed_prechecks[idx].get("action_tool"),
                        }
                    )
                    state.passed_prechecks.pop(idx)
                events += [{"type": "gate_override", "action": k} for k in overrides]
                if (
                    self.cfg.skills
                ):  # exploit (card in context) or explore (no card) at each write
                    events += [
                        {
                            "type": "write_mode",
                            "tool": k,
                            "card_loaded": k in state.loaded_skills,
                        }
                        for tc in calls
                        if (k := gated_key(tc))
                        and ":" not in k
                        and k != "transfer_to_human_agents"
                    ]
                self.context.outgoing(out, state)
                out.cost, out.usage = cost + state.checker_cost, usage
                state.checker_cost = 0.0
                if events:
                    out.raw_data = {**(out.raw_data or {}), "harness": events}
                state.messages.append(out)
                return out, state
            state.messages.append(
                out
            )  # handled internally: lives in the agent's context only
            for tc in calls:
                reply = self._answer(tc, blocked, state, events)
                state.messages.append(
                    ToolMessage(
                        id=tc.id, role="tool", content=reply, requestor="assistant"
                    )
                )

        logger.warning("adapted harness: internal call budget exhausted")
        msg = AssistantMessage(
            role="assistant",
            content="One moment please, let me check that for you.",
            cost=cost,
            usage=usage,
            raw_data={"harness": events + [{"type": "budget_exhausted"}]},
        )
        state.messages.append(msg)
        return msg, state

    def _check_independently(
        self, record: dict, state: AdaptedAgentState
    ) -> tuple[str, str]:
        """Maker/checker: a fresh model call that sees only the request, the decision, and the cited
        documents (not the agent's reasoning), and judges the decision against the documents."""
        docs = []
        for d in {
            str(x.get("doc_id", ""))
            for x in (record.get("rules") or []) + (record.get("candidates") or [])
        }:
            did = K.kb().resolve(d)
            if did:
                docs.append(
                    f'<document id="{did}">\n# {K.kb().docs[did]["title"]}\n{K.kb().docs[did]["content"]}\n</document>'
                )
        customer = [
            m.content
            for m in state.messages
            if isinstance(m, UserMessage)
            and m.content
            and not m.content.startswith("[harness note")
        ][-4:]
        body = (
            f"<customer_messages>\n"
            + "\n---\n".join(c.split("\n\n[harness note")[0] for c in customer)
            + "\n</customer_messages>\n<decision>\n"
            + json.dumps(record, indent=1)[:6000]
            + "\n</decision>\n"
            + "\n".join(docs)[:14000]
        )
        try:
            r = generate(
                model=self.llm,
                tools=None,
                call_name="decision_checker",
                messages=[
                    SystemMessage(role="system", content=CHECKER_PROMPT),
                    UserMessage(role="user", content=body),
                ],
                **self.llm_args,
            )
            state.checker_cost += r.cost or 0.0
            m = re.search(r"\{.*\}", r.content or "", re.S)
            out = json.loads(m.group(0)) if m else {}
            v = str(out.get("verdict", "uphold")).lower()
            return ("reject" if v == "reject" else "uphold"), str(
                out.get("reason", "")
            )[:800]
        except Exception as e:  # the checker never blocks a conversation by failing
            logger.warning(f"adapted harness: checker failed ({e})")
            return "uphold", ""

    def _lean_block(self, real, state: AdaptedAgentState) -> dict:
        """Calls to hold, with the reason. Bounded: a call is held at most twice (a transfer once)."""
        held = {}
        done = set(state.called_tools)
        if done & {
            "get_user_information_by_id",
            "get_user_information_by_name",
            "get_user_information_by_email",
            "log_verification",
        }:
            done |= {
                "get_user_information_by_id",
                "get_user_information_by_name",
                "get_user_information_by_email",
            }
        for tc in real:
            key = gated_key(tc)
            if key is None:
                continue
            if tc.name == "transfer_to_human_agents":
                if state.human_requests < 4 and state.rejections.get(key, 0) < 1:
                    state.rejections[key] = 1
                    held[tc.id] = (
                        f"NOT EXECUTED YET: the customer has asked for a human {state.human_requests} "
                        "time(s). Policy: if the issue is within your capabilities, help first; after 4 "
                        "requests you may transfer. Transfer now only if no procedure can resolve the "
                        "issue or a document prescribes a transfer for this situation; then re-issue."
                    )
                continue
            missing = [
                p
                for p in K.contracts(self.cfg.contracts_path)
                .get(key, {})
                .get("prerequisite_calls", [])
                if p["tool"] not in done and p["tool"] != "get_current_time"
            ]
            if missing and state.rejections.get(key, 0) < 2:
                state.rejections[key] = state.rejections.get(key, 0) + 1
                seen, lines = set(), []
                for p in missing:
                    if p["tool"] not in seen:
                        seen.add(p["tool"])
                        lines.append(f"- {p['tool']}: {p['purpose']}")
                held[tc.id] = (
                    f"NOT EXECUTED YET: {key} needs these lookups first, each proving one of its "
                    "conditions:\n"
                    + "\n".join(lines)
                    + "\nMake them, check the result, then re-issue."
                )
        return held

    def _screen(self, calls, state: AdaptedAgentState):
        blocked, matched, overrides = [], {}, []
        for tc in calls:
            key = gated_key(tc)
            if key is None:
                continue
            idx = self.gate.match(tc, key, state, set(matched.values()))
            if idx is not None:
                matched[tc.id] = idx
            elif state.rejections.get(key, 0) >= self.cfg.max_rejections:
                overrides.append(key)
            else:
                blocked.append((tc, key))
        for _, key in blocked:
            state.rejections[key] = state.rejections.get(key, 0) + 1
        return blocked, matched, overrides

    def _answer(self, tc, blocked, state: AdaptedAgentState, events: list) -> str:
        if tc.name == "precheck":
            problems = self.gate.check(tc.arguments, state)
            events.append(
                {"type": "precheck", "args": tc.arguments, "problems": problems}
            )
            if problems:
                return "PRECHECK FAILED:\n- " + "\n- ".join(problems)
            state.passed_prechecks.append(tc.arguments)
            return f"PRECHECK PASSED for {tc.arguments.get('action_tool')}. Make that call now, with exactly the planned arguments."
        if tc.name == "decision_record":
            problems = check_decision(self.gate, tc.arguments, state)
            events.append(
                {"type": "decision_record", "args": tc.arguments, "problems": problems}
            )
            if problems:
                return "DECISION RECORD FAILED:\n- " + "\n- ".join(problems)
            if self.cfg.checker and state.checker_rejections < 2:
                verdict, reason = self._check_independently(tc.arguments, state)
                events.append({"type": "checker", "verdict": verdict, "reason": reason})
                if verdict == "reject":
                    state.checker_rejections += 1
                    return (
                        "DECISION REJECTED by an independent reviewer who read the cited documents:\n"
                        f"{reason}\nRevise the decision (or do what the customer asked), then record it again."
                    )
            state.turn_grounded = True
            return "DECISION RECORDED. You may now tell the customer, citing the rule in plain words."
        if tc.name == "update_ledger":
            new = tc.arguments.get("requests") or []
            problems_c = []
            if self.cfg.decisions:
                # Request conservation: a recorded request changes status, it never disappears.
                key = lambda r: str(r.get("id") or r.get("description"))  # noqa: E731
                kept = {key(r) for r in new}
                for old in state.ledger.get("requests", []):
                    if key(old) not in kept and old.get("status") == "open":
                        new.append(old)
                        problems_c.append(
                            f"request '{old.get('description', key(old))}' was dropped; it is kept as open. "
                            "Close it as done, declined_by_customer (with the customer's words) or "
                            "not_possible (after a decision_record)"
                        )
                for r in new:
                    st = r.get("status")
                    if st == "declined_by_customer":
                        q = K.md_norm(r.get("customer_quote", ""))
                        if len(q) < 4 or q not in K.md_norm(state.seen_customer):
                            r["status"] = "open"
                            problems_c.append(
                                f"request '{r.get('description')}' marked declined_by_customer without "
                                "the customer's own words (customer_quote); kept open"
                            )
                    if (
                        st in ("not_possible", "needs_condition")
                        and not state.turn_grounded
                    ):
                        r["status"] = "open"
                        problems_c.append(
                            f"request '{r.get('description')}' marked {st} without a passed "
                            "decision_record this turn; kept open"
                        )
            state.ledger = {
                "requests": new,
                "customer_claims": tc.arguments.get("customer_claims") or [],
            }
            # A restriction (refusal or added condition) must rest on a rule the model has read.
            problems = list(problems_c)
            for r in [] if self.cfg.decisions else state.ledger["requests"]:
                if r.get("status") not in ("not_possible", "needs_condition"):
                    continue
                b = r.get("basis") or {}
                p = (
                    self.gate.quote_problem(
                        str(b.get("doc_id", "")), str(b.get("quote", "")), state
                    )
                    if b
                    else "no basis given"
                )
                if p:
                    problems.append(
                        f"request '{r.get('description', r.get('id'))}' is marked {r.get('status')} but its rule does not check out ({p})"
                    )
                else:
                    state.turn_grounded = True
            events.append(
                {"type": "ledger", "ledger": state.ledger, "problems": problems}
            )
            text = "Ledger stored:\n" + json.dumps(state.ledger, indent=1)[:3000]
            if problems:
                text += (
                    "\nRESTRICTIONS WITHOUT A VERIFIED RULE:\n- "
                    + "\n- ".join(problems)
                    + "\nQuote the rule from a document you read, or do what the customer asked."
                )
            return text
        if tc.name == "kb_search":
            k = int(tc.arguments.get("k") or 8)
            text, shown = K.search_text(
                str(tc.arguments.get("query", "")), max(1, min(k, 15))
            )
            state.seen_kb += "\n" + text  # snippets count as text the model saw
            events.append(
                {
                    "type": "kb_search",
                    "query": tc.arguments.get("query"),
                    "returned": shown,
                }
            )
            return text
        if tc.name == "skill_search":
            text, shown = K.skill_search_text(
                self.cfg, str(tc.arguments.get("situation", ""))
            )
            events.append(
                {
                    "type": "skill_search",
                    "query": tc.arguments.get("situation"),
                    "returned": shown,
                }
            )
            return text
        if tc.name == "load_skill":
            sid = str(tc.arguments.get("skill_id", "")).strip()
            text, fresh = K.skill_text(self.cfg, sid)
            if fresh == "fresh" and sid not in state.loaded_skills:
                state.loaded_skills.append(sid)
            events.append({"type": "load_skill", "skill": sid, "freshness": fresh})
            return text
        if tc.name == "kb_related":
            text, shown = K.related_text(self.cfg, str(tc.arguments.get("doc_id", "")))
            events.append(
                {
                    "type": "kb_related",
                    "doc": tc.arguments.get("doc_id"),
                    "returned": shown,
                }
            )
            return text
        for b, key in blocked:
            if b is tc:
                events.append({"type": "gate_block", "action": key})
                return (
                    f"NOT EXECUTED: {key} is a state-changing action and needs a passing `precheck` for this "
                    f"exact call first (rejection {state.rejections[key]} of {self.cfg.max_rejections})."
                    f"{self.gate.block_hint(key)}"
                )
        return (
            "NOT EXECUTED: harness tools (precheck, update_ledger, kb_related) must be called in a turn of "
            "their own. Re-issue this call next turn."
        )


def create_adapted_agent(tools, domain_policy, **kwargs):
    """Factory for the adapted harness. Ignores ``task`` by design (information boundary)."""
    cfg = HarnessConfig.from_env()
    logger.info(f"adapted harness config: {cfg.summary()}")
    return AdaptedLLMAgent(
        tools=tools,
        domain_policy=domain_policy,
        llm=kwargs.get("llm"),
        llm_args=kwargs.get("llm_args"),
        config=cfg,
        additional_stop_tool_names=kwargs.get(
            "additional_stop_tool_names", frozenset()
        ),
    )
