"""Does kb_related help inter-document reasoning? Trace-level usage analysis (grader-side).

For each simulation of an adapted-harness run, reports:
  - kb_related calls and the documents each returned
  - follow-through: returned docs the agent opened afterwards
  - citation: returned docs cited in a later precheck (governing rules / derived arguments)
  - relevance: returned docs that are in the task's required_documents (grader-only; scoring use)
  - required docs the agent never opened, and whether the index would have pointed to them

usage: uv run --frozen python adapted-harness/diagnostics/index_usage.py data/simulations/<run> [...]
"""

import json
import os
import sys

from loguru import logger

logger.remove()
import tau2.agent.adapted_agent as A  # noqa: E402
from tau2.agent.adapted.kb import KB_TOOLS  # noqa: E402

TASKS = "data/tau2/domains/banking_knowledge/tasks"


def analyse(sim: dict) -> dict:
    kb = A._kb()
    task = json.load(open(os.path.join(TASKS, f"{sim['task_id']}.json")))
    req = set(task.get("required_documents") or [])
    calls, opened_at = {}, {}
    related_calls, cited = [], set()
    for i, m in enumerate(sim["messages"]):
        for tc in m.get("tool_calls") or []:
            calls[tc["id"]] = tc
        if (
            m["role"] == "tool"
            and m["id"] in calls
            and calls[m["id"]]["name"] in KB_TOOLS
        ):
            tc = calls[m["id"]]
            for d in kb.docs_seen(
                tc["name"], tc["arguments"].get("command", ""), m.get("content") or ""
            ):
                opened_at.setdefault(d, i)
        for e in (m.get("raw_data") or {}).get("harness") or []:
            if e["type"] == "kb_related":
                ret = [kb.resolve(x) or x for x in e.get("returned") or []]
                related_calls.append({"i": i, "doc": e.get("doc"), "returned": ret})
            if e["type"] == "precheck":
                a = e.get("args") or {}
                for r in (a.get("governing_rules") or []) + (
                    a.get("derived_arguments") or []
                ):
                    if r.get("doc_id"):
                        cited.add(kb.resolve(str(r["doc_id"])) or str(r["doc_id"]))
    returned = {d for c in related_calls for d in c["returned"]}
    first_call = min((c["i"] for c in related_calls), default=None)
    opened_after = {
        d
        for d in returned
        if d in opened_at and first_call is not None and opened_at[d] > first_call
    }
    never_opened_req = req - set(opened_at)
    index_would_point = set()
    for d in opened_at:
        index_would_point |= {r["doc"] for r in A._index().get(d, [])[:8]}
    return {
        "task": sim["task_id"],
        "pass": sim["reward_info"]["reward"] == 1,
        "kb_related_calls": len(related_calls),
        "returned": len(returned),
        "opened_after": len(opened_after),
        "cited_in_precheck": len(returned & cited),
        "returned_required": len(returned & req),
        "required": len(req),
        "required_never_opened": len(never_opened_req),
        "index_points_to_unopened_required": len(never_opened_req & index_would_point),
        "queried_docs": [c["doc"] for c in related_calls][:6],
    }


if __name__ == "__main__":
    for run in sys.argv[1:]:
        sims = json.load(open(os.path.join(run, "results.json")))["simulations"]
        rows = [analyse(s) for s in sorted(sims, key=lambda s: s["task_id"])]
        print(f"\n## {os.path.basename(run.rstrip('/'))}")
        print(
            "task      pass  calls ret opened_after cited ret∩req req never_opened_req idx→unopened_req"
        )
        for r in rows:
            print(
                f"{r['task']}  {'P' if r['pass'] else 'F'}    {r['kb_related_calls']:>3} {r['returned']:>4} "
                f"{r['opened_after']:>8} {r['cited_in_precheck']:>6} {r['returned_required']:>6} {r['required']:>4} "
                f"{r['required_never_opened']:>10} {r['index_points_to_unopened_required']:>10}"
            )
        tot = lambda k: sum(r[k] for r in rows)  # noqa: E731
        if tot("returned"):
            print(
                f"follow-through {tot('opened_after')}/{tot('returned')} returned docs opened; "
                f"{tot('cited_in_precheck')} cited in prechecks; {tot('returned_required')} were required docs"
            )
        print(
            f"required docs never opened: {tot('required_never_opened')}; of those the index points to "
            f"{tot('index_points_to_unopened_required')} from docs the agent did open"
        )
