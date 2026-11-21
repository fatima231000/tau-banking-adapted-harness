"""DEV results of every harness arm on one table (grader-side scoring only).

Reads the recorded runs, prints pass/fail per task and totals with agent cost, and writes the
same data to adapted-harness/evolve/out/dev_results.json. Runs that are missing are skipped.

usage: uv run --frozen python adapted-harness/diagnostics/dev_table.py
"""

import json
import os

RUNS = [  # label, run directory, what it is
    (
        "base-A",
        "adapted-harness/baseline/dev-sonnet55-terminal",
        "baseline (given run)",
    ),
    (
        "base-B",
        "data/simulations/dev-baseline-rerun1-sonnet55-terminal",
        "baseline (rerun)",
    ),
    ("v6", "data/simulations/dev-adapted-v6-e4f308a", "gates v6"),
    ("v7", "data/simulations/dev-adapted-v7-096652a", "gates v7 + caching"),
    ("v8", "data/simulations/dev-adapted-v8-1ca51c8", "gates v8 + decision records"),
    ("cards-1", "data/simulations/dev-lean-ce7724b-r1", "skill cards + rulings"),
    ("cards-2", "data/simulations/dev-lean-ce7724b-r2", "skill cards + rulings"),
    (
        "enable-1",
        "data/simulations/dev-enable-85c017b-r1",
        "working method + search tool",
    ),
    (
        "enable-2",
        "data/simulations/dev-enable-85c017b-r2",
        "working method + search tool",
    ),
    (
        "gold-docs",
        "data/simulations/dev-plain-golden-retrieval",
        "oracle: required docs in prompt",
    ),
    ("decisions", "data/simulations/dev-decide-r1", "hand-written decisions section"),
    ("method", "data/simulations/dev-cand-method-r1", "seed: working-method section"),
    (
        "method+check",
        "data/simulations/dev-cand-method-review-r1",
        "seed: + self-check",
    ),
    ("evolved-1", "data/simulations/dev-evolved-g1c1-r1", "evolved candidate g1c1"),
    ("evolved-2", "data/simulations/dev-evolved-g1c1-r2", "evolved candidate g1c1"),
    (
        "evolved-3",
        "data/simulations/dev-evolved-final-r1",
        "evolved candidate, final wording",
    ),
]
EVOLVE = {"task_015", "task_026", "task_066", "task_070", "task_078", "task_081"}
NOT_DERIVABLE = {"task_082", "task_083", "task_084", "task_087"}
OUT = "adapted-harness/evolve/out/dev_results.json"


def load(d):
    p = os.path.join(d, "results.json")
    if not os.path.exists(p):
        return {}
    return {
        s["task_id"]: s
        for s in json.load(open(p))["simulations"]
        if s["task_id"] != "task_102"
    }


def main():
    runs = {k: load(d) for k, d, _ in RUNS}
    runs = {k: v for k, v in runs.items() if v}
    tasks = sorted(runs["base-A"])
    ok = lambda s: int(s["reward_info"]["reward"])  # noqa: E731
    print("task  " + " ".join(f"{k[:9]:>9}" for k in runs))
    for t in tasks:
        print(
            t[-3:]
            + "   "
            + " ".join(f"{(ok(runs[k][t]) if t in runs[k] else '-'):>9}" for k in runs)
        )
    out = {}
    print(
        f"\n{'arm':<13}{'done':>5}{'passed':>7}{'evolve-6':>9}{'other-14':>9}{'n/d-4':>6}{'agent $':>9}  what"
    )
    for k, _, what in RUNS:
        d = runs.get(k)
        if not d:
            continue
        cost = sum(
            (m.get("cost") or 0)
            for s in d.values()
            for m in s["messages"]
            if m["role"] == "assistant"
        )
        g = lambda keep: sum(ok(s) for t, s in d.items() if keep(t))  # noqa: E731
        row = {
            "what": what,
            "done": len(d),
            "passed": g(lambda t: True),
            "evolve_tasks": g(lambda t: t in EVOLVE),
            "other_tasks": g(lambda t: t not in EVOLVE and t not in NOT_DERIVABLE),
            "not_derivable": g(lambda t: t in NOT_DERIVABLE),
            "agent_cost_usd": round(cost, 2),
            "per_task": {t: ok(s) for t, s in sorted(d.items())},
        }
        out[k] = row
        print(
            f"{k:<13}{row['done']:>5}{row['passed']:>7}{row['evolve_tasks']:>9}{row['other_tasks']:>9}"
            f"{row['not_derivable']:>6}{row['agent_cost_usd']:>9.2f}  {what}"
        )
    json.dump(out, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
