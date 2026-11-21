"""Hill-climb ledger: task × iteration outcomes across runs, with pass counts and cost.

usage: uv run --frozen python adapted-harness/diagnostics/hillclimb.py
Edit RUNS to add an iteration. Cells: P pass, . fail, blank not run.
"""

import json
import os

RUNS = [  # (label, change made, run dir)
    (
        "base-A",
        "given baseline (llm_agent)",
        "adapted-harness/baseline/dev-sonnet55-terminal",
    ),
    (
        "base-B",
        "baseline rerun, no change",
        "data/simulations/dev-baseline-rerun1-sonnet55-terminal",
    ),
    (
        "base-S",
        "baseline SMOKE rerun, no change",
        "data/simulations/smoke-baseline-sonnet55-terminal",
    ),
    (
        "v1",
        "+ precheck gate, ledger, grounding note, derived-arg citations",
        "data/simulations/smoke-adapted-v1-all",
    ),
    (
        "v2-S",
        "+ KB tool contracts, transfer-request count, quote-check fixes",
        "data/simulations/smoke-adapted-v2-contracts",
    ),
    ("v2-D", "same as v2-S, targeted DEV", "data/simulations/dev-targeted-adapted-v2"),
    (
        "v3",
        "v2 + kb_related connected index (90 docs)",
        "data/simulations/dev-targeted-adapted-v3-index",
    ),
    (
        "v4",
        "v2 + liability rule card (dispute tool)",
        "data/simulations/dev-targeted-adapted-v4-rulecard",
    ),
    (
        "base-S-bm25",
        "baseline llm_agent, bm25_grep retrieval (SMOKE)",
        "data/simulations/smoke-baseline-llmagent-bm25grep",
    ),
    (
        "v5-S",
        "v4 + package refactor, hybrid retrieval, cross-doc check, grep cap (SMOKE)",
        "data/simulations/smoke-adapted-v5-hybrid",
    ),
]
UNREACHABLE = {
    "task_070",
    "task_071",
    "task_083",
}  # ambiguous or broken gold (FAILURE-PROFILE.md)


def load(d):
    p = os.path.join(d, "results.json")
    if not os.path.exists(p):
        return None
    out = {}
    for s in json.load(open(p))["simulations"]:
        if s["task_id"] == "task_102":
            continue
        cost = sum(
            (m.get("cost") or 0) for m in s["messages"] if m["role"] == "assistant"
        ) + (s.get("user_cost") or 0)
        out[s["task_id"]] = (s["reward_info"]["reward"] == 1, cost)
    return out


runs = [(lbl, why, load(d)) for lbl, why, d in RUNS]
runs = [r for r in runs if r[2]]
tasks = sorted({t for _, _, r in runs for t in r})
print("| task | " + " | ".join(lbl for lbl, _, _ in runs) + " |")
print("|---|" + "---|" * len(runs))
for t in tasks:
    mark = " (gold issue)" if t in UNREACHABLE else ""
    cells = [("P" if r[t][0] else ".") if t in r else " " for _, _, r in runs]
    print(f"| {t}{mark} | " + " | ".join(cells) + " |")
print()
print("| iteration | change | tasks run | passed | pass rate | cost | $/task |")
print("|---|---|---|---|---|---|---|")
for lbl, why, r in runs:
    n, p, c = len(r), sum(v[0] for v in r.values()), sum(v[1] for v in r.values())
    print(f"| {lbl} | {why} | {n} | {p} | {p / n:.0%} | ${c:.2f} | ${c / n:.2f} |")


def compare(a, b, label):
    ra, rb = (
        dict((x[0], x[2]) for x in runs).get(a),
        dict((x[0], x[2]) for x in runs).get(b),
    )
    if not ra or not rb:
        return
    common = sorted(set(ra) & set(rb))
    fixed = [t for t in common if rb[t][0] and not ra[t][0]]
    broke = [t for t in common if ra[t][0] and not rb[t][0]]
    print(
        f"- {label}: on {len(common)} shared tasks {sum(ra[t][0] for t in common)} → {sum(rb[t][0] for t in common)}; "
        f"fixed {fixed or '-'}; regressed {broke or '-'}"
    )


print("\nStep comparisons (same tasks only):")
for a, b, lbl in [
    ("base-A", "base-B", "noise: baseline A vs B"),
    ("base-S", "v1", "SMOKE baseline → v1"),
    ("v1", "v2-S", "SMOKE v1 → v2"),
    ("base-A", "v2-D", "targeted DEV baseline A → v2"),
    ("base-B", "v2-D", "targeted DEV baseline B → v2"),
    ("v2-D", "v3", "v2 → v3 (+index)"),
    ("v2-D", "v4", "v2 → v4 (+rule card)"),
    ("v2-S", "v3", "SMOKE v2 → v3 on 081/087"),
    ("base-S-bm25", "v5-S", "SMOKE baseline bm25_grep → v5 hybrid"),
    ("v2-S", "v5-S", "SMOKE v2 → v5"),
]:
    compare(a, b, lbl)
