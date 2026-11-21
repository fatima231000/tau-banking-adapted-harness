"""How many failures are caused by KB-conflict fields? Grader-side attribution over DB diffs.

For every failed simulation, each differing DB field is classed as:
  conflict:  dispute fields the KB leaves conflicting or undefined
             - provisional credit (doc 032: REQUIRED vs NOT REQUIRED lists overlap; the tool
               stores eligible == issued)
             - pin classification (doc 031 enum definitions do not cover a written-down PIN)
             - liability amount (doc 031/037 "noticed" vs doc 031/032 "statement" anchor)
  other:     everything else
A failure is "conflict-only" when every differing field is a conflict field, i.e. the task
would pass if those fields matched gold.

usage: uv run --frozen python adapted-harness/diagnostics/conflict_attribution.py
"""

import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_diff import dump, gold_env, predicted_env  # noqa: E402

from tau2.data_model.simulation import SimulationRun  # noqa: E402
from tau2.data_model.tasks import Task  # noqa: E402

RUNS = {
    "base-A": "adapted-harness/baseline/dev-sonnet55-terminal",
    "base-B": "data/simulations/dev-baseline-rerun1-sonnet55-terminal",
    "base-S": "data/simulations/smoke-baseline-sonnet55-terminal",
    "v1": "data/simulations/smoke-adapted-v1-all",
    "v2-S": "data/simulations/smoke-adapted-v2-contracts",
    "v2-D": "data/simulations/dev-targeted-adapted-v2",
    "v3": "data/simulations/dev-targeted-adapted-v3-index",
    "v4": "data/simulations/dev-targeted-adapted-v4-rulecard",
}
CONFLICT_GROUPS = {
    "provisional": (
        "provisional_credit_eligible",
        "provisional_credit_issued",
        "provisional_credit_amount",
        "eligible_for_provisional_credit",
    ),
    "pin": ("pin_compromised", "pin_shared_voluntarily"),
    "liability": ("customer_max_liability_amount",),
}
FIELD_GROUP = {f: g for g, fs in CONFLICT_GROUPS.items() for f in fs}
TASKS = "data/tau2/domains/banking_knowledge/tasks"


def field_diffs(task, sim):
    P, G = dump(predicted_env(task, sim)), dump(gold_env(task))
    out = []  # (table, record, field or None for whole-record)
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
                if a is None or b is None:
                    out.append((table, rid, None))
                else:
                    out += [
                        (table, rid, f) for f in set(a) | set(b) if a.get(f) != b.get(f)
                    ]
    return out


def main():
    per_run = {}
    group_hits = defaultdict(Counter)
    for label, run in RUNS.items():
        p = os.path.join(run, "results.json")
        if not os.path.exists(p):
            continue
        rows = []
        for s in json.load(open(p))["simulations"]:
            if s["task_id"] == "task_102" or s["reward_info"]["reward"] == 1:
                continue
            task = Task(**json.load(open(os.path.join(TASKS, f"{s['task_id']}.json"))))
            if task.evaluation_criteria.reward_basis != ["DB"]:
                rows.append((s["task_id"], "action-graded", [], []))
                continue
            diffs = field_diffs(task, SimulationRun(**s))
            conflict = [d for d in diffs if d[2] in FIELD_GROUP]
            other = [d for d in diffs if d[2] not in FIELD_GROUP]
            for d in conflict:
                group_hits[label][FIELD_GROUP[d[2]]] += 1
            kind = (
                "conflict-only"
                if conflict and not other
                else "conflict+other"
                if conflict
                else "other-only"
            )
            rows.append((s["task_id"], kind, conflict, other))
        per_run[label] = rows

    print(
        "| run | failed | conflict-only | conflict + other | other only | action-graded |"
    )
    print("|---|---|---|---|---|---|")
    for label, rows in per_run.items():
        k = Counter(r[1] for r in rows)
        print(
            f"| {label} | {len(rows)} | {k['conflict-only']} | {k['conflict+other']} | {k['other-only']} | {k['action-graded']} |"
        )

    print("\nConflict fields that differ from gold (dispute records), by group:")
    for label, c in group_hits.items():
        if c:
            print(f"- {label}: {dict(c)}")

    print("\nPer failed task (conflict-involved only):")
    for label, rows in per_run.items():
        for t, kind, conflict, other in rows:
            if conflict:
                groups = sorted({FIELD_GROUP[d[2]] for d in conflict})
                oth = sorted({f"{d[0]}.{d[2] or 'record'}" for d in other})[:4]
                print(
                    f"- {label} {t}: {kind}; conflict groups {groups}; other diffs {oth or '-'}"
                )


if __name__ == "__main__":
    main()
