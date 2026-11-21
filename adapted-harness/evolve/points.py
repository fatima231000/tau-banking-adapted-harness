"""Build the decision-point set from recorded DEV runs (grader-side; DEV only; never agent input).

A decision point is one recorded agent message plus the conversation before it.

  target   a failing run: the first agent message whose decision contradicts gold. A labeller
           model reads the transcript, gold's state changes, the agent's state changes and the
           database diff, and returns the message index, gold's decision at that point, the
           kind of error and the rule it turns on. This is the root-cause record.
  control  a passing run: an agent message that states a decision or changes state. The
           recorded message is the reference; a harness change must not alter that decision.

Only runs of the plain baseline agent are used, so every harness variant is measured as an
addition to the same starting context. Tasks whose gold the documents do not determine
(derivability oracle) are left out. Tasks are split, by task, into an evolve half (candidates
may be written from these) and a validate half (never shown to the proposer).

usage: set -a; . ./.env; set +a
       UV_FROZEN=1 uv run --with anthropic python adapted-harness/evolve/points.py
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Literal

import anthropic
from loguru import logger
from pydantic import BaseModel

logger.remove()
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "diagnostics"))
import db_diff  # noqa: E402

from tau2.agent.base_agent import is_valid_agent_history_message  # noqa: E402
from tau2.data_model.simulation import SimulationRun  # noqa: E402

TASKS = "data/tau2/domains/banking_knowledge/tasks"
OUT = os.path.join(HERE, "out", "points.json")
MODEL = "claude-opus-5-5"
RUNS = {  # plain baseline agent only: (run dir, retrieval config)
    "base-A": ("adapted-harness/baseline/dev-sonnet55-terminal", "terminal_use"),
    "base-B": (
        "data/simulations/dev-baseline-rerun1-sonnet55-terminal",
        "terminal_use",
    ),
    "gold-docs": ("data/simulations/dev-plain-golden-retrieval", "golden_retrieval"),
}
# Gold not determined by the documents (diagnostics/derivability.py): no decision to learn from.
NOT_DERIVABLE = {"task_082", "task_083", "task_084", "task_087"}
# By task. Evolve = tasks already read while writing the first hand-made candidate.
EVOLVE = {"task_015", "task_026", "task_066", "task_070", "task_078", "task_081"}
SKIP = {"log_verification", "unlock_discoverable_agent_tool", "get_current_time"}
KB_TOOLS = {"shell", "bash", "KB_search", "grep"}
_DECISION = re.compile(
    r"\b(can't|cannot|unable to|not able to|not eligible|isn't eligible|I recommend|"
    r"won't be able|not possible|I need to verify|before I can|I've (opened|closed|filed|"
    r"frozen|ordered|applied|transferred))\b",
    re.I,
)

Kind = Literal[
    "adds_condition",  # requires something no policy line or internal procedure requires
    "narrows_request",  # acts on fewer items than asked / qualify
    "replaces_request",  # does a different thing from what was asked
    "extra_action",  # changes state gold does not change
    "argument_value",  # right call, wrong or unrequested argument
    "skips_check",  # omits a lookup or step gold makes
    "wrong_choice",  # picks the wrong option among several
    "handoff",  # transfers too early, too late, or with the wrong reason
    "other",
]


class RootCause(BaseModel):
    index: int  # index (as shown) of the agent message that first contradicts gold
    reference: str  # what a correct reply does at this point, one or two sentences
    kind: Kind
    what_agent_did: str  # one sentence
    rule: str  # the policy line or document wording the correct decision rests on
    visible_in_one_reply: (
        bool  # the right/wrong decision shows in that single agent message
    )
    confident: bool


PROMPT = """You are diagnosing why a bank customer-service agent failed a graded task. The grader
replays the reference solution and compares the final database; the agent's run ended in a
different state.

Find the FIRST agent message (role "assistant") whose decision contradicts the reference solution:
the message where it declines, adds a condition, narrows or replaces what was asked, hands off,
picks an option, or makes a call with arguments the reference does not make. If the divergence is
something the agent never did, pick the message where it decided not to (or wrapped up without it).

Return its index exactly as shown in brackets. Write `reference` as a description of what a correct
reply does AT THAT POINT, given only what has happened so far, concretely enough that a reader of
one reply can tell whether it took that decision. Do not quote hidden information.

<reference_state_changes>
{gold}
</reference_state_changes>

<agent_state_changes>
{pred}
</agent_state_changes>

<database_difference agent_vs_reference>
{diff}
</database_difference>

<transcript>
{transcript}
</transcript>"""


def calls(actions) -> str:
    out = []
    for name, who, args in actions:
        if name in SKIP or name in KB_TOOLS:
            continue
        inner = args.get("agent_tool_name") or args.get("discoverable_tool_name")
        if name.startswith("call_discoverable") and inner:
            if inner.startswith("get_"):
                continue
            name, args = inner, args.get("arguments")
        elif name.startswith("get_"):
            continue
        out.append(f"{who}: {name} {json.dumps(args)[:400]}")
    return "\n".join(out) or "(none)"


def transcript(sim: SimulationRun) -> str:
    lines = []
    for i, m in enumerate(sim.messages):
        if not is_valid_agent_history_message(m):
            continue
        if m.role == "tool":
            lines.append(f"[{i}] tool result: {str(m.content)[:350]}")
            continue
        if m.content:
            lines.append(f"[{i}] {m.role}: {m.content[:1400]}")
        for tc in m.tool_calls or []:
            lines.append(
                f"[{i}] {m.role} CALL {tc.name} {json.dumps(tc.arguments)[:350]}"
            )
    return "\n".join(lines)


def db_difference(task_id: str, sim: SimulationRun) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            db_diff.diff(task_id, sim)
        except Exception as e:
            print(f"(diff failed: {e})")
    return buf.getvalue()[:3000]


def main():
    client = anthropic.Anthropic()
    sims = {}
    for label, (d, retrieval) in RUNS.items():
        for s in json.load(open(os.path.join(d, "results.json")))["simulations"]:
            if s["task_id"] != "task_102":
                sims[(label, s["task_id"])] = SimulationRun(**s)

    def label_one(key):
        run, tid = key
        sim = sims[key]
        task = json.load(open(f"{TASKS}/{tid}.json"))
        gold = [
            (a["name"], a.get("requestor", "assistant"), a["arguments"])
            for a in task["evaluation_criteria"]["actions"] or []
        ]
        pred = [
            (tc.name, m.role, tc.arguments)
            for m in sim.messages
            if m.role != "tool"
            for tc in (m.tool_calls or [])
        ]
        prompt = PROMPT.format(
            gold=calls(gold),
            pred=calls(pred),
            diff=diffs[key],
            transcript=transcript(sim),
        )
        for _ in range(2):
            try:
                r = client.messages.parse(
                    model=MODEL,
                    max_tokens=6000,
                    output_config={"effort": "medium"},
                    output_format=RootCause,
                    messages=[{"role": "user", "content": prompt}],
                )
                return key, r.parsed_output
            except Exception as e:
                err = e
        print("label failed", key, str(err)[:120])
        return key, None

    failing = [
        k
        for k, s in sims.items()
        if s.reward_info.reward != 1 and k[1] not in NOT_DERIVABLE
    ]
    # redirect_stdout is process-wide: compute the diffs one at a time, before the threads start
    diffs = {k: db_difference(k[1], sims[k]) for k in failing}
    points, dropped = [], []
    with ThreadPoolExecutor(6) as pool:
        for (run, tid), rc in pool.map(label_one, failing):
            if rc is None:
                continue
            msgs = sims[(run, tid)].messages
            ok = (
                0 < rc.index < len(msgs) and msgs[rc.index].role == "assistant"
            )  # the labeller's own doubt is recorded, not used to drop: it marked 20 of 24 good
            # labels as not confident, including the ones checked by hand
            row = {
                "run": run,
                "retrieval": RUNS[run][1],
                "task": tid,
                "index": rc.index,
                "role": "target",
                "split": "evolve" if tid in EVOLVE else "validate",
                "kind": rc.kind,
                "reference": rc.reference,
                "what_agent_did": rc.what_agent_did,
                "rule": rc.rule,
                "confident": rc.confident and rc.visible_in_one_reply,
            }
            (points if ok else dropped).append(row)

    rng = random.Random(0)
    controls = []
    for (run, tid), sim in sorted(sims.items()):
        if sim.reward_info.reward != 1:
            continue
        cands = []
        for i, m in enumerate(sim.messages):
            if m.role != "assistant" or i < 2:
                continue
            writes = [
                tc
                for tc in (m.tool_calls or [])
                if tc.name
                in ("give_discoverable_user_tool", "transfer_to_human_agents")
                or (
                    tc.name == "call_discoverable_agent_tool"
                    and not str(tc.arguments.get("agent_tool_name", "")).startswith(
                        "get_"
                    )
                )
            ]
            if writes or (m.content and _DECISION.search(m.content)):
                cands.append(i)
        for i in rng.sample(cands, min(2, len(cands))):
            controls.append(
                {
                    "run": run,
                    "retrieval": RUNS[run][1],
                    "task": tid,
                    "index": i,
                    "role": "control",
                    "split": "evolve" if rng.random() < 0.5 else "validate",
                    "kind": "control",
                }
            )
    json.dump(
        {"targets": points, "controls": controls, "dropped": dropped},
        open(OUT, "w"),
        indent=1,
    )
    print(
        f"targets {len(points)} (dropped {len(dropped)}), controls {len(controls)} -> {OUT}"
    )
    for split in ("evolve", "validate"):
        rows = [p for p in points if p["split"] == split]
        kinds = {}
        for p in rows:
            kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
        print(
            f"  {split}: {len(rows)} targets, tasks {sorted({p['task'][-3:] for p in rows})}, {kinds}"
        )
    for p in points:
        print(
            f"  {p['run']:9} {p['task'][-3:]}@{p['index']:<4} {p['split']:8} {p['kind']:17} {p['reference'][:150]}"
        )


if __name__ == "__main__":
    main()
