"""Grader-side DB diff for banking_knowledge runs. FOR ANALYSIS ONLY: never agent input.

Rebuilds the two environments the EnvironmentEvaluator compares (agent trajectory
replayed vs. gold actions replayed, both from the task's initial state) and prints
the records that differ, per table.

usage: uv run python adapted-harness/diagnostics/db_diff.py data/simulations/<run> [task_id ...]
"""

import json
import os
import sys
from copy import deepcopy

from loguru import logger

logger.remove()

from tau2.data_model.simulation import SimulationRun  # noqa: E402
from tau2.data_model.tasks import Task  # noqa: E402
from tau2.domains.banking_knowledge.environment import get_environment  # noqa: E402
from tau2.runner.build import _derive_read_log_allowlist  # noqa: E402

TASKS = "data/tau2/domains/banking_knowledge/tasks"


def build_env(task: Task):
    return get_environment(
        retrieval_variant="no_knowledge",  # DB tools are identical; avoids the sandbox
        task=task,
        read_log_allowlist=_derive_read_log_allowlist(task),
    )


def init(env, task: Task, history):
    st = task.initial_state
    env.set_state(
        initialization_data=st.initialization_data if st else None,
        initialization_actions=st.initialization_actions if st else None,
        message_history=history,
        strict=False,
    )


def predicted_env(task, sim):
    env = build_env(task)
    # Replay only DB tool calls: drop shell calls (and their results), which have
    # no DB effect and do not exist under no_knowledge.
    drop = {
        tc.id
        for m in sim.messages
        for tc in (getattr(m, "tool_calls", None) or [])
        if tc.name == "shell"
    }
    hist = []
    for m in sim.messages:
        m = deepcopy(m)
        if getattr(m, "tool_calls", None):
            m.tool_calls = [tc for tc in m.tool_calls if tc.id not in drop] or None
            if m.tool_calls is None and not m.has_text_content():
                continue
        if m.role == "tool" and m.id in drop:
            continue
        hist.append(m)
    init(env, task, hist)
    return env


def gold_env(task):
    env = build_env(task)
    init(env, task, [])
    for a in task.evaluation_criteria.actions or []:
        try:
            out = env.make_tool_call(
                tool_name=a.name, requestor=a.requestor, **a.arguments
            )
        except Exception as e:  # mirrors the evaluator: log and continue
            print(f"  [GOLD ACTION RAISED] {a.name}: {e}")
            continue
        # call_discoverable_* return errors as strings; the evaluator does not notice these.
        if isinstance(out, str) and out.lstrip().startswith("Error"):
            name = (
                a.arguments.get("agent_tool_name")
                or a.arguments.get("user_tool_name")
                or a.name
            )
            print(f"  [GOLD ACTION RETURNED ERROR] {name}: {out[:160]}")
    return env


def dump(env):
    return {
        "agent": json.loads(env.tools.db.model_dump_json()) if env.tools else {},
        "user": json.loads(env.user_tools.db.model_dump_json())
        if env.user_tools
        and getattr(env.user_tools, "db", None) is not None
        and env.user_tools.db is not env.tools.db
        else {},
    }


def diff(task_id, sim):
    task = Task(**json.load(open(os.path.join(TASKS, f"{task_id}.json"))))
    print(f"\n## {task_id}")
    p, g = predicted_env(task, sim), gold_env(task)
    match = (
        p.get_db_hash() == g.get_db_hash()
        and p.get_user_db_hash() == g.get_user_db_hash()
    )
    print(f"hash match {match} (recorded reward {sim.reward_info.reward})")
    P, G = dump(p), dump(g)
    for side in ("agent", "user"):
        for table in sorted(set(P[side]) | set(G[side])):
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
            for rid in sorted(set(pt) | set(gt)):
                a, b = pt.get(rid), gt.get(rid)
                if a == b:
                    continue
                if b is None:
                    print(f"- {table}/{rid}: EXTRA in agent run: {json.dumps(a)[:400]}")
                elif a is None:
                    print(f"- {table}/{rid}: MISSING (gold has): {json.dumps(b)[:400]}")
                else:
                    fields = {
                        k: (a.get(k), b.get(k))
                        for k in set(a) | set(b)
                        if a.get(k) != b.get(k)
                    }
                    print(
                        f"- {table}/{rid}: DIFF agent→gold {json.dumps(fields)[:400]}"
                    )


if __name__ == "__main__":
    run = sys.argv[1].rstrip("/")
    want = set(sys.argv[2:])
    sims = [
        SimulationRun(**s)
        for s in json.load(open(os.path.join(run, "results.json")))["simulations"]
    ]
    for s in sorted(sims, key=lambda s: s.task_id):
        if (want and s.task_id not in want) or s.task_id == "task_102":
            continue
        if not want and s.reward_info and s.reward_info.reward == 1:
            continue
        diff(s.task_id, s)
