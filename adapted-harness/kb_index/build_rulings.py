"""Resolve the KB's conflicts and gaps at compile time, under fixed general principles.

For each discoverable WRITE tool, takes the issues in known_issues.json (conflicts, ambiguities,
cross-document dependencies found in the KB) and produces one RULING per issue: a concrete
instruction the agent can follow, the principle it rests on, and supporting quotes.
No task, gold or DB data is read: the principles are general and stated below.

usage (repo root):
  set -a; . ./.env; set +a
  UV_FROZEN=1 uv run --with anthropic python adapted-harness/kb_index/build_rulings.py
Output: adapted-harness/kb_index/out/rulings.json
"""

from __future__ import annotations

import inspect
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Literal

import anthropic
from pydantic import BaseModel

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
MODEL = "claude-opus-5-5"

PRINCIPLES = """Precedence principles (apply in this order; name the one you used):
P1 tool-definition: for a tool argument, the tool's own parameter definition (allowed values and what
   each means) beats wording in a document.
P2 mandatory-over-discretionary: a rule that says something is required / must happen governs when its
   conditions are all met; a clause that says something is "not required" or "may" be done describes the
   cases outside that mandatory set, and does not cancel it.
P3 explicit-definition: a document that defines a term, anchor or threshold explicitly beats one that
   mentions it loosely or by example.
P4 stated-rule-over-example: a rule stated in general beats an example that contradicts it.
P5 internal-over-customer-facing: an internal procedure for agents beats customer-facing guidance; steps
   addressed to the customer ("confirm your...", "prepare your...") are for the customer to self-check,
   not conditions the agent must verify, unless an internal procedure also lists them.
P6 narrower-scope: the rule written for this exact product, category or situation beats the general one.
P7 available-data: if a rule depends on a fact no tool provides, derive it from the data the tools do
   provide by the most direct inference and say so; if only the customer can know it, ask the customer.
P8 customer-request: where the documents allow more than one action, do what the customer asked;
   advice in a document ("recommend X instead") is something to tell the customer, not a substitute
   for their request."""


class Quote(BaseModel):
    doc_id: str
    quote: str


class Ruling(BaseModel):
    issue_id: str
    ruling: str  # the concrete instruction: what to do / which value to pass, in one or two sentences
    principle: Literal["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
    confidence: Literal["high", "medium", "low"]
    quotes: list[Quote]


class Rulings(BaseModel):
    rulings: list[Ruling]


PROMPT = """A bank's knowledge base has conflicts and gaps around one internal tool. You are the policy
owner resolving them so that agents act consistently. For EVERY issue below, write one ruling: a
concrete instruction an agent can follow (what to do, or exactly which value to pass), decided by the
precedence principles, with exact verbatim quotes from the documents that support it. Every issue
gets a ruling: when the documents truly leave it open, apply P7 or P8. Do not invent facts or rules
that no document supports.

{principles}

Tool: `{tool}`
Tool description and parameters:
{docstring}

Issues to resolve:
{issues}

Documents:
{documents}"""


def norm(s: str) -> str:
    s = re.sub(r"[*`]+", "", str(s))
    s = re.sub(r"[|#>]+", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower().strip("\"'.:;- ")


def main():
    from tau2.agent.adapted import kb as K
    from tau2.domains.banking_knowledge import tools as T

    kb = K.kb()
    known = json.load(open(f"{OUT}/known_issues.json"))["tools"]
    members = dict(inspect.getmembers(T.KnowledgeTools, inspect.isfunction))
    client = anthropic.Anthropic()

    def one(tool):
        v = known[tool]
        body = "\n\n".join(
            f'<document id="{i}">\n# {kb.docs[i]["title"]}\n\n{kb.docs[i]["content"]}\n</document>'
            for i in v["docs"]
        )
        issues = "\n".join(
            f"- {i['id']} [{i['kind']}] {i['topic']}: {i['description']}"
            for i in v["issues"]
        )
        for _ in range(2):
            try:
                r = client.messages.parse(
                    model=MODEL,
                    max_tokens=16000,
                    output_config={"effort": "medium"},
                    output_format=Rulings,
                    messages=[
                        {
                            "role": "user",
                            "content": PROMPT.format(
                                principles=PRINCIPLES,
                                tool=tool,
                                docstring=inspect.getdoc(members[tool]),
                                issues=issues,
                                documents=body,
                            ),
                        }
                    ],
                )
                return (
                    tool,
                    r.parsed_output,
                    (r.usage.input_tokens, r.usage.output_tokens),
                )
            except Exception as e:
                err = e
        print("  failed", tool, str(err)[:100])
        return tool, None, (0, 0)

    out, tok, unsupported = {}, [0, 0], 0
    with ThreadPoolExecutor(6) as pool:
        for tool, res, t in pool.map(one, sorted(known)):
            tok[0] += t[0]
            tok[1] += t[1]
            if not res:
                continue
            ids = {i["id"] for i in known[tool]["issues"]}
            kept = {}
            for r in res.rulings:
                if r.issue_id not in ids:
                    continue
                quotes = []
                for q in r.quotes:
                    did = kb.resolve(q.doc_id)
                    if (
                        did
                        and norm(q.quote)
                        and norm(q.quote) in norm(kb.docs[did]["content"])
                    ):
                        quotes.append({"doc_id": did, "quote": q.quote})
                if not quotes:
                    unsupported += 1  # kept, but marked: no verified quote behind it
                kept[r.issue_id] = {
                    "ruling": r.ruling,
                    "principle": r.principle,
                    "confidence": r.confidence,
                    "quotes": quotes,
                    "supported": bool(quotes),
                }
            out[tool] = kept
    n = sum(len(v) for v in out.values())
    from collections import Counter

    pc = Counter(r["principle"] for v in out.values() for r in v.values())
    cc = Counter(r["confidence"] for v in out.values() for r in v.values())
    json.dump(
        {"model": MODEL, "principles": PRINCIPLES, "rulings": out},
        open(f"{OUT}/rulings.json", "w"),
        indent=1,
    )
    print(
        f"{n} rulings across {len(out)} tools; without a verified quote: {unsupported}; "
        f"principles {dict(pc)}; confidence {dict(cc)}; tokens in/out {tok[0]}/{tok[1]}"
    )


if __name__ == "__main__":
    main()
