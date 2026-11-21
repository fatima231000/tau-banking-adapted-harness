"""Build a tool-contract registry from the KB alone: prerequisites for every discoverable WRITE tool.

For each write tool, the model reads the KB documents that name it plus the tool's docstring and
the catalog of read tools, and returns a contract:
  - prerequisite_calls: read tools that must be called earlier in the conversation (enforceable)
  - preconditions: conditions that must hold, each with the tool that can verify it
  - ordering: steps that must precede or follow the call
  - derived_arguments: arguments whose value is set by a KB rule
Every entry must carry an exact quote; entries whose quote is not found in the cited document
are dropped (logged in `dropped`). No task, gold or DB data is read.

usage (repo root):
  set -a; . ./.env; set +a
  UV_FROZEN=1 uv run --with anthropic python adapted-harness/kb_index/build_contracts.py
Output: adapted-harness/kb_index/out/contracts.json and contracts_report.md
"""

from __future__ import annotations

import inspect
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Literal, Optional

import anthropic
from loguru import logger
from pydantic import BaseModel

logger.remove()
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
from tau2.domains.banking_knowledge import tools as T  # noqa: E402

DOCS_DIR = os.path.join(ROOT, "data/tau2/domains/banking_knowledge/documents")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
MODEL = "claude-opus-5-5"


class PrereqCall(BaseModel):
    tool: str  # an exact read-tool name from the catalog
    purpose: str
    doc_id: str
    quote: str


class Precondition(BaseModel):
    condition: str
    verifying_tool: Optional[
        str
    ]  # read tool (catalog) or initial tool that can confirm it, else null
    doc_id: str
    quote: str


class Ordering(BaseModel):
    relation: Literal["must_happen_before_this_call", "must_happen_after_this_call"]
    step: str
    doc_id: str
    quote: str


class DerivedArg(BaseModel):
    argument: str
    rule: str
    doc_id: str
    quote: str


class Contract(BaseModel):
    prerequisite_calls: list[PrereqCall]
    preconditions: list[Precondition]
    ordering: list[Ordering]
    derived_arguments: list[DerivedArg]


PROMPT = """You are writing a machine-checkable contract for one internal banking tool, from the bank's \
knowledge base. An agent harness will enforce it before the tool is called.

Tool: `{tool}`
Tool description and parameters:
{docstring}

Read tools the agent can call to check facts (discoverable ones must be unlocked first):
{catalog}

Knowledge-base documents that mention this tool, and the documents its description refers to:
{documents}

Write the contract:
- prerequisite_calls: read tools from the catalog that the documents require (explicitly or because a \
stated condition can only be checked with that tool's data) BEFORE calling `{tool}`. Only tools from the \
catalog. Empty if none.
- preconditions: every condition the documents impose on calling `{tool}` (eligibility, status, counts, \
limits, timing, pending items, consent, verification). For each, name the tool that can verify it, or null.
- ordering: steps the documents say must happen before or after this call.
- derived_arguments: parameters whose value the documents determine by a rule (not copied from a lookup).
Every entry needs `doc_id` (exactly as given) and an exact, verbatim `quote` (one sentence or table row) \
from that document. Only what the documents state; do not invent requirements."""


def load_docs():
    docs = {}
    for f in sorted(os.listdir(DOCS_DIR)):
        if f.endswith(".json"):
            d = json.load(open(os.path.join(DOCS_DIR, f)))
            docs[d["id"]] = d
    return docs


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower().strip("\"'`*|- ")


def main():
    os.makedirs(OUT, exist_ok=True)
    docs = load_docs()
    members = dict(inspect.getmembers(T.KnowledgeTools, inspect.isfunction))
    disc = {n: f for n, f in members.items() if getattr(f, "__discoverable__", False)}
    kind = lambda f: str(getattr(f, "__tool_type__", ""))  # noqa: E731
    writes = sorted(
        n
        for n, f in disc.items()
        if kind(f).endswith("WRITE") and n != "example_agent_tool_0000"
    )
    reads = {n: f for n, f in disc.items() if kind(f).endswith("READ")}
    initial_reads = {
        n: f
        for n, f in members.items()
        if getattr(f, "__tool__", False)
        and not getattr(f, "__discoverable__", False)
        and kind(f).endswith("READ")
    }
    catalog = "\n".join(
        f"- `{n}`{' (discoverable)' if n in reads else ''}: {(inspect.getdoc(f) or '').split(chr(10))[0][:200]}"
        for n, f in sorted({**reads, **initial_reads}.items())
    )
    valid_tools = set(reads) | set(initial_reads)

    def related(tool):
        f = disc[tool]
        doc = inspect.getdoc(f) or ""
        ids = [i for i, d in docs.items() if tool in d["content"]]
        ids += [
            i
            for i, d in docs.items()
            if len(d["title"]) >= 18
            and d["title"].lower() in doc.lower()
            and i not in ids
        ]
        return ids

    client = anthropic.Anthropic()

    def build(tool):
        ids = related(tool)
        body = "\n\n".join(
            f'<document id="{i}">\n# {docs[i]["title"]}\n\n{docs[i]["content"]}\n</document>'
            for i in ids
        )
        resp = client.messages.parse(
            model=MODEL,
            max_tokens=16000,
            output_config={"effort": "medium"},
            output_format=Contract,
            messages=[
                {
                    "role": "user",
                    "content": PROMPT.format(
                        tool=tool,
                        docstring=inspect.getdoc(disc[tool]),
                        catalog=catalog,
                        documents=body or "(none)",
                    ),
                }
            ],
        )
        if resp.stop_reason == "refusal":
            raise RuntimeError(f"{tool}: refusal")
        return (
            tool,
            ids,
            resp.parsed_output,
            (resp.usage.input_tokens, resp.usage.output_tokens),
        )

    contracts, dropped, tok = {}, [], [0, 0]
    with ThreadPoolExecutor(5) as pool:
        for tool, ids, c, t in pool.map(build, writes):
            tok[0] += t[0]
            tok[1] += t[1]
            kept = {}
            for field in (
                "prerequisite_calls",
                "preconditions",
                "ordering",
                "derived_arguments",
            ):
                kept[field] = []
                for e in getattr(c, field):
                    e = e.model_dump()
                    text = docs.get(e["doc_id"], {}).get("content", "")
                    ok = (
                        e["doc_id"] in ids
                        and norm(e["quote"])
                        and norm(e["quote"]) in norm(text)
                    )
                    if field == "prerequisite_calls" and e["tool"] not in valid_tools:
                        ok = False
                    if field == "preconditions" and e.get("verifying_tool") not in (
                        None,
                        *valid_tools,
                    ):
                        e["verifying_tool"] = None
                    (kept[field] if ok else dropped).append(
                        e if ok else {"tool": tool, "field": field, **e}
                    )
            contracts[tool] = {"source_docs": ids, **kept}
            print(
                f"{tool}: docs {len(ids)}, prereq calls {len(kept['prerequisite_calls'])}, "
                f"preconditions {len(kept['preconditions'])}, ordering {len(kept['ordering'])}, "
                f"derived {len(kept['derived_arguments'])}"
            )

    json.dump(
        {
            "model": MODEL,
            "tokens": {"input": tok[0], "output": tok[1]},
            "contracts": contracts,
            "dropped": dropped,
        },
        open(f"{OUT}/contracts.json", "w"),
        indent=1,
    )

    L = [
        "# Tool-contract registry (built from the KB)",
        "",
        f"Model `{MODEL}`; tokens in/out {tok[0]}/{tok[1]}; {len(dropped)} entries dropped for unverifiable quotes.",
        "",
        "| tool | source docs | prerequisite calls | preconditions | ordering | derived args |",
        "|---|---|---|---|---|---|",
    ]
    for t, c in contracts.items():
        L.append(
            f"| `{t}` | {len(c['source_docs'])} | {', '.join(sorted({p['tool'] for p in c['prerequisite_calls']})) or '-'} "
            f"| {len(c['preconditions'])} | {len(c['ordering'])} | {', '.join(d['argument'] for d in c['derived_arguments']) or '-'} |"
        )
    L += ["", "## Contracts", ""]
    for t, c in contracts.items():
        L.append(f"### `{t}`")
        for p in c["prerequisite_calls"]:
            L.append(
                f"- **call first** `{p['tool']}`: {p['purpose']}  \n  > {p['quote']} ({p['doc_id']})"
            )
        for p in c["preconditions"]:
            L.append(
                f"- **condition** {p['condition']} (verify: {p['verifying_tool']})  \n  > {p['quote']} ({p['doc_id']})"
            )
        for p in c["ordering"]:
            L.append(f"- **{p['relation']}**: {p['step']}")
        for p in c["derived_arguments"]:
            L.append(f"- **derived** `{p['argument']}`: {p['rule']}")
        L.append("")
    open(f"{OUT}/contracts_report.md", "w").write("\n".join(L))
    print(f"wrote {OUT}/contracts.json; dropped {len(dropped)}; tokens {tok}")


if __name__ == "__main__":
    main()
