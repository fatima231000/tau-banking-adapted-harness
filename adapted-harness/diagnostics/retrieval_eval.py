"""Offline quality check of hybrid retrieval: BM25 KB_search, then 1-hop expansion through the
connected index. Grader-side: required_documents (DEV only) are used to SCORE, never as input.

Query per task = what the customer says in the given baseline DEV run (agent-visible text).
Reports recall / precision of required docs for:
  bm25@k                  τ²'s own KB_search pipeline (bm25_grep retrieval config)
  bm25@k + index(1 hop)   + docs kb_related would return for each retrieved doc
usage: uv run --frozen python adapted-harness/diagnostics/retrieval_eval.py
"""

import json
import os
import re
import sys
from dataclasses import replace

from loguru import logger

logger.remove()
from tau2.agent.adapted import kb as K  # noqa: E402
from tau2.agent.adapted.config import HarnessConfig  # noqa: E402
from tau2.data_model.message import ToolCall  # noqa: E402
from tau2.domains.banking_knowledge.environment import get_environment  # noqa: E402

D = "data/tau2/domains/banking_knowledge"
RUN = "adapted-harness/baseline/dev-sonnet55-terminal/results.json"
OUT = "adapted-harness/kb_index/out"
INDEXES = {"proc90": f"{OUT}/index_proc90.json", "all698": f"{OUT}/index_all698.json"}


def ids(text):
    return [i for t in re.findall(r"ID:\s*(\S+)", text) if (i := K.kb().resolve(t))]


def main(k_list=(5, 10), hop_from=5, hop_limit=5):
    env = get_environment(retrieval_variant="bm25_grep")
    sims = {
        s["task_id"]: s
        for s in json.load(open(RUN))["simulations"]
        if s["task_id"] != "task_102"
    }
    rows = []
    for t in open("adapted-harness/splits/dev.txt").read().split():
        req = set(
            json.load(open(f"{D}/tasks/{t}.json")).get("required_documents") or []
        )
        cust = [
            m["content"]
            for m in sims[t]["messages"]
            if m["role"] == "user" and (m.get("content") or "").strip()
        ]
        q_first, q_all = cust[0][:1500], " ".join(cust)[:4000]
        row = {"task": t, "req": len(req)}
        for qname, q in (("first", q_first), ("all", q_all)):
            got = ids(
                env.get_response(
                    ToolCall(id="q", name="KB_search", arguments={"query": q})
                ).content
            )
            for k in k_list:
                top = got[:k]
                row[f"{qname}_bm25@{k}"] = (len(set(top) & req), len(top))
            for iname, path in INDEXES.items():
                if not os.path.exists(path):
                    continue
                cfg = replace(HarnessConfig(), index_path=path)
                exp = set(got[:hop_from])
                for d in got[:hop_from]:
                    exp |= set(K.related_text(cfg, d, limit=hop_limit)[1])
                row[f"{qname}_bm25@{hop_from}+{iname}"] = (len(exp & req), len(exp))
        rows.append(row)

    keys = [k for k in rows[0] if k not in ("task", "req")]
    R = sum(r["req"] for r in rows)
    print(f"{len(rows)} DEV tasks, {R} required docs in total\n")
    print(
        "| retrieval | query | recall of required docs | docs returned (mean) | precision |"
    )
    print("|---|---|---|---|---|")
    for key in keys:
        hit = sum(r[key][0] for r in rows)
        n = sum(r[key][1] for r in rows)
        q, sysname = key.split("_", 1)
        print(
            f"| {sysname} | {q} customer text | {hit}/{R} = {hit / R:.0%} | {n / len(rows):.1f} | {hit / max(n, 1):.0%} |"
        )
    json.dump(rows, open(f"{OUT}/retrieval_eval.json", "w"), indent=1)


if __name__ == "__main__":
    main()
    sys.exit(0)
