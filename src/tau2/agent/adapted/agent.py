"""The adapted agent: LLMAgent plus context builder, pre-action gate and harness tools.

Information boundary: the harness uses only what the agent itself saw (its tool results, the
KB the agent can read, the policy). The ``task`` passed to agent factories is ignored.
Harness tools are answered inside the agent and logged under ``raw_data["harness"]`` of the
assistant message finally returned to the orchestrator.
"""

from __future__ import annotations

import json
from typing import Optional

from loguru import logger

from tau2.agent.adapted import kb as K
from tau2.agent.adapted.config import HarnessConfig
from tau2.agent.adapted.context import AdaptedAgentState, ContextBuilder
from tau2.agent.adapted.gate import Gate, gated_key
from tau2.agent.adapted.prompts import build_system_prompt
from tau2.agent.adapted.virtual_tools import (
    VIRTUAL_TOOLS,
    kb_related,
    kb_search,
    precheck,
    update_ledger,
)
from tau2.agent.llm_agent import LLMAgent
from tau2.data_model.message import AssistantMessage, MultiToolMessage, ToolMessage
from tau2.environment.tool import Tool, as_tool
from tau2.utils.llm_utils import generate


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
        super().__init__(
            tools=list(tools) + virtual,
            domain_policy=domain_policy,
            llm=llm,
            llm_args=llm_args,
            **kw,
        )
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
        return generate(
            model=self.llm,
            tools=self.tools,
            messages=state.system_messages + state.messages,
            call_name="agent_response",
            **self.llm_args,
        )

    def generate_next_message(self, message, state: AdaptedAgentState):
        for m in (
            message.tool_messages
            if isinstance(message, MultiToolMessage)
            else [message]
        ):
            state.messages.append(self.context.incoming(m, state))

        events, cost, usage = [], 0.0, {"prompt_tokens": 0, "completion_tokens": 0}
        for _ in range(self.cfg.max_internal_calls):
            out = self._llm(state)
            cost += out.cost or 0.0
            for k in usage:
                usage[k] += (out.usage or {}).get(k, 0) or 0
            calls = out.tool_calls or []
            virtual = [tc for tc in calls if tc.name in VIRTUAL_TOOLS]
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
                self.context.outgoing(out, state)
                out.cost, out.usage = cost, usage
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
        if tc.name == "update_ledger":
            state.ledger = {
                "requests": tc.arguments.get("requests") or [],
                "customer_claims": tc.arguments.get("customer_claims") or [],
            }
            events.append({"type": "ledger", "ledger": state.ledger})
            return "Ledger stored:\n" + json.dumps(state.ledger, indent=1)[:3000]
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
