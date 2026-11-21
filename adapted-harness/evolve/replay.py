"""Decision-point replay: score harness candidates on frozen decisions (grader-side; DEV only).

An end-to-end DEV run gives one noisy bit per task. This freezes a recorded conversation just
before one agent decision and regenerates that decision k times under each candidate, through the
harness's own turn loop, with the context the agent had. It reports P(reference decision).

  targets   the recorded agent contradicted gold; reference = gold's decision (points.py)
  controls  the recorded agent was right; reference = the recorded message. A control counts as
            broken only when the new reply takes a CONTRARY decision; a reply that pauses to look
            something up is not a break (gen 0 showed most apparent breaks were of that kind).

A candidate is a JSON file (candidates/*.json) with optional "system", "note", "review" elements;
it runs on top of the plain baseline agent. Only the judge sees a reference.

usage: set -a; . ./.env; set +a
       UV_FROZEN=1 uv run --with anthropic python adapted-harness/evolve/replay.py \
           --candidates plain,method,method_review [--split evolve|validate|all] [--k 3]
           [--control-k 2] [--controls 30] [--out NAME]
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from typing import Literal

import anthropic
from loguru import logger
from pydantic import BaseModel

logger.remove()

from tau2.agent.adapted.agent import AdaptedLLMAgent  # noqa: E402
from tau2.agent.adapted.config import HarnessConfig  # noqa: E402
from tau2.agent.base_agent import is_valid_agent_history_message  # noqa: E402
from tau2.data_model.message import MultiToolMessage, UserMessage  # noqa: E402
from tau2.data_model.simulation import SimulationRun  # noqa: E402
from tau2.data_model.tasks import Task  # noqa: E402
from tau2.domains.banking_knowledge.environment import get_environment  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = "data/tau2/domains/banking_knowledge/tasks"
RUNS = {
    "base-A": "adapted-harness/baseline/dev-sonnet55-terminal",
    "base-B": "data/simulations/dev-baseline-rerun1-sonnet55-terminal",
    "gold-docs": "data/simulations/dev-plain-golden-retrieval",
}
AGENT_MODEL = "claude-sonnet-5-5"
JUDGE_MODEL = "claude-opus-5-5"


class Verdict(BaseModel):
    # same: takes the reference decision. contrary: commits to something the reference rules out,
    # or drops a refusal, limit, check or condition the reference imposes, or acts differently.
    # undecided: only reads or looks something up, with no commitment either way.
    verdict: Literal["same", "contrary", "undecided"]
    what_it_did: str  # one short sentence


JUDGE = """You are scoring one reply of a bank's customer-service agent against a reference decision.

<reference kind="{kind}">
{reference}
</reference>

<reply>
{reply}
</reply>

{rule}
Judge only the decision (what the agent does or commits to, declines, requires, leaves out or hands
off), not wording or tone. Answer "undecided" when the reply only looks something up or reads a
document and has not committed either way."""
RULES = {
    "target": "The reference states the correct decision at this point. Does the reply take it "
    "(same), go against it (contrary), or not decide yet (undecided)?",
    "control": "The reference is an earlier reply whose decision was correct. Does the new reply "
    "make the same decision (same), a contrary one (contrary), or none yet (undecided)? The same "
    "lookup, or the same action with the same arguments, is the same decision.",
}


def render(msg) -> str:
    parts = [msg.content] if msg.content else []
    for tc in msg.tool_calls or []:
        parts.append(f"TOOL CALL {tc.name}({json.dumps(tc.arguments)[:1500]})")
    return "\n".join(parts) or "(empty)"


class Replayer:
    def __init__(self):
        self.sims, self.envs = {}, {}
        self.client = anthropic.Anthropic()

    def sim(self, run, tid) -> SimulationRun:
        if run not in self.sims:
            raw = json.load(open(os.path.join(RUNS[run], "results.json")))
            self.sims[run] = {
                s["task_id"]: SimulationRun(**s) for s in raw["simulations"]
            }
        return self.sims[run][tid]

    def env(self, retrieval, tid):
        """Tool schemas and policy as the recorded agent had them. Built up front, single thread."""
        key = (retrieval, tid if retrieval == "golden_retrieval" else None)
        if key not in self.envs:
            task = Task(**json.load(open(f"{TASKS}/{tid}.json")))
            e = get_environment(
                retrieval_variant=retrieval,
                **({"task": task} if retrieval == "golden_retrieval" else {}),
            )
            self.envs[key] = (e.get_tools(), e.get_policy())
        return self.envs[key]

    def reference(self, p) -> str:
        if p["role"] == "target":
            return p["reference"]
        return render(self.sim(p["run"], p["task"]).messages[p["index"]])

    def sample(self, p, candidate_path: str) -> str:
        tools, policy = self.env(p["retrieval"], p["task"])
        cfg = replace(HarnessConfig.preset("plain"), candidate_path=candidate_path)
        agent = AdaptedLLMAgent(
            tools=tools, domain_policy=policy, llm=AGENT_MODEL, llm_args={}, config=cfg
        )
        hist = [
            deepcopy(m)
            for m in self.sim(p["run"], p["task"]).messages[: p["index"]]
            if is_valid_agent_history_message(m)
        ]
        cut = len(
            hist
        )  # the trailing block the agent is answering: one user message, or tool results
        while cut > 0 and hist[cut - 1].role == "tool":
            cut -= 1
        if cut == len(hist):
            cut -= 1
        state = agent.get_init_state(message_history=[])
        for m in hist[
            :cut
        ]:  # earlier customer turns get the same state line they would have had
            state.messages.append(
                agent.context.incoming(m, state) if isinstance(m, UserMessage) else m
            )
        tail = hist[cut:]
        incoming = (
            tail[0]
            if len(tail) == 1
            else MultiToolMessage(role="tool", tool_messages=tail)
        )
        out, _ = agent.generate_next_message(incoming, state)
        return render(out)

    def judge(self, p, reply: str) -> Verdict:
        r = self.client.messages.parse(
            model=JUDGE_MODEL,
            max_tokens=2000,
            output_format=Verdict,
            messages=[
                {
                    "role": "user",
                    "content": JUDGE.format(
                        kind=p["role"],
                        reference=self.reference(p),
                        reply=reply,
                        rule=RULES[p["role"]],
                    ),
                }
            ],
        )
        return r.parsed_output

    def score(self, points, candidates: dict, k: int, control_k: int, workers: int = 8):
        """candidates: name -> path. Returns rows (one per sample)."""
        for p in points:
            self.sim(p["run"], p["task"])
            self.env(p["retrieval"], p["task"])

        def one(job):
            p, name, n = job
            try:
                reply = self.sample(p, candidates[name])
                v = self.judge(p, reply)
                did, verdict = v.what_it_did, v.verdict
                ok = (
                    verdict == "same"
                    if p["role"] == "target"
                    else verdict != "contrary"
                )
            except Exception as e:  # recorded, not hidden
                reply, ok, did, verdict = f"ERROR {e}", None, None, None
            return {
                "run": p["run"],
                "task": p["task"],
                "index": p["index"],
                "role": p["role"],
                "split": p["split"],
                "kind": p["kind"],
                "candidate": name,
                "n": n,
                "ok": ok,
                "verdict": verdict,
                "did": did,
                "reply": reply[:1500],
            }

        rows = []
        # first sample of each (point, candidate) alone, so the later ones read the prompt cache
        for phase in (0, 1):
            jobs = [
                (p, name, n)
                for p in points
                for name in candidates
                for n in range(k if p["role"] == "target" else control_k)
                if (n == 0) == (phase == 0)
            ]
            with ThreadPoolExecutor(workers) as pool:
                rows += list(pool.map(one, jobs))
        return rows


def rate(rows):
    ok = [r["ok"] for r in rows if r["ok"] is not None]
    return (sum(ok), len(ok))


def fmt(x):
    return f"{x[0]}/{x[1]}" if x[1] else "-"


def table(rows, names):
    pts = sorted(
        {
            (r["role"], r["split"], r["task"], r["run"], r["index"], r["kind"])
            for r in rows
        }
    )
    print(
        f"\n{'point':<22}{'split':<9}{'kind':<17}" + "".join(f"{n:>15}" for n in names)
    )
    for role, split, task, run, idx, kind in pts:
        if role != "target":
            continue
        sel = [r for r in rows if (r["task"], r["run"], r["index"]) == (task, run, idx)]
        cells = [fmt(rate([r for r in sel if r["candidate"] == n])) for n in names]
        print(
            f"{task[-3:]}@{idx:<4}{run:<13}{split:<9}{kind:<17}"
            + "".join(f"{c:>15}" for c in cells)
        )
    for role in ("target", "control"):
        for split in ("evolve", "validate"):
            sel = [r for r in rows if r["role"] == role and r["split"] == split]
            if sel:
                cells = [
                    fmt(rate([r for r in sel if r["candidate"] == n])) for n in names
                ]
                print(
                    f"{'TOTAL ' + role:<22}{split:<9}{'':<17}"
                    + "".join(f"{c:>15}" for c in cells)
                )
    errs = sum(r["ok"] is None for r in rows)
    if errs:
        print(f"errors: {errs}")


def load_points(split: str, n_controls: int):
    x = json.load(open(os.path.join(HERE, "out", "points.json")))
    keep = (lambda p: True) if split == "all" else (lambda p: p["split"] == split)
    targets = [p for p in x["targets"] if keep(p)]
    controls = [p for p in x["controls"] if keep(p)]
    random.Random(0).shuffle(controls)
    return targets + controls[:n_controls]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default="plain,method")
    ap.add_argument("--split", default="all")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--control-k", type=int, default=2)
    ap.add_argument("--controls", type=int, default=30)
    ap.add_argument("--out", default="replay")
    a = ap.parse_args()
    names = a.candidates.split(",")
    cands = {n: os.path.join(HERE, "candidates", f"{n}.json") for n in names}
    points = load_points(a.split, a.controls)
    rows = Replayer().score(points, cands, a.k, a.control_k)
    json.dump(rows, open(os.path.join(HERE, "out", f"{a.out}.json"), "w"), indent=1)
    table(rows, names)


if __name__ == "__main__":
    sys.exit(main())
