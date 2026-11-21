"""Build two KB-only artifacts for the v6 harness (no task, gold or DB data):

1. workflows.json: for each internal procedure document, its ordered steps and the tool each
   step uses. The harness turns the steps of documents the agent reads into a to-do list and
   checks the order before later steps' tools run.
2. known_issues.json: for each discoverable WRITE tool, the conflicts and ambiguities across
   the documents that govern it (its contract sources + their connected documents), each with
   quotes, and whether the KB resolves it (and how) or leaves it open.

Every quote is checked against the cited document; entries that fail are dropped.

usage (repo root):
  set -a; . ./.env; set +a
  UV_FROZEN=1 uv run --with anthropic python adapted-harness/kb_index/build_workflows_issues.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Literal, Optional

import anthropic
from pydantic import BaseModel

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
MODEL = "claude-opus-5-5"


class Step(BaseModel):
    order: int
    step: str
    tool: Optional[str]  # exact tool name if the step uses one, else null
    condition: Optional[str]  # when the step applies (e.g. "if the card was lost")
    quote: str


class Workflow(BaseModel):
    scenario: str  # the situation this procedure handles
    steps: list[Step]


class DocQuote(BaseModel):
    doc_id: str
    quote: str


class Issue(BaseModel):
    topic: str  # the decision or argument affected
    kind: Literal["conflict", "ambiguity", "cross_document_dependency"]
    description: str
    doc_quotes: list[DocQuote]
    resolved_by_kb: bool
    resolution: Optional[
        str
    ]  # how the KB resolves it, citing the deciding document; else null


class ToolIssues(BaseModel):
    issues: list[Issue]


WF_PROMPT = """From this bank knowledge-base procedure document, extract the procedure as ordered steps.
For each step give: the action, the exact tool name it uses (tools look like `name_1234` or are named
explicitly; null if none), the condition under which the step applies (null if always), and an exact
verbatim quote of the sentence that states the step. Only steps the document states; keep its order.
If the document is not a procedure, return an empty steps list.

<document id="{doc_id}">
# {title}

{content}
</document>"""

ISSUE_PROMPT = """An agent must call the banking tool `{tool}` correctly, following the knowledge base below.
List the places where these documents create risk of a wrong call:
- conflict: two documents (or two clauses) prescribe different things for the same decision or value;
- ambiguity: a needed decision or value is not determined by the documents;
- cross_document_dependency: a rule in one document only works together with a rule or step in another
  (e.g. a status a procedure requires that another procedure changes, or an anchor date defined elsewhere).
For each: the topic (decision or tool argument), a description, exact verbatim quotes with doc ids, whether
the KB itself resolves it, and if so how (naming the document that decides it). Do not invent rules.
Only issues the documents show. At most 6, most consequential first.

Tool description:
{docstring}

Documents:
{documents}"""


def norm(s: str) -> str:
    s = re.sub(r"[*`]+", "", str(s))
    s = re.sub(r"[|#>]+", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower().strip("\"'.:;- ")


def main(issues_only: bool = "--issues-only" in sys.argv):
    import inspect

    from tau2.agent.adapted import kb as K
    from tau2.agent.adapted.config import HarnessConfig
    from tau2.domains.banking_knowledge import tools as T

    kb = K.kb()
    cfg = HarnessConfig()
    contracts = K.contracts(cfg.contracts_path)
    client = anthropic.Anthropic()
    tok = [0, 0]

    def parse(prompt, schema):
        for _ in range(2):
            try:
                r = client.messages.parse(
                    model=MODEL,
                    max_tokens=16000,
                    output_config={"effort": "medium"},
                    messages=[{"role": "user", "content": prompt}],
                    output_format=schema,
                )
                return r.parsed_output, (r.usage.input_tokens, r.usage.output_tokens)
            except Exception as e:
                err = e
        print("  failed:", str(err)[:120])
        return None, (0, 0)

    # ---- workflows over internal procedure docs ----
    procs = (
        []
        if issues_only
        else sorted(i for i, d in kb.docs.items() if "internal" in d["title"].lower())
    )

    def wf(i):
        d = kb.docs[i]
        out, t = parse(
            WF_PROMPT.format(doc_id=i, title=d["title"], content=d["content"]), Workflow
        )
        return i, out, t

    workflows, dropped = {}, 0
    with ThreadPoolExecutor(8) as pool:
        for i, out, t in pool.map(wf, procs):
            tok[0] += t[0]
            tok[1] += t[1]
            if not out or not out.steps:
                continue
            text = norm(kb.docs[i]["content"])
            steps = []
            for s in sorted(out.steps, key=lambda s: s.order):
                if norm(s.quote) and norm(s.quote) in text:
                    steps.append(s.model_dump())
                else:
                    dropped += 1
            if steps:
                workflows[i] = {"scenario": out.scenario, "steps": steps}
    print(
        f"workflows: {len(workflows)} procedure docs with steps; {dropped} steps dropped (quote not found)"
    )

    # ---- known issues per write tool ----
    members = dict(inspect.getmembers(T.KnowledgeTools, inspect.isfunction))
    idx = K.index(cfg.index_path)

    def issues(tool):
        src = list(
            contracts.get(tool, {}).get("source_docs") or kb.tool_docs.get(tool, [])
        )
        rel = []
        for d in src:
            e = idx.get(d, {})
            rel += [o for o, _, _ in e.get("needs", [])][:4]
        ids = list(dict.fromkeys(src + rel))[:7]
        body = "\n\n".join(
            f'<document id="{i}">\n# {kb.docs[i]["title"]}\n\n{kb.docs[i]["content"]}\n</document>'
            for i in ids
        )
        out, t = parse(
            ISSUE_PROMPT.format(
                tool=tool, docstring=inspect.getdoc(members[tool]), documents=body
            ),
            ToolIssues,
        )
        return tool, ids, out, t

    known, idropped = {}, 0
    with ThreadPoolExecutor(6) as pool:
        for tool, ids, out, t in pool.map(issues, sorted(contracts)):
            tok[0] += t[0]
            tok[1] += t[1]
            if not out:
                continue
            kept = []
            for k, iss in enumerate(out.issues, 1):
                quotes = []
                for q in iss.doc_quotes:
                    did = kb.resolve(q.doc_id)
                    if (
                        did
                        and norm(q.quote)
                        and norm(q.quote) in norm(kb.docs[did]["content"])
                    ):
                        quotes.append({"doc_id": did, "quote": q.quote})
                if quotes:
                    kept.append(
                        {"id": f"I{k}", **iss.model_dump(), "doc_quotes": quotes}
                    )
                else:
                    idropped += 1
            if kept:
                known[tool] = {"docs": ids, "issues": kept}
    print(
        f"known issues: {sum(len(v['issues']) for v in known.values())} across {len(known)} tools; {idropped} dropped"
    )

    if not issues_only:
        json.dump(
            {"model": MODEL, "workflows": workflows},
            open(f"{OUT}/workflows.json", "w"),
            indent=1,
        )
    json.dump(
        {"model": MODEL, "tools": known},
        open(f"{OUT}/known_issues.json", "w"),
        indent=1,
    )
    print(f"tokens in/out {tok[0]}/{tok[1]}")


if __name__ == "__main__":
    main()
