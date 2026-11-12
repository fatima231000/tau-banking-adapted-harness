#!/bin/sh
# usage: adapted-harness/export_traces.sh data/simulations/<run>  -> writes <run_dir>/traces/<task_id>.md and traces/index.md
exec python3 -I - "$1" <<'EOF'
import json, sys, os, collections
run = sys.argv[1].rstrip("/")
r = json.load(open(os.path.join(run, "results.json")))
info = r.get("info") or {}
agent_llm = (info.get("agent_info") or {}).get("llm"); user_llm = (info.get("user_info") or {}).get("llm")
out = os.path.join(run, "traces"); os.makedirs(out, exist_ok=True)
CUT = 2000
def clip(t, n=CUT):
    t = t if isinstance(t, str) else json.dumps(t, ensure_ascii=False)
    return t if len(t) <= n else t[:n] + f"\n… [{len(t)-n} more chars]"
rows = []
EXCLUDE = {"task_102"}  # removed from DEV: its NL-assertion grader is hard-coded to OpenAI
import glob
for f in glob.glob(os.path.join(out, "task_102.md")): os.remove(f)
for s in sorted((s for s in r["simulations"] if s["task_id"] not in EXCLUDE), key=lambda s: s["task_id"]):
    tid = s["task_id"]; ri = s.get("reward_info") or {}
    reward = ri.get("reward"); db = (ri.get("db_check") or {}).get("db_match")
    msgs = s.get("messages") or []
    acost = sum((m.get("cost") or 0) for m in msgs if m.get("role") == "assistant")
    ucost = s.get("user_cost") or 0
    tools = collections.Counter(tc.get("name") for m in msgs for tc in (m.get("tool_calls") or []))
    status = "INFRA ERROR" if s.get("termination_reason") == "infrastructure_error" else ("PASS" if reward == 1 else "FAIL")
    L = [f"# {tid}: {status}", "",
         f"- run: `{os.path.basename(run)}`, trial {s.get('trial')}",
         f"- agent: `{agent_llm}`, customer simulator: `{user_llm}`, retrieval: `{info.get('retrieval_config')}`",
         f"- reward {reward}, DB match {db}, ended by `{s.get('termination_reason')}`",
         f"- {len(msgs)} messages, {round(s.get('duration') or 0)}s, cost ${acost+ucost:.2f} (agent ${acost:.2f}, customer ${ucost:.2f})",
         f"- tool calls: {dict(tools)}", ""]
    L += ["## Grading (grader-only: never give this to the agent)", ""]
    for c in (ri.get("action_checks") or []):
        a = c.get("action") or {}
        L.append(f"- {'OK  ' if c.get('action_match') else 'MISS'} `{a.get('name')}` {clip(a.get('arguments'), 300)}")
    if ri.get("reward_breakdown"): L.append(f"- reward breakdown: {ri.get('reward_breakdown')}")
    L += ["", "## Transcript", ""]
    names = {}
    for i, m in enumerate(msgs, 1):
        role = m.get("role"); content = m.get("content") or ""
        if role == "user":
            L += [f"**[{i}] customer:** {content}", ""]
        elif role == "assistant":
            if content.strip(): L += [f"**[{i}] agent:** {content}", ""]
            for tc in (m.get("tool_calls") or []):
                names[tc.get("id")] = tc.get("name")
                args = tc.get("arguments") or {}
                if tc.get("name") == "shell" and isinstance(args, dict) and "command" in args:
                    L += [f"**[{i}] agent → shell:**", "```sh", args["command"], "```", ""]
                else:
                    L += [f"**[{i}] agent → `{tc.get('name')}`** `{clip(args, 600)}`", ""]
        elif role == "tool":
            L += [f"**[{i}] tool result ({names.get(m.get('id'), m.get('name') or 'tool')}):**", "```", clip(content), "```", ""]
        else:
            L += [f"**[{i}] {role}:** {clip(content)}", ""]
    open(os.path.join(out, f"{tid}.md"), "w").write("\n".join(L))
    rows.append((tid, status, db, len(msgs), round(s.get("duration") or 0), acost + ucost, tools.get("shell", 0)))
idx = [f"# Traces: {os.path.basename(run)}", "", f"agent `{agent_llm}`, customer `{user_llm}`, retrieval `{info.get('retrieval_config')}`", "",
       "| task | result | DB match | messages | seconds | cost | shell calls |", "|---|---|---|---|---|---|---|"]
idx += [f"| [{t}]({t}.md) | {st} | {db} | {n} | {d} | ${c:.2f} | {sh} |" for t, st, db, n, d, c, sh in rows]
p = sum(1 for x in rows if x[1] == "PASS")
idx += ["", f"{p}/{len(rows)} passed, total ${sum(x[5] for x in rows):.2f}"]
open(os.path.join(out, "index.md"), "w").write("\n".join(idx))
print(f"{run}: {len(rows)} traces, {p} passed, ${sum(x[5] for x in rows):.2f}")
EOF
