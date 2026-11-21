"""Offline KB interconnection index, built from the KB alone (no task, gold or DB data).

Two methods over the same document sample:
  1. BM25: lexical doc-to-doc similarity.
  2. Entity/relation extraction with Claude: typed entities, relations with evidence quotes,
     and what each doc NEEDS from elsewhere vs. PROVIDES. A canonicalisation pass merges
     names across docs; docs are then linked by needs→provides, shared tools, shared
     specific entities.

usage (from repo root; the anthropic SDK is pulled in for this process only):
  set -a; . ./.env; set +a
  UV_FROZEN=1 uv run --with anthropic python adapted-harness/kb_index/build_index.py --n 20
Outputs: adapted-harness/kb_index/out/{sample,extractions,index}_<n>.json and report_<n>.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Literal, Optional

import anthropic
from pydantic import BaseModel
from rank_bm25 import BM25Okapi

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS_DIR = os.path.join(ROOT, "data/tau2/domains/banking_knowledge/documents")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
MODEL = "claude-opus-5-5"

# Seed: docs that name these debit-card / dispute tools (chosen by KB content, not by tasks).
SEED_TOOLS = [
    "file_debit_card_transaction_dispute_6281",
    "get_user_dispute_history_7291",
    "get_debit_dispute_status_7483",
    "get_bank_account_transactions_9173",
    "close_debit_card_4721",
    "order_debit_card_5739",
    "freeze_debit_card_3892",
    "unfreeze_debit_card_3893",
    "clear_debit_card_fraud_alert_4892",
]

# Dependencies found by hand while profiling baseline traces: used only to SCORE the index.
KNOWN_LINKS = [
    (
        "doc_bank_accounts_bank_accounts_(general)_031",
        "doc_bank_accounts_bank_accounts_(general)_032",
        "dispute filing (liability) ↔ provisional-credit guidelines",
    ),
    (
        "doc_bank_accounts_bank_accounts_(general)_039",
        "doc_bank_accounts_bank_accounts_(general)_031",
        "fraud escalation ↔ dispute filing (conflicting guidance)",
    ),
    (
        "doc_bank_accounts_bank_accounts_(general)_025",
        "TOOL:get_bank_account_transactions_9173",
        "card closure 'no pending transactions' ↔ the tool that shows pending transactions",
    ),
]

ENTITY_TYPES = Literal[
    "product",
    "tool",
    "rule",
    "condition",
    "fee_or_limit",
    "process",
    "regulation",
    "data_field",
    "role",
    "document_reference",
    "other",
]
PREDICATES = Literal[
    "requires",
    "prohibits",
    "permits",
    "applies_to",
    "uses_tool",
    "determines_value_of",
    "exception_to",
    "precedes",
    "defines",
    "limits",
    "references",
    "escalates_to",
]


class Entity(BaseModel):
    name: str
    type: ENTITY_TYPES
    canonical: str  # short normalised name, lowercase


class Relation(BaseModel):
    subject: str
    predicate: PREDICATES
    object: str
    condition: Optional[str]
    quote: str  # exact supporting text from the document


class Need(BaseModel):
    needs: str  # what this doc relies on but does not itself define
    kind: Literal["rule", "data", "tool", "definition", "procedure", "threshold"]
    why: str


class DocExtraction(BaseModel):
    summary: str
    entities: list[Entity]
    relations: list[Relation]
    needs: list[Need]
    provides: list[
        str
    ]  # rules, definitions, values, procedures or tools this doc establishes


class CanonGroup(BaseModel):
    canonical: str
    members: list[str]


class CanonGroups(BaseModel):
    groups: list[CanonGroup]  # only names that should be merged


class NeedMatch(BaseModel):
    need_id: str  # e.g. "N12"
    provide_id: str  # e.g. "P40"
    reason: str


class NeedMatches(BaseModel):
    matches: list[NeedMatch]


EXTRACT_PROMPT = """You are building a dependency index over a bank's internal knowledge base, so that \
a customer-service agent can see which documents must be read together before acting.

Extract from the document below:
- entities: banking-specific things it mentions (products, internal tools named like `name_1234`, \
rules, conditions, fees/limits/thresholds, processes, regulations, data fields, roles, references to \
other documents or guidelines). Give each a short lowercase `canonical` name that another document \
would also use for the same thing (e.g. "provisional credit", "regulation e", "pending transactions").
- relations: how the entities relate, each backed by an exact quote from the document.
- needs: what this document relies on but does NOT itself define or supply (a rule, threshold, \
data the agent must look up, a tool, a procedure or definition that must come from elsewhere).
- provides: the rules, definitions, values, procedures or tools this document itself establishes.
Be specific and faithful to the text; do not invent content.

<document id="{doc_id}">
# {title}

{content}
</document>"""

CANON_PROMPT = """Below are entity names extracted independently from several bank knowledge-base \
documents. Group the names that mean the same thing (e.g. "reg e", "regulation e liability rules" -> \
"regulation e"; "pending or processing transactions" -> "pending transactions"). Return ONLY groups \
with two or more members; names you do not group stay as they are. Keep distinct concepts distinct.

{names}"""

MATCH_PROMPT = """A bank knowledge base has been split into documents. For each document we extracted \
what it NEEDS from elsewhere (rules, data, tools, thresholds, procedures it relies on but does not \
define) and what it PROVIDES (rules, definitions, values, procedures, tools it establishes).

Match needs to provisions: return a pair (need_id, provide_id) when the provision, in another document, \
supplies what the need asks for. Only real matches; a need may match several provisions or none. Give a \
one-line reason.

NEEDS:
{needs}

PROVIDES:
{provides}"""


def load_docs() -> dict[str, dict]:
    docs = {}
    for f in sorted(os.listdir(DOCS_DIR)):
        if f.endswith(".json"):
            d = json.load(open(os.path.join(DOCS_DIR, f)))
            docs[d["id"]] = d
    return docs


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]{2,}", text.lower())


def select_sample(docs: dict, n: int) -> list[str]:
    seed = [i for i, d in docs.items() if any(t in d["content"] for t in SEED_TOOLS)]
    ids = list(docs)
    bm = BM25Okapi([tokens(docs[i]["title"] + " " + docs[i]["content"]) for i in ids])
    pool = Counter()
    for s in seed:
        scores = bm.get_scores(tokens(docs[s]["title"] + " " + docs[s]["content"]))
        for j in sorted(range(len(ids)), key=lambda k: -scores[k])[:10]:
            if ids[j] not in seed:
                pool[ids[j]] += scores[j]
    return (seed + [i for i, _ in pool.most_common()])[:n]


def bm25_edges(docs: dict, sample: list[str], k: int = 3) -> list[dict]:
    corpus = [tokens(docs[i]["title"] + " " + docs[i]["content"]) for i in sample]
    bm = BM25Okapi(corpus)
    edges = []
    for a, q in zip(sample, corpus):
        scores = bm.get_scores(q)
        ranked = sorted((s, b) for s, b in zip(scores, sample) if b != a)[::-1][:k]
        edges += [{"a": a, "b": b, "score": round(float(s), 2)} for s, b in ranked]
    return edges


def parse(client, prompt: str, schema, max_tokens: int = 16000):
    resp = client.messages.parse(
        model=MODEL,
        max_tokens=max_tokens,
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": prompt}],
        output_format=schema,
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"refusal: {resp.stop_details}")
    u = resp.usage
    return resp.parsed_output, (u.input_tokens, u.output_tokens)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument(
        "--scope",
        choices=["seed", "procedural", "all"],
        default="seed",
        help="seed: debit-card/dispute cluster of n docs; procedural: every internal, "
        "tool-naming or '(general)' doc (KB-only selection); all: the whole KB",
    )
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    docs = load_docs()
    if args.scope == "all":
        sample = sorted(docs)
        args.n = f"all{len(sample)}"
    elif args.scope == "procedural":
        sample = sorted(
            i
            for i, d in docs.items()
            if "internal" in d["title"].lower()
            or re.search(r"_\d{4}\b", d["content"])
            or "(general)" in i
        )
        args.n = f"proc{len(sample)}"
    else:
        sample = select_sample(docs, args.n)
    json.dump(sample, open(f"{OUT}/sample_{args.n}.json", "w"), indent=1)
    print(f"sample: {len(sample)} docs")

    client = anthropic.Anthropic()
    tok = [0, 0]

    def run(i):
        d = docs[i]
        for attempt in range(2):  # one retry: a truncated or invalid JSON reply is rare
            try:
                out, t = parse(
                    client,
                    EXTRACT_PROMPT.format(
                        doc_id=i, title=d["title"], content=d["content"]
                    ),
                    DocExtraction,
                )
                return i, out, t
            except Exception as e:
                err = e
        print(f"  FAILED {i}: {str(err)[:120]}")
        return i, None, (0, 0)

    ex_path = f"{OUT}/extractions_{args.n}.json"
    cached = {}
    for f in sorted(os.listdir(OUT)):  # same prompt across scopes: reuse any extraction
        if f.startswith("extractions_") and f.endswith(".json"):
            cached.update(json.load(open(os.path.join(OUT, f))))
    ex = {i: DocExtraction(**v) for i, v in cached.items() if i in sample}
    todo = [i for i in sample if i not in ex]
    save = lambda: json.dump(  # noqa: E731
        {i: e.model_dump() for i, e in ex.items()}, open(ex_path, "w"), indent=1
    )
    with ThreadPoolExecutor(8) as pool:
        for k, (i, out, t) in enumerate(pool.map(run, todo), 1):
            if out is None:
                continue
            ex[i] = out
            tok[0] += t[0]
            tok[1] += t[1]
            if k % 50 == 0:
                save()
                print(f"  {k}/{len(todo)} extracted; tokens in/out {tok[0]}/{tok[1]}")
    print(f"extractions: {len(ex)} ({len(ex) - len(todo)} reused)")
    save()

    names = sorted({e.canonical for x in ex.values() for e in x.entities})
    canon = {}
    if (
        len(names) <= 3000
    ):  # kb_related ignores shared-entity links; skip merging at scale
        groups, t = parse(
            client,
            CANON_PROMPT.format(names="\n".join(f"- {n}" for n in names)),
            CanonGroups,
        )
        tok[0] += t[0]
        tok[1] += t[1]
        canon = {
            m: g.canonical.lower().strip() for g in groups.groups for m in g.members
        }
    else:
        print(f"entity merging skipped ({len(names)} names)")
    C = lambda s: canon.get(s, s.lower().strip())  # noqa: E731

    need_list = [
        (f"N{k}", i, n)
        for k, (i, n) in enumerate((i, n) for i, x in ex.items() for n in x.needs)
    ]
    prov_list = [
        (f"P{k}", i, p)
        for k, (i, p) in enumerate((i, p) for i, x in ex.items() for p in x.provides)
    ]
    provides_txt = "\n".join(f"{pid} [{i}] {p}" for pid, i, p in prov_list)

    def match_chunk(chunk):
        return parse(
            client,
            MATCH_PROMPT.format(
                needs="\n".join(
                    f"{nid} [{i}] ({n.kind}) {n.needs}" for nid, i, n in chunk
                ),
                provides=provides_txt,
            ),
            NeedMatches,
        )

    matches = NeedMatches(matches=[])
    if len(prov_list) <= 1500:
        chunks = [need_list[k : k + 100] for k in range(0, len(need_list), 100)]
        jobs = [(c, provides_txt) for c in chunks]
    else:
        # Hybrid matching at scale: BM25 proposes 15 candidate provisions per need (from
        # other documents), the model confirms or rejects them in batches of 25 needs.
        ptoks = [tokens(docs[i]["title"] + " " + p) for _, i, p in prov_list]
        pbm = BM25Okapi(ptoks)
        jobs = []
        for k in range(0, len(need_list), 25):
            chunk = need_list[k : k + 25]
            cand = set()
            for _, i, n in chunk:
                sc = pbm.get_scores(tokens(n.needs + " " + n.why))
                ranked = [
                    j
                    for j in sorted(range(len(prov_list)), key=lambda j: -sc[j])
                    if prov_list[j][1] != i
                ]
                cand.update(ranked[:15])
            jobs.append(
                (
                    chunk,
                    "\n".join(
                        f"{prov_list[j][0]} [{prov_list[j][1]}] {prov_list[j][2]}"
                        for j in sorted(cand)
                    ),
                )
            )

    def match_job(job):
        chunk, ptxt = job
        try:
            return parse(
                client,
                MATCH_PROMPT.format(
                    needs="\n".join(
                        f"{nid} [{i}] ({n.kind}) {n.needs}" for nid, i, n in chunk
                    ),
                    provides=ptxt,
                ),
                NeedMatches,
            )
        except Exception as e:
            print(f"  match batch failed: {str(e)[:100]}")
            return NeedMatches(matches=[]), (0, 0)

    with ThreadPoolExecutor(6) as pool:
        for m, t in pool.map(match_job, jobs):
            matches.matches.extend(m.matches)
            tok[0] += t[0]
            tok[1] += t[1]
    print(
        f"matching: {len(jobs)} batch(es), {len(matches.matches)} matches; tokens in/out {tok[0]}/{tok[1]}"
    )
    need_by_id = {nid: (i, n) for nid, i, n in need_list}
    prov_by_id = {pid: (i, p) for pid, i, p in prov_list}

    # --- link documents -------------------------------------------------------------
    ent_docs, provides_docs, tool_docs = (
        defaultdict(set),
        defaultdict(set),
        defaultdict(set),
    )
    for i, x in ex.items():
        for e in x.entities:
            ent_docs[C(e.canonical)].add(i)
            if e.type == "tool" or re.search(r"_\d{4}\b", e.name):
                tool_docs[re.sub(r"[`()]", "", e.name).strip()].add(i)
        for p in x.provides:
            provides_docs[C(p)].add(i)
    generic = {c for c, ds in ent_docs.items() if len(ds) > len(sample) * 0.5}
    edges = defaultdict(
        lambda: {"needs_provides": [], "shared_tools": [], "shared_entities": []}
    )
    matched_needs = set()
    for m in matches.matches:
        if m.need_id not in need_by_id or m.provide_id not in prov_by_id:
            continue
        (i, nd), (j, p) = need_by_id[m.need_id], prov_by_id[m.provide_id]
        if i == j:
            continue
        matched_needs.add(m.need_id)
        a, b = sorted((i, j))
        edges[(a, b)]["needs_provides"].append(
            f"[{i[-12:]} needs] {nd.needs} ({nd.kind}) ← [{j[-12:]} provides] {p} | {m.reason}"
        )
    for tool, ds in tool_docs.items():
        for a in ds:
            for b in ds:
                if a < b:
                    edges[(a, b)]["shared_tools"].append(tool)
    for c, ds in ent_docs.items():
        if c in generic:
            continue
        for a in ds:
            for b in ds:
                if a < b:
                    edges[(a, b)]["shared_entities"].append(c)
    ent_edges = [{"a": a, "b": b, **v} for (a, b), v in edges.items()]

    bm = bm25_edges(docs, sample)
    index = {
        "sample": sample,
        "bm25_edges": bm,
        "entity_edges": ent_edges,
        "canonical_map": canon,
        "generic_entities": sorted(generic),
        "tokens": {"input": tok[0], "output": tok[1]},
    }
    json.dump(index, open(f"{OUT}/index_{args.n}.json", "w"), indent=1)

    # --- score against hand-found dependencies --------------------------------------
    def linked(a, b, method):
        if b.startswith("TOOL:"):
            t = b[5:]
            return a in tool_docs.get(t, set()) or any(
                t in r.object or t in r.subject
                for r in ex.get(
                    a,
                    DocExtraction(
                        summary="", entities=[], relations=[], needs=[], provides=[]
                    ),
                ).relations
            )
        pairs = {(e["a"], e["b"]) for e in (bm if method == "bm25" else ent_edges)}
        return (a, b) in pairs or (b, a) in pairs

    title = lambda i: docs[i]["title"] if i in docs else i  # noqa: E731
    L = [
        f"# KB interconnection index: {len(sample)}-doc experiment",
        "",
        f"Model `{MODEL}` (effort medium), tokens in/out {tok[0]}/{tok[1]}. Sample = docs naming the debit-card/dispute "
        "tools, filled with BM25 neighbours (KB-only selection).",
        "",
        "## Known dependencies (from trace profiling)",
        "",
        "| link | in sample | BM25 top-3 | entity index |",
        "|---|---|---|---|",
    ]
    for a, b, why in KNOWN_LINKS:
        ins = a in sample and (b.startswith("TOOL:") or b in sample)
        L.append(
            f"| {why} | {ins} | {linked(a, b, 'bm25') if ins and not b.startswith('TOOL:') else 'n/a'} | {linked(a, b, 'ent') if ins else 'n/a'} |"
        )
    L += [
        "",
        f"## Entity-index edges ({len(ent_edges)}; generic entities dropped: {sorted(generic)})",
        "",
    ]
    for e in sorted(
        ent_edges,
        key=lambda e: -(
            3 * len(e["needs_provides"])
            + 2 * len(e["shared_tools"])
            + len(e["shared_entities"])
        ),
    ):
        L.append(f"- **{title(e['a'])}** ↔ **{title(e['b'])}**")
        for np_ in e["needs_provides"][:3]:
            L.append(f"  - needs→provides: {np_}")
        if e["shared_tools"]:
            L.append(f"  - shared tools: {sorted(set(e['shared_tools']))}")
        if e["shared_entities"]:
            L.append(f"  - shared entities: {sorted(set(e['shared_entities']))[:8]}")
    L += ["", "## BM25 top-3 neighbours", ""]
    for e in bm:
        L.append(f"- {title(e['a'])} → {title(e['b'])} ({e['score']})")
    L += ["", "## Unresolved needs (no doc in the sample provides them)", ""]
    unresolved = [(i, n) for nid, i, n in need_list if nid not in matched_needs]
    L.insert(
        5,
        f"Needs: {len(need_list)}, matched to another doc: {len(matched_needs)}, unresolved: "
        f"{len(unresolved)}. Edges: {sum(1 for e in ent_edges if e['needs_provides'])} needs→provides, "
        f"{sum(1 for e in ent_edges if e['shared_tools'])} shared-tool, "
        f"{sum(1 for e in ent_edges if e['shared_entities'])} shared-entity.\n",
    )
    for i, n in unresolved:
        L.append(f"- {title(i)}: needs **{n.needs}** ({n.kind})")
    open(f"{OUT}/report_{args.n}.md", "w").write("\n".join(L))
    print(f"wrote {OUT}/report_{args.n}.md; tokens in/out {tok[0]}/{tok[1]}")


if __name__ == "__main__":
    main()
