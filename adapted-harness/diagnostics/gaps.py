"""Consistent gaps: classify every failed simulation into general gap types and show which
gaps persist across runs. Grader-side (uses DB diffs against gold); never agent input.

Gap types (a failure can have several):
  transfer_extra      agent transferred, gold has no transfer
  transfer_missing    gold transfers (or counts more requests), agent did not
  user_tool_missing   a customer-side tool gold gives / the customer uses is missing
  write_missing:<t>   a state change gold makes is missing (by table)
  value_conflict      a differing field the KB leaves conflicting (provisional, pin, liability)
  value_other         another differing field
  write_extra:<t>     a state change gold does not make
  action_graded       ACTION-graded task (exact calls)

usage: uv run --frozen python adapted-harness/diagnostics/gaps.py [label=run_dir ...]
"""

import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_diff import dump, gold_env, predicted_env  # noqa: E402

from tau2.data_model.simulation import SimulationRun  # noqa: E402
from tau2.data_model.tasks import Task  # noqa: E402

DEFAULT_RUNS = {
    "base-A": "adapted-harness/baseline/dev-sonnet55-terminal",
    "base-B": "data/simulations/dev-baseline-rerun1-sonnet55-terminal",
    "v2-D": "data/simulations/dev-targeted-adapted-v2",
    "v5-S": "data/simulations/smoke-adapted-v5-hybrid",
    "v6-S": "data/simulations/smoke-adapted-v6",
    "v6-D": "data/simulations/dev-adapted-v6-e4f308a",
    "v7-S": "data/simulations/smoke-adapted-v7-096652a",
}
CONFLICT_FIELDS = {
    "provisional_credit_eligible",
    "provisional_credit_issued",
    "provisional_credit_amount",
    "eligible_for_provisional_credit",
    "pin_compromised",
    "pin_shared_voluntarily",
    "customer_max_liability_amount",
}
USER_TABLES = {"user_discoverable_tools", "user_discoverable_tool_calls"}
TASKS = "data/tau2/domains/banking_knowledge/tasks"


def classify(task: Task, sim: dict) -> set[str]:
    if task.evaluation_criteria.reward_basis != ["DB"]:
        return {"action_graded"}
    P, G = dump(predicted_env(task, SimulationRun(**sim))), dump(gold_env(task))
    gaps = set()
    agent_transfer = any(
        tc["name"] == "transfer_to_human_agents"
        for m in sim["messages"]
        for tc in (m.get("tool_calls") or [])
    )
    gold_transfer = any(
        a.name == "transfer_to_human_agents"
        for a in task.evaluation_criteria.actions or []
    )
    if agent_transfer and not gold_transfer:
        gaps.add("transfer_extra")
    for side in ("agent", "user"):
        for table in set(P[side]) | set(G[side]):
            pt = (
                (P[side].get(table) or {}).get("data", {})
                if isinstance(P[side].get(table), dict)
                else {}
            )
            gt = (
                (G[side].get(table) or {}).get("data", {})
                if isinstance(G[side].get(table), dict)
                else {}
            )
            for rid in set(pt) | set(gt):
                a, b = pt.get(rid), gt.get(rid)
                if a == b:
                    continue
                if a is None:
                    if table in USER_TABLES:
                        gaps.add("user_tool_missing")
                    elif table == "human_transfer_requests":
                        gaps.add("transfer_missing")
                    else:
                        gaps.add(f"write_missing:{table}")
                elif b is None:
                    gaps.add(f"write_extra:{table}")
                else:
                    diff = {f for f in set(a) | set(b) if a.get(f) != b.get(f)}
                    gaps.add(
                        "value_conflict" if diff <= CONFLICT_FIELDS else "value_other"
                    )
    return gaps or {"unexplained"}


def main(runs: dict):
    per_task = defaultdict(dict)  # task -> run -> gaps
    totals = defaultdict(Counter)
    for label, d in runs.items():
        p = os.path.join(d, "results.json")
        if not os.path.exists(p):
            continue
        for s in json.load(open(p))["simulations"]:
            if s["task_id"] == "task_102":
                continue
            if s["reward_info"]["reward"] == 1:
                per_task[s["task_id"]][label] = {"PASS"}
                continue
            task = Task(**json.load(open(os.path.join(TASKS, f"{s['task_id']}.json"))))
            g = classify(task, s)
            per_task[s["task_id"]][label] = g
            for x in g:
                totals[label][x.split(":")[0]] += 1
    labels = [lb for lb in runs if any(lb in v for v in per_task.values())]
    print("| task | " + " | ".join(labels) + " |\n|---|" + "---|" * len(labels))
    for t in sorted(per_task):
        cells = []
        for lb in labels:
            g = per_task[t].get(lb)
            cells.append(
                ""
                if g is None
                else "P"
                if g == {"PASS"}
                else ", ".join(
                    sorted(
                        x.replace("write_missing:", "miss:").replace(
                            "write_extra:", "extra:"
                        )
                        for x in g
                    )
                )
            )
        print(f"| {t} | " + " | ".join(cells) + " |")
    print("\nGap type counts per run (failures can have several):")
    kinds = sorted({k for c in totals.values() for k in c})
    print("| gap | " + " | ".join(labels) + " |\n|---|" + "---|" * len(labels))
    for k in kinds:
        print(
            f"| {k} | " + " | ".join(str(totals[lb].get(k, 0)) for lb in labels) + " |"
        )
    persistent = Counter()
    for t, rr in per_task.items():
        fails = [g for g in rr.values() if g != {"PASS"}]
        if len(fails) >= 2:
            common = set.intersection(*[{x.split(":")[0] for x in g} for g in fails])
            for c in common:
                persistent[c] += 1
    print(
        "\nPersistent gaps (same gap type in every failing run of a task, ≥2 runs):",
        dict(persistent.most_common()),
    )


if __name__ == "__main__":
    args = dict(a.split("=", 1) for a in sys.argv[1:]) or DEFAULT_RUNS
    main(args)
