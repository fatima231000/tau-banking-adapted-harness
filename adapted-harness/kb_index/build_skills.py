"""Assemble skill cards from the compiled KB artifacts. Deterministic: no model calls.

One card per discoverable WRITE tool, built from artifacts that were extracted from the KB
alone and quote-checked (contracts.json, workflows.json, known_issues.json):
  - when to use it and the source documents
  - procedure steps in order, per source procedure
  - lookups that prove each condition
  - how each argument is determined
  - open issues the documents leave unresolved, and those they resolve
  - a freshness stamp: sha256 of each source document's content

usage (repo root): uv run --frozen python adapted-harness/kb_index/build_skills.py
Output: adapted-harness/kb_index/out/skills.json
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import sys

from loguru import logger

logger.remove()
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def doc_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def main():
    from tau2.agent.adapted import kb as K
    from tau2.domains.banking_knowledge import tools as T

    kb = K.kb()
    contracts = json.load(open(f"{OUT}/contracts.json"))["contracts"]
    workflows = json.load(open(f"{OUT}/workflows.json"))["workflows"]
    issues = json.load(open(f"{OUT}/known_issues.json"))["tools"]
    rulings = {}
    if os.path.exists(
        f"{OUT}/rulings.json"
    ):  # conflicts resolved at compile time (build_rulings.py)
        rulings = json.load(open(f"{OUT}/rulings.json"))["rulings"]
    members = dict(inspect.getmembers(T.KnowledgeTools, inspect.isfunction))

    skills = {}
    for tool, c in sorted(contracts.items()):
        sources = list(c.get("source_docs") or kb.tool_docs.get(tool, []))
        purpose = (inspect.getdoc(members[tool]) or "").split("\n")[0]
        L = [
            f"SKILL: {tool}",
            f"Purpose: {purpose}",
            "Source documents (read the one that fits before acting; quote rules from it): "
            + ", ".join(f"{K.sanitize(d)}.md" for d in sources),
        ]
        scenarios = []
        for d in sources:
            wf = workflows.get(d)
            if not wf:
                continue
            scenarios.append(wf["scenario"])
            L.append(f"\nProcedure: {wf['scenario']}  [{K.sanitize(d)}.md]")
            for s in wf["steps"]:
                tool_note = f"  -> {s['tool']}" if s.get("tool") else ""
                cond = f"  (only if {s['condition']})" if s.get("condition") else ""
                L.append(f"  {s['order']}. {s['step']}{tool_note}{cond}")
        if c.get("prerequisite_calls"):
            L.append("\nLook up first (each proves a condition below):")
            seen = set()
            for p in c["prerequisite_calls"]:
                if p["tool"] not in seen:
                    seen.add(p["tool"])
                    L.append(f"  - {p['tool']}: {p['purpose']}")
        if c.get("preconditions"):
            L.append("\nConditions that must hold:")
            for p in c["preconditions"]:
                v = (
                    f"  [check with {p['verifying_tool']}]"
                    if p.get("verifying_tool")
                    else ""
                )
                L.append(f"  - {p['condition']}{v}")
        if c.get("derived_arguments"):
            L.append("\nArguments set by a rule (not copied from a lookup):")
            for p in c["derived_arguments"]:
                L.append(f"  - {p['argument']}: {p['rule']}")
        iss = issues.get(tool, {}).get("issues", [])
        if iss:
            L.append(
                "\nRulings where the documents conflict or leave a gap (follow these):"
            )
            for i in iss:
                r = rulings.get(tool, {}).get(i["id"])
                if r:
                    tail = f"\n      RULING: {r['ruling']}"
                elif i.get("resolved_by_kb") and i.get("resolution"):
                    tail = f"\n      RULING: {i['resolution']}"
                else:
                    tail = "\n      No ruling: read the source and decide from its wording."
                L.append(f"  - {i['topic']}: {i['description']}{tail}")
        skills[tool] = {
            "id": tool,
            "purpose": purpose,
            "scenarios": scenarios,
            "sources": {d: doc_hash(kb.docs[d]["content"]) for d in sources},
            "open_issues": sum(1 for i in iss if not i.get("resolved_by_kb")),
            "text": "\n".join(L),
        }
    json.dump({"skills": skills}, open(f"{OUT}/skills.json", "w"), indent=1)
    sizes = sorted(len(s["text"]) for s in skills.values())
    print(
        f"{len(skills)} skill cards; chars min/median/max {sizes[0]}/{sizes[len(sizes) // 2]}/{sizes[-1]}"
    )


if __name__ == "__main__":
    main()
