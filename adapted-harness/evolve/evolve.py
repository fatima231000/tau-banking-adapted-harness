"""Evolve a harness candidate from root causes (reflective evolution; grader-side; DEV only).

Loop, starting from a parent candidate already scored on the evolve half:
  1. feedback: the evolve-half decisions the parent still gets wrong (root-cause records from
     points.py, plus what its replies did) and the correct decisions it breaks (controls)
  2. propose: a model rewrites the candidate's elements (system section, state line, self-check)
     in general terms
  3. lint: reject text with task content (product names, tool ids, amounts, dates)
  4. score: replay on the evolve half; a child replaces the parent only if it gets more wrong
     decisions right AND keeps the controls (within --tolerance)
After the last generation the best candidate is scored once on the validate half, which the
proposer never saw. Only a candidate that also holds there is written to out/best.json.

usage: set -a; . ./.env; set +a
       UV_FROZEN=1 uv run --with anthropic python adapted-harness/evolve/evolve.py \
           --parent method --parent-rows gen0 [--generations 3] [--children 2]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict

import anthropic
from pydantic import BaseModel

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import replay as R  # noqa: E402

MODEL = "claude-opus-5-5"
DOCS = "data/tau2/domains/banking_knowledge/documents"
POLICY = "data/tau2/domains/banking_knowledge/prompts/components"
MAX_SYSTEM, MAX_NOTE, MAX_REVIEW = 2600, 400, 900


class Candidate(BaseModel):
    system: str  # prompt section, appended after the bank's policy
    note: str  # one state line on customer turns; may use {n} = human-agent requests so far; "" for none
    review: str  # self-check the agent runs once on a draft reply before sending; "" for none
    rationale: str  # what changed and which kind of error it addresses (not shown to the agent)


PROPOSER = """You are improving the harness of a bank customer-service agent. The agent is a capable
model that already has the bank's policy, a knowledge base it can read, and tools. The harness adds
up to three elements on top, and you are rewriting them:

- system: a short section appended to the agent's instructions. It should make the agent better at
  grounding (acting on a rule it has read), verification (checking facts and its own work),
  reasoning, handling conflicts between documents, and decision making.
- note: one state line the harness appends to customer messages once the customer has asked for a
  human agent. `{{n}}` is replaced by how many times they have asked. Leave empty for none.
- review: a self-check the agent runs once on its own draft reply before it is sent. Leave empty
  for none. It costs one extra model call per reply, so keep it only if it earns its place.

Below is the current candidate, the decisions it still gets WRONG, and the correct decisions it
BREAKS (decisions the plain agent gets right that this candidate changes). Each wrong decision has
a diagnosis: the kind of error, what the agent did, what a correct reply does, and the rule it
turns on.

Write a better candidate. Requirements:
1. General. Every sentence must hold for any request at any bank. No product names, tool names,
   amounts, dates, or instructions tied to one situation. Generalise from the KIND of error, never
   from the case. A reader must not be able to tell which cases you saw.
2. Two-sided. Fixing the wrong decisions must not break correct ones. Many correct decisions are
   refusals, required checks and conditions that a rule really does impose. An instruction that
   simply makes the agent more permissive, or simply more cautious, will trade one error for
   another. Say how to tell the cases apart.
3. Consistent with the bank's policy below; do not restate it.
4. Short and plain: system at most {max_system} characters, note at most {max_note}, review at
   most {max_review}. Fewer, sharper principles beat a list of rules. Do not pile up bullet points.
5. Keep what works in the current candidate; change what the evidence says is failing.

<bank_policy>
{policy}
</bank_policy>

<current_candidate>
{candidate}
</current_candidate>

<wrong_decisions fixed="{t_ok}/{t_n}">
{wrong}
</wrong_decisions>

<broken_correct_decisions kept="{c_ok}/{c_n}">
{broken}
</broken_correct_decisions>
{history}"""


def product_names() -> set[str]:
    """Product names from the knowledge base's document ids, for the lint only."""
    names = set()
    for f in os.listdir(DOCS):
        m = re.match(
            r"doc_(?:business_)?(?:checking_accounts|savings_accounts|credit_cards)_(.+)_\d+\.json",
            f,
        )
        if m and "general" not in m.group(1) and "logistics" not in m.group(1):
            names.add(m.group(1).replace("_", " ").lower())
    return {n for n in names if len(n) > 5}


def lint(c: Candidate, products: set[str]) -> list[str]:
    problems = []
    text = "\n".join([c.system, c.note, c.review])
    low = text.lower()
    for n in sorted(products):
        if re.search(rf"\b{re.escape(n)}\b", low):
            problems.append(f"product name: {n}")
    if re.search(r"\b[a-z]+(?:_[a-z]+)+_\d{4}\b", text):  # knowledge-base tool ids
        problems.append("tool identifier")
    if re.search(
        r"\$\s?\d|\b\d{2,}\b|\b\d+\s?(?:days?|%|percent|years?|months?)\b", text
    ):
        problems.append("amount, count or date")
    if len(c.system) > MAX_SYSTEM:
        problems.append(f"system too long ({len(c.system)})")
    if len(c.note) > MAX_NOTE or len(c.review) > MAX_REVIEW:
        problems.append("note or review too long")
    bad_fields = set(re.findall(r"\{([^{}]*)\}", c.note)) - {"n"}
    if bad_fields or "{" in c.system or "{" in c.review:
        problems.append("placeholder other than {n} in note")
    return problems


def per_point(rows):
    d = defaultdict(list)
    for r in rows:
        d[(r["run"], r["task"], r["index"])].append(r)
    return d


def totals(rows):
    t = R.rate([r for r in rows if r["role"] == "target"])
    c = R.rate([r for r in rows if r["role"] == "control"])
    return t, c


def feedback(rows, points, rp):
    by = per_point(rows)
    wrong, broken = [], []
    for p in points:
        rs = by.get((p["run"], p["task"], p["index"]), [])
        ok, n = R.rate(rs)
        if not n or ok == n:
            continue
        bad = next((r for r in rs if r["ok"] is False), None)
        if p["role"] == "target":
            wrong.append(
                f"- kind: {p['kind']} (right in {ok}/{n} samples)\n"
                f"  agent did: {bad['did'] if bad else p['what_agent_did']}\n"
                f"  a correct reply: {p['reference']}\n"
                f"  rule it turns on: {p['rule']}"
            )
        else:
            broken.append(
                f"- correct decision (kept in {ok}/{n} samples): {rp.reference(p)[:500]}\n"
                f"  with this candidate the agent instead: {bad['did'] if bad else '?'}"
            )
    return "\n".join(wrong) or "(none)", "\n".join(broken) or "(none)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent", default="method")
    ap.add_argument("--parent-rows", default="gen0")
    ap.add_argument("--generations", type=int, default=3)
    ap.add_argument("--children", type=int, default=2)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--control-k", type=int, default=2)
    ap.add_argument("--controls", type=int, default=30)
    ap.add_argument("--tolerance", type=int, default=1)
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()

    client = anthropic.Anthropic()
    rp = R.Replayer()
    products = product_names()
    policy = "\n\n".join(
        open(os.path.join(POLICY, f)).read()
        for f in ("policy_header.md", "additional_instructions.md")
    )
    all_points = R.load_points("all", a.controls)
    evolve = [p for p in all_points if p["split"] == "evolve"]
    validate = [p for p in all_points if p["split"] == "validate"]
    keys = {(p["run"], p["task"], p["index"]) for p in evolve}

    cand_dir = os.path.join(HERE, "candidates")
    best_name = a.parent
    best = json.load(open(os.path.join(cand_dir, f"{best_name}.json")))
    rows_path = os.path.join(HERE, "out", f"{a.parent_rows}.json")
    if os.path.exists(rows_path):
        best_rows = [
            r
            for r in json.load(open(rows_path))
            if r["candidate"] == a.parent and (r["run"], r["task"], r["index"]) in keys
        ]
    else:  # no earlier scoring of the parent: score it here
        best_rows = rp.score(
            evolve,
            {a.parent: os.path.join(cand_dir, f"{a.parent}.json")},
            a.k,
            a.control_k,
            workers=a.workers,
        )
    (bt, bn), (bc, bcn) = totals(best_rows)
    print(f"parent {best_name}: evolve targets {bt}/{bn}, controls {bc}/{bcn}")
    log, tried = [], []

    for gen in range(1, a.generations + 1):
        wrong, broken = feedback(best_rows, evolve, rp)
        children = {}
        for j in range(a.children):
            history = ""
            if tried:
                history = (
                    "\n<rejected_attempts>\n"
                    + "\n".join(tried[-4:])
                    + "\n</rejected_attempts>\nDo not repeat these; take a different approach."
                )
            msg = PROPOSER.format(
                max_system=MAX_SYSTEM,
                max_note=MAX_NOTE,
                max_review=MAX_REVIEW,
                policy=policy,
                candidate=json.dumps(
                    {k: best.get(k, "") for k in ("system", "note", "review")}, indent=1
                ),
                wrong=wrong,
                broken=broken,
                t_ok=bt,
                t_n=bn,
                c_ok=bc,
                c_n=bcn,
                history=history,
            )
            for attempt in range(3):
                r = client.messages.parse(
                    model=MODEL,
                    max_tokens=8000,
                    output_config={"effort": "high"},
                    output_format=Candidate,
                    messages=[{"role": "user", "content": msg}],
                )
                c = r.parsed_output
                problems = lint(c, products)
                if not problems:
                    break
                msg += f"\n\nYour last attempt was rejected by the lint: {problems}. Remove these and return the full candidate again."
            if problems:
                print(f"gen {gen} child {j}: lint failed {problems}")
                continue
            name = f"g{gen}c{j}"
            spec = {k: v for k, v in c.model_dump().items() if v and k != "rationale"}
            spec["_rationale"], spec["_parent"] = c.rationale, best_name
            json.dump(spec, open(os.path.join(cand_dir, f"{name}.json"), "w"), indent=1)
            children[name] = spec
            tried.append(f"- {name}: {c.rationale[:400]}")
        if not children:
            continue
        rows = rp.score(
            evolve,
            {n: os.path.join(cand_dir, f"{n}.json") for n in children},
            a.k,
            a.control_k,
            workers=a.workers,
        )
        json.dump(
            rows,
            open(os.path.join(HERE, "out", f"evolve_gen{gen}.json"), "w"),
            indent=1,
        )
        for name, spec in children.items():
            crow = [r for r in rows if r["candidate"] == name]
            (t, tn), (c_, cn) = totals(crow)
            accept = t > bt and c_ >= bc - a.tolerance
            log.append(
                {
                    "gen": gen,
                    "name": name,
                    "targets": [t, tn],
                    "controls": [c_, cn],
                    "accepted": accept,
                }
            )
            print(
                f"gen {gen} {name}: evolve targets {t}/{tn}, controls {c_}/{cn} -> {'ACCEPT' if accept else 'reject'} | {spec['_rationale'][:160]}"
            )
            tried[-len(children) + list(children).index(name)] += (
                f" -> targets {t}/{tn}, controls {c_}/{cn}"
            )
            if accept and (t, c_) > (bt, bc - a.tolerance):
                best_name, best, best_rows, bt, bn, bc, bcn = (
                    name,
                    spec,
                    crow,
                    t,
                    tn,
                    c_,
                    cn,
                )

    print(
        f"\nbest on the evolve half: {best_name} (targets {bt}/{bn}, controls {bc}/{bcn})"
    )
    names = list(dict.fromkeys(["plain", a.parent, best_name]))
    rows = rp.score(
        validate,
        {n: os.path.join(cand_dir, f"{n}.json") for n in names},
        a.k,
        a.control_k,
        workers=a.workers,
    )
    json.dump(
        rows, open(os.path.join(HERE, "out", "evolve_validate.json"), "w"), indent=1
    )
    print("\nVALIDATE half (never shown to the proposer):")
    R.table(rows, names)
    json.dump(log, open(os.path.join(HERE, "out", "evolve_log.json"), "w"), indent=1)
    res = {n: totals([r for r in rows if r["candidate"] == n]) for n in names}
    (vt, _), (vc, _) = res[best_name]
    (pt, _), (pc, _) = res["plain"]
    holds = vt > pt and vc >= pc - a.tolerance
    print(
        f"\n{best_name} on validate: targets {vt} vs plain {pt}; controls {vc} vs plain {pc} -> {'HOLDS' if holds else 'does not hold'}"
    )
    if holds:
        json.dump(best, open(os.path.join(HERE, "out", "best.json"), "w"), indent=1)
        print("wrote out/best.json")


if __name__ == "__main__":
    main()
