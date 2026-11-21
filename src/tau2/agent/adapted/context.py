"""Context/input builder: what the model sees each turn, and what the harness tracks.

Every incoming message passes through ``ContextBuilder.incoming`` before it enters the
agent's own history. The orchestrator's trajectory objects are never mutated (copies only),
so annotations exist in the agent's context and nowhere else.
"""

from __future__ import annotations

import re
from copy import deepcopy

from tau2.agent.adapted import kb as K
from tau2.agent.adapted.config import HarnessConfig
from tau2.agent.adapted.prompts import GROUNDING_NOTE, TODO_NOTE
from tau2.agent.llm_agent import LLMAgentState
from tau2.data_model.message import AssistantMessage, ToolMessage, UserMessage

_HUMAN_ASK = re.compile(
    r"\b(human|real person|live (agent|person)|representative|supervisor|manager|"
    r"speak (to|with) (someone|a person)|transfer me)\b",
    re.I,
)
_TRANSFER_OFFER = re.compile(
    r"\b(transfer you|transferred to|human agent|live agent|representative|specialist)\b",
    re.I,
)
_GREP_ENTRY = re.compile(r"(?m)^\d+\. [^\n]*\n\s+ID: doc_")


class AdaptedAgentState(LLMAgentState):
    """Agent state: the LLM history plus what the harness has observed (agent-visible only)."""

    ledger: dict = {}
    seen_kb: str = ""  # KB text the model was shown
    seen_tools: str = ""  # non-KB tool output
    seen_customer: str = ""  # customer text
    opened_docs: list[str] = []
    called_tools: list[str] = []  # executed tools (discoverable: inner name)
    offered_transfer: bool = False
    human_requests: int = (
        0  # customer turns asking for a human (policy rule 6 counts to 4)
    )
    passed_prechecks: list[dict] = []
    rejections: dict = {}
    call_names: dict = {}  # tool_call id -> (name, inner name, command)
    todos: list[dict] = []  # procedure steps from workflow docs the model has read
    pending_virtual: list = []  # harness-tool results waiting to join the next tool-result block
    turn_grounded: bool = (
        False  # a restriction this turn was recorded with a verified rule
    )
    bounced: bool = False  # decision gate already bounced once this turn


def add_workflow(cfg: HarnessConfig, doc: str, state: "AdaptedAgentState") -> None:
    """Turn a procedure document's steps into to-do items (once per document)."""
    wf = K.workflows(cfg.workflows_path).get(doc)
    if not wf or any(t["doc"] == doc for t in state.todos):
        return
    for s in wf["steps"]:
        state.todos.append(
            {
                "id": f"{doc}#{s['order']}",
                "doc": doc,
                "order": s["order"],
                "step": s["step"],
                "tool": s.get("tool"),
                "condition": s.get("condition"),
            }
        )


def open_todos(state: "AdaptedAgentState") -> list[str]:
    """Tool steps not yet done, as short labels."""
    done = set(state.called_tools)
    return [
        f"{t['step']} [{t['tool']}]"
        + (f" (if {t['condition']})" if t.get("condition") else "")
        for t in state.todos
        if t.get("tool") and t["tool"] not in done
    ]


class ContextBuilder:
    def __init__(self, cfg: HarnessConfig):
        self.cfg = cfg

    # ---- outgoing (model → world) ----

    def outgoing(self, msg: AssistantMessage, state: AdaptedAgentState) -> None:
        if (msg.content or "").strip() and _TRANSFER_OFFER.search(msg.content):
            state.offered_transfer = True
        for tc in msg.tool_calls or []:
            inner = (
                tc.arguments.get("agent_tool_name")
                if tc.name == "call_discoverable_agent_tool"
                else None
            )
            state.call_names[tc.id] = (tc.name, inner, tc.arguments.get("command", ""))

    # ---- incoming (world → model) ----

    def incoming(self, msg, state: AdaptedAgentState):
        if isinstance(msg, UserMessage):
            return self._customer(msg, state)
        if isinstance(msg, ToolMessage):
            return self._tool_result(msg, state)
        return msg

    def _customer(self, msg: UserMessage, state: AdaptedAgentState):
        text = msg.content or ""
        state.seen_customer += "\n" + text
        if _HUMAN_ASK.search(text):
            state.human_requests += 1
        if self.cfg.ledger and text.strip():
            msg = deepcopy(msg)
            open_items = [
                r.get("description")
                for r in state.ledger.get("requests", [])
                if r.get("status") == "open"
            ]
            msg.content = f"{text}\n\n{GROUNDING_NOTE.format(open_items=open_items or 'none recorded')}"
            if self.cfg.workflows and (todos := open_todos(state)):
                msg.content += TODO_NOTE.format(todos="; ".join(todos[:6]))
        return msg

    def _tool_result(self, msg: ToolMessage, state: AdaptedAgentState):
        name, inner, command = state.call_names.get(msg.id, (None, None, ""))
        content = msg.content or ""
        if name in K.KB_TOOLS:
            if name == "grep" and self.cfg.grep_cap:
                content = self._cap_grep(content)
                if content != msg.content:
                    msg = deepcopy(msg)
                    msg.content = content
            state.seen_kb += "\n" + content
            for d in K.kb().docs_seen(name, command, content):
                if d not in state.opened_docs:
                    state.opened_docs.append(d)
                    if self.cfg.workflows:
                        add_workflow(self.cfg, d, state)
            return msg
        state.seen_tools += "\n" + content
        if not msg.error and not content.lstrip().startswith("Error"):
            state.called_tools.append(inner or name)
        if name == "unlock_discoverable_agent_tool" and content.startswith(
            "Tool unlocked"
        ):
            msg = self._annotate_unlock(msg, content)
        return msg

    def _cap_grep(self, content: str) -> str:
        """Keep the top N grep hits in full; list the rest by title and id so context stays usable."""
        # An entry starts at "N. <title>" followed by an "   ID: doc_..." line; numbered lists
        # inside document content do not have that ID line, so they never split an entry.
        starts = [m.start() for m in _GREP_ENTRY.finditer(content)]
        entries = [content[a:b] for a, b in zip(starts, starts[1:] + [len(content)])]
        if len(entries) <= self.cfg.grep_cap:
            return content
        head, tail = entries[: self.cfg.grep_cap], entries[self.cfg.grep_cap :]
        listed = []
        for e in tail:
            first = e.splitlines()[0].strip()
            did = re.search(r"ID:\s*(\S+)", e)
            listed.append(f"{first}  [ID: {did.group(1) if did else '?'}]")
        return (
            "".join(head)
            + f"\n[harness] {len(tail)} more matching documents (content not shown; "
            "read one with KB_search or a narrower grep):\n" + "\n".join(listed)
        )

    def _annotate_unlock(self, msg: ToolMessage, content: str) -> ToolMessage:
        tool = content.split("\n", 1)[0].removeprefix("Tool unlocked: ").strip()
        notes = []
        if self.cfg.derived:
            docs, refs = K.kb().tool_docs.get(tool, []), K.kb().tool_refs.get(tool, [])
            if docs or refs:
                notes.append(
                    f"[harness] Documents that name this tool: {docs}. Documents its description "
                    f"refers to: {refs}. Rules for using it may also be in product, eligibility, fee "
                    "or guideline docs. Precheck is required before calling it."
                )
        if ct := K.cards_text(self.cfg, tool):
            notes.append(f"[harness] {ct}")
        if self.cfg.early_checklist:
            # Show the whole checklist now, so the first precheck can pass.
            if self.cfg.contracts and (c := K.contract_text(self.cfg, tool)):
                notes.append(f"[harness] {c}")
            if self.cfg.known_issues and (it := K.issues_text(self.cfg, tool)):
                notes.append(f"[harness] {it}")
        if not notes:
            return msg
        msg = deepcopy(msg)
        msg.content = content + "\n\n" + "\n\n".join(notes)
        return msg
