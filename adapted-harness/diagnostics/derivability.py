"""Derivability oracle (grader-side diagnosis, DEV only): is each task's gold outcome derivable
from the documents by a fully informed reader?

For each task, a strong model receives: the policy, the task's required documents in full, the
definitions of the tools those documents name, the customer's complete (hidden) script, and the
facts returned by gold's own READ calls replayed on a fresh environment. It outputs the
state-changing calls the documents require. Those are compared field by field with gold's.
Run twice per task: two informed runs disagreeing on a field means the documents under-determine it.

  derivable      both oracle runs reproduce every gold state change
  partly         gold differs on some fields; listed
  under-determined  the two oracle runs disagree with each other

usage: set -a; . ./.env; set +a
       UV_FROZEN=1 uv run --with anthropic python adapted-harness/diagnostics/derivability.py task_014 task_015 ...
"""

from __future__ import annotations

import inspect
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import anthropic
from loguru import logger
from pydantic import BaseModel

logger.remove()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_diff import build_env, init  # noqa: E402

from tau2.data_model.tasks import Task  # noqa: E402
from tau2.domains.banking_knowledge import tools as T  # noqa: E402

D = "data/tau2/domains/banking_knowledge"
OUT = "adapted-harness/diagnostics/out/derivability.json"
MODEL = "claude-opus-5-5"
AGENT = dict(inspect.getmembers(T.KnowledgeTools, inspect.isfunction))
USER = dict(inspect.getmembers(T.KnowledgeUserTools, inspect.isfunction))
WRITE = {
    n
    for n, f in AGENT.items()
    if getattr(f, "__discoverable__", False)
    and str(getattr(f, "__tool_type__", "")).endswith("WRITE")
}
SKIP = {
    "log_verification",
    "unlock_discoverable_agent_tool",
    "request_human_agent_transfer",
    "list_discoverable_agent_tools",
}


class Call(BaseModel):
    actor: str  # "agent" or "customer"
    tool: str  # tool name (for discoverable agent tools: the discoverable tool's own name)
    arguments_json: str  # JSON object of the arguments
    rule: str  # the document rule that determines this call / its judgement arguments


class Plan(BaseModel):
    calls: list[Call]
    open_points: list[str]  # decisions the documents do not determine, if any


PROMPT = """You are auditing a bank's customer-service procedures. Below are the agent policy, the knowledge-base
documents that govern one customer conversation, the tools those documents name, everything the customer
will say or do, and the facts the bank's lookup tools return for this customer.

Work out, strictly from the documents, the complete list of STATE-CHANGING calls that a correct agent
makes and that the customer makes with tools the agent gives them. Include: discoverable write tools
(name the tool itself, with its arguments), giving a tool to the customer (tool "give_discoverable_user_tool"
with argument discoverable_tool_name), transferring to a human (tool "transfer_to_human_agents" with its
reason), and the customer's own actions (actor "customer"). Do not list lookups, unlocks or identity
logging. For every argument that is a judgement rather than a copied fact, the `rule` must cite the
document rule that determines it. If the documents leave a decision open, still give your best reading
and add it to open_points.

<policy>
{policy}
</policy>

<tools>
{tools}
</tools>

<customer_script>
{script}
</customer_script>

<facts_from_lookups>
{facts}
</facts_from_lookups>

<documents>
{docs}
</documents>"""


def gold_writes(task: Task):
    out = []
    for a in task.evaluation_criteria.actions or []:
        if a.name in SKIP:
            continue
        if a.name == "call_discoverable_agent_tool":
            inner = a.arguments.get("agent_tool_name")
            if inner in WRITE:
                out.append(
                    ("agent", inner, json.loads(a.arguments.get("arguments") or "{}"))
                )
        elif a.name == "give_discoverable_user_tool":
            out.append(
                (
                    "agent",
                    a.name,
                    {
                        "discoverable_tool_name": a.arguments.get(
                            "discoverable_tool_name"
                        )
                    },
                )
            )
        elif a.name == "transfer_to_human_agents":
            out.append(("agent", a.name, {"reason": a.arguments.get("reason")}))
        elif a.name == "call_discoverable_user_tool":
            out.append(
                (
                    "customer",
                    a.arguments.get("discoverable_tool_name"),
                    json.loads(a.arguments.get("arguments") or "{}"),
                )
            )
        elif a.requestor == "user":
            out.append(("customer", a.name, dict(a.arguments)))
        elif a.name == "change_user_email":
            out.append(("agent", a.name, dict(a.arguments)))
    return out


def lookup_facts(task: Task) -> str:
    """Replay only gold's READ calls on a fresh environment and record what the tools return."""
    env = build_env(task)
    init(env, task, [])
    lines = []
    for a in task.evaluation_criteria.actions or []:
        try:
            if a.name == "unlock_discoverable_agent_tool":
                env.make_tool_call(
                    tool_name=a.name, requestor=a.requestor, **a.arguments
                )
                continue
            inner = (
                a.arguments.get("agent_tool_name")
                if a.name == "call_discoverable_agent_tool"
                else None
            )
            is_read = (inner and inner not in WRITE) or (
                a.name.startswith("get_") and a.requestor == "assistant"
            )
            if not is_read:
                continue
            res = env.make_tool_call(
                tool_name=a.name, requestor=a.requestor, **a.arguments
            )
            lines.append(
                f"### {inner or a.name}({json.dumps(a.arguments.get('arguments') or a.arguments)[:200]})\n{str(res)[:6000]}"
            )
        except Exception as e:
            lines.append(f"### {a.name}: error {e}")
    return "\n\n".join(lines) or "(no lookups in the reference path)"


def same(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b or str(a).lower() == str(b).lower()
    try:
        return abs(float(a) - float(b)) < 0.006
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip()


def compare(gold, calls):
    """Greedy match each gold write to the oracle call of the same tool agreeing on most arguments."""
    used, rows = set(), []
    parsed = []
    for c in calls:
        try:
            parsed.append((c.actor, c.tool, json.loads(c.arguments_json or "{}")))
        except Exception:
            parsed.append((c.actor, c.tool, {}))
    for actor, tool, args in gold:
        best, best_i = None, None
        for i, (_, t2, a2) in enumerate(parsed):
            if i in used or t2 != tool:
                continue
            score = sum(same(args.get(k), a2.get(k)) for k in args)
            if best is None or score > best:
                best, best_i = score, i
        if best_i is None:
            rows.append({"tool": tool, "status": "missing", "diff": {}})
            continue
        used.add(best_i)
        a2 = parsed[best_i][2]
        diff = {
            k: [a2.get(k, "—"), v] for k, v in args.items() if not same(v, a2.get(k))
        }
        rows.append(
            {"tool": tool, "status": "match" if not diff else "differs", "diff": diff}
        )
    extra = [parsed[i][1] for i in range(len(parsed)) if i not in used]
    return rows, extra


def main(task_ids):
    from tau2.domains.banking_knowledge.environment import get_environment

    policy = get_environment(retrieval_variant="terminal_use").get_policy()
    client = anthropic.Anthropic()
    docs_all = {}
    for f in os.listdir(f"{D}/documents"):
        d = json.load(open(f"{D}/documents/{f}"))
        docs_all[d["id"]] = d

    def one(job):
        tid, k = job
        raw = json.load(open(f"{D}/tasks/{tid}.json"))
        task = Task(**raw)
        req = [
            docs_all[i] for i in (raw.get("required_documents") or []) if i in docs_all
        ]
        text = "\n".join(d["content"] for d in req)
        named = sorted(
            {
                n
                for n in list(AGENT) + list(USER)
                if re.search(rf"\b{re.escape(n)}\b", text)
                and (getattr(AGENT.get(n) or USER.get(n), "__discoverable__", False))
            }
        )
        base = [
            "transfer_to_human_agents",
            "give_discoverable_user_tool",
            "change_user_email",
            "apply_for_credit_card",
            "submit_referral",
            "submit_transaction",
        ]
        tools = "\n\n".join(
            f"## {n}\n{inspect.getdoc(AGENT.get(n) or USER.get(n))}"
            for n in named + base
            if (AGENT.get(n) or USER.get(n))
        )
        ins = raw["user_scenario"]["instructions"]
        prompt = PROMPT.format(
            policy=policy,
            tools=tools,
            script=ins if isinstance(ins, str) else json.dumps(ins, indent=1),
            facts=lookup_facts(task),
            docs="\n\n".join(
                f'<document id="{d["id"]}">\n# {d["title"]}\n{d["content"]}\n</document>'
                for d in req
            ),
        )
        for _ in range(2):
            try:
                r = client.messages.parse(
                    model=MODEL,
                    max_tokens=16000,
                    output_config={"effort": "high"},
                    messages=[{"role": "user", "content": prompt}],
                    output_format=Plan,
                )
                return (
                    tid,
                    k,
                    r.parsed_output,
                    (r.usage.input_tokens, r.usage.output_tokens),
                )
            except Exception as e:
                err = e
        print("failed", tid, str(err)[:120])
        return tid, k, None, (0, 0)

    jobs = [(t, k) for t in task_ids for k in (1, 2)]
    res, tok = {}, [0, 0]
    with ThreadPoolExecutor(6) as pool:
        for tid, k, plan, t in pool.map(one, jobs):
            tok[0] += t[0]
            tok[1] += t[1]
            res.setdefault(tid, {})[k] = plan
    report = {}
    for tid in task_ids:
        task = Task(**json.load(open(f"{D}/tasks/{tid}.json")))
        gold = gold_writes(task)
        runs = {}
        for k, plan in res.get(tid, {}).items():
            if plan is None:
                continue
            rows, extra = compare(gold, plan.calls)
            runs[k] = {
                "rows": rows,
                "extra": extra,
                "open_points": plan.open_points,
                "calls": [c.model_dump() for c in plan.calls],
            }
        ok = [
            all(r["status"] == "match" for r in v["rows"]) and not v["extra"]
            for v in runs.values()
        ]
        agree = len(runs) == 2 and json.dumps(
            runs[1]["rows"], sort_keys=True
        ) == json.dumps(runs[2]["rows"], sort_keys=True)
        verdict = (
            "derivable"
            if ok and all(ok)
            else (
                "under-determined"
                if len(runs) == 2 and not agree
                else "not derivable as gold"
            )
        )
        report[tid] = {"verdict": verdict, "gold_writes": len(gold), "runs": runs}
        print(f"\n## {tid}: {verdict}  (gold state changes: {len(gold)})")
        for k, v in runs.items():
            bad = [r for r in v["rows"] if r["status"] != "match"]
            print(
                f"  run {k}: {len(v['rows']) - len(bad)}/{len(v['rows'])} gold changes reproduced; extra calls {v['extra'] or '-'}"
            )
            for r in bad:
                print(
                    f"     {r['status']:8} {r['tool']}  oracle→gold {json.dumps(r['diff'])[:230]}"
                )
            for o in v["open_points"][:3]:
                print(f"     open: {o[:200]}")
    json.dump(report, open(OUT, "w"), indent=1)
    c = {}
    for v in report.values():
        c[v["verdict"]] = c.get(v["verdict"], 0) + 1
    print(f"\nverdicts: {c}; tokens in/out {tok[0]}/{tok[1]}")


if __name__ == "__main__":
    main(sys.argv[1:])
