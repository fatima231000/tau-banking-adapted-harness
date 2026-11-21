"""Agent-side view of the knowledge base, built from the KB files alone (never tasks or DB).

Holds: document titles and ids, which docs name each tool, the KB-derived tool contracts,
curated rule cards, and the connected-document index behind ``kb_related``.
"""

from __future__ import annotations

import inspect
import json
import os
import re
from functools import lru_cache
from typing import Any, Optional

from loguru import logger

from tau2.agent.adapted.config import HarnessConfig

# Tools whose output is KB text (terminal_use: shell; bm25_grep/alltools: KB_search, grep ...).
KB_TOOLS = {"shell", "KB_search", "grep", "KB_search_bm25", "KB_search_dense"}

_DOC_FILE = re.compile(r"doc_[A-Za-z0-9_().\-]+?(?=\.md)")
_ID_LINE = re.compile(r"^\s*ID:\s*(doc_\S+)", re.M)


def sanitize(name: str) -> str:
    """The sandbox's file-name form of a document id ('(' and ')' become '_')."""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().lower().strip("\"'`*")


def md_norm(s: str) -> str:
    """Normalise Markdown so quotes match whether copied from a table, list or heading."""
    s = re.sub(r"[*`]+", "", str(s))
    s = re.sub(r"[|#>]+", " ", s)
    s = re.sub(r"^\s*[-•]\s+", " ", s, flags=re.M)
    s = re.sub(r"\s+([:;,.])", r"\1", s)
    return re.sub(r"\s+", " ", s).strip().lower().strip("\"'.:;- ")


def value_forms(v: Any) -> set[str]:
    """String forms a scalar argument value may take in tool or KB output."""
    if isinstance(v, bool) or v is None:
        return set()
    if isinstance(v, (int, float)):
        f = float(v)
        forms = {f"{f}", f"{f:.2f}", f"{f:,.2f}"}
        if f.is_integer():
            forms |= {str(int(f)), f"{int(f):,}"}
        return forms
    s = str(v).strip()
    return {s} if len(s) >= 4 else set()


class KBView:
    def __init__(self):
        from tau2.domains.banking_knowledge import tools as T
        from tau2.domains.banking_knowledge.utils import KNOWLEDGE_DOCUMENTS_DIR

        self.docs: dict[str, dict] = {}
        for f in sorted(os.listdir(KNOWLEDGE_DOCUMENTS_DIR)):
            if f.endswith(".json"):
                d = json.load(open(os.path.join(KNOWLEDGE_DOCUMENTS_DIR, f)))
                self.docs[d["id"]] = d
        self.sanitized = {sanitize(i): i for i in self.docs}
        self.title_line = {f"# {d['title']}": i for i, d in self.docs.items()}
        members = list(inspect.getmembers(T.KnowledgeTools, inspect.isfunction))
        self.write_tools = {
            n
            for n, f in members
            if getattr(f, "__discoverable__", False)
            and str(getattr(f, "__tool_type__", "")).endswith("WRITE")
        }
        disc = {n: f for n, f in members if getattr(f, "__discoverable__", False)}
        disc.update(
            {
                n: f
                for n, f in inspect.getmembers(T.KnowledgeUserTools, inspect.isfunction)
                if getattr(f, "__discoverable__", False)
            }
        )
        self.tool_docs = {
            n: sorted(i for i, d in self.docs.items() if n in d["content"])
            for n in disc
        }
        self.tool_refs = {}
        for n, f in disc.items():
            doc = inspect.getdoc(f) or ""
            self.tool_refs[n] = sorted(
                i
                for i, d in self.docs.items()
                if len(d["title"]) >= 18 and d["title"].lower() in doc.lower()
            ) + sorted(self._guideline_refs(doc))

    def _guideline_refs(self, text: str) -> set[str]:
        out = set()
        for m in re.finditer(
            r"((?:[A-Z][\w\-]*\s){1,6}(?:Guidelines|Policy|Procedures?|Rules|Requirements))",
            text,
        ):
            p = set(re.findall(r"[a-z0-9]+", m.group(1).lower()))
            for i, d in self.docs.items():
                t = set(re.findall(r"[a-z0-9]+", d["title"].lower()))
                if p and len(p & t) / len(p | t) >= 0.6:
                    out.add(i)
        return out

    def resolve(self, token: str) -> Optional[str]:
        token = str(token).strip().removesuffix(".md")
        return token if token in self.docs else self.sanitized.get(token)

    def docs_seen(self, tool: str, command: str, output: str) -> set[str]:
        """Documents whose content the agent saw in one KB tool result."""
        found = set()
        if tool == "shell" and re.search(
            r"\b(cat|head|tail|sed|less|awk|python3?)\b", command
        ):
            found |= {i for t in _DOC_FILE.findall(command) if (i := self.resolve(t))}
        found |= {
            i for t in _ID_LINE.findall(output) if (i := self.resolve(t))
        }  # KB_search / grep
        found |= {
            i for line, i in self.title_line.items() if line in output
        }  # cat output
        return found


@lru_cache(maxsize=1)
def kb() -> KBView:
    return KBView()


# ---- tool contracts and rule cards ------------------------------------------------------


@lru_cache(maxsize=4)
def contracts(path: str) -> dict:
    try:
        return json.load(open(path))["contracts"]
    except Exception as e:
        logger.warning(f"adapted harness: no tool contracts loaded ({e})")
        return {}


@lru_cache(maxsize=4)
def _cards(path: str) -> tuple:
    try:
        return tuple(json.load(open(path))["cards"])
    except Exception as e:
        logger.warning(f"adapted harness: no rule cards loaded ({e})")
        return ()


def rule_cards(cfg: HarnessConfig, tool: str) -> list[dict]:
    return (
        [c for c in _cards(cfg.rule_cards_path) if c["applies_to_tool"] == tool]
        if cfg.rule_cards
        else []
    )


def cards_text(cfg: HarnessConfig, tool: str) -> str:
    out = []
    for c in rule_cards(cfg, tool):
        src = "; ".join(f'{s["doc_id"]}: "{s["quote"]}"' for s in c["sources"])
        out.append(
            f"Rule for `{c['argument']}` (documents disagree; resolved): {c['rule']} "
            f"Why: {c['conflict']} Sources: {src}"
        )
    return "\n".join(out)


def contract_text(cfg: HarnessConfig, tool: str) -> str:
    c = contracts(cfg.contracts_path).get(tool) if cfg.contracts else None
    if not c:
        return cards_text(cfg, tool)
    carded = {k["argument"] for k in rule_cards(cfg, tool)}
    lines = [f"Registered contract for {tool} (from the KB):"]
    lines += [
        f"- call first: {p['tool']} ({p['purpose']}) [{p['doc_id']}]"
        for p in c.get("prerequisite_calls", [])
    ]
    for p in c.get("preconditions", []):
        v = f"; verify with {p['verifying_tool']}" if p.get("verifying_tool") else ""
        lines.append(f"- condition: {p['condition']}{v} [{p['doc_id']}]")
    lines += [
        f"- {p['relation'].replace('_', ' ')}: {p['step']}"
        for p in c.get("ordering", [])
    ]
    lines += [
        f"- {p['argument']} is set by rule: {p['rule']} [{p['doc_id']}]"
        for p in c.get("derived_arguments", [])
        if p["argument"] not in carded
    ]
    if carded:
        lines.append(cards_text(cfg, tool))
    return "\n".join(lines)


# ---- connected-document index (kb_related) ---------------------------------------------

_NP = re.compile(
    r"^\[(?P<tag>[^\]]+) needs\] (?P<need>.*?) ← \[(?P<ptag>[^\]]+) provides\] (?P<prov>.*?)(?: \| .*)?$"
)


@lru_cache(maxsize=4)
def index(path: str) -> dict:
    """doc id -> {"needs": [(other, need, provision)], "needed_by": [...], "tools": {other: [tools]}}."""
    out: dict[str, dict] = {}
    try:
        idx = json.load(open(path))
    except Exception as e:
        logger.warning(f"adapted harness: no KB index loaded ({e})")
        return out
    blank = lambda: {"needs": [], "needed_by": [], "tools": {}}  # noqa: E731
    for e in idx.get("entity_edges", []):
        a, b = e["a"], e["b"]
        for s in e["needs_provides"]:
            m = _NP.match(s)
            if not m:
                continue
            needer, provider = (
                (a, b) if a.endswith(m["tag"]) or not b.endswith(m["tag"]) else (b, a)
            )
            out.setdefault(needer, blank())["needs"].append(
                (provider, m["need"], m["prov"])
            )
            out.setdefault(provider, blank())["needed_by"].append(
                (needer, m["need"], m["prov"])
            )
        if e["shared_tools"]:
            for me, other in ((a, b), (b, a)):
                out.setdefault(me, blank())["tools"][other] = sorted(
                    set(e["shared_tools"])
                )
    return out


def related_text(
    cfg: HarnessConfig, doc_id: str, limit: int = 5
) -> tuple[str, list[str]]:
    """Refined kb_related answer: what this doc needs and who provides it first, then docs that
    depend on it, then shared-tool docs only if nothing stronger exists. Returns (text, doc ids)."""
    v = kb()
    did = v.resolve(doc_id) or doc_id
    entry = index(cfg.index_path).get(did)
    if not entry:
        return f"No indexed dependencies for {doc_id}.", []
    title = lambda i: v.docs.get(i, {}).get("title", "")  # noqa: E731
    lines, shown = [f"Documents connected to {did} ({title(did)}):"], []

    def group(pairs):
        g: dict[str, list] = {}
        for other, need, prov in pairs:
            g.setdefault(other, []).append((need, prov))
        return sorted(g.items(), key=lambda kv: -len(kv[1]))

    for other, items in group(entry["needs"]):
        if len(shown) >= limit:
            break
        shown.append(other)
        lines.append(f"- {other} ({title(other)}) PROVIDES what this document needs:")
        lines += [f"    · needs {n} ← {p}" for n, p in items[:2]]
    for other, items in group(entry["needed_by"]):
        if len(shown) >= limit or other in shown:
            continue
        shown.append(other)
        lines.append(f"- {other} ({title(other)}) RELIES ON this document for:")
        lines += [f"    · {n}" for n, _ in items[:2]]
    if not shown:
        for other, tools in list(entry["tools"].items())[:limit]:
            shown.append(other)
            lines.append(
                f"- {other} ({title(other)}) uses the same tools: {', '.join(tools)}"
            )
    return "\n".join(lines), shown


# ---- v6: procedure workflows, known issues, KB-stated argument rules --------------------


@lru_cache(maxsize=4)
def workflows(path: str) -> dict:
    """doc id -> {"scenario", "steps": [{order, step, tool, condition, quote}]}."""
    try:
        return json.load(open(path))["workflows"]
    except Exception as e:
        logger.warning(f"adapted harness: no workflows loaded ({e})")
        return {}


@lru_cache(maxsize=4)
def known_issues(path: str) -> dict:
    """tool -> {"docs", "issues": [{id, topic, kind, description, doc_quotes, resolved_by_kb, resolution}]}."""
    try:
        return json.load(open(path))["tools"]
    except Exception as e:
        logger.warning(f"adapted harness: no known issues loaded ({e})")
        return {}


@lru_cache(maxsize=4)
def arg_rules(path: str) -> tuple:
    try:
        return tuple(json.load(open(path))["rules"])
    except Exception as e:
        logger.warning(f"adapted harness: no argument rules loaded ({e})")
        return ()


def issues_for(cfg: HarnessConfig, tool: str) -> list[dict]:
    return (
        known_issues(cfg.known_issues_path).get(tool, {}).get("issues", [])
        if cfg.known_issues
        else []
    )


def issues_text(cfg: HarnessConfig, tool: str, max_chars: int = 2500) -> str:
    items = issues_for(cfg, tool)
    if not items:
        return ""
    lines = [f"Known issues for {tool} (address each by id in issue_checks):"]
    for i in items:
        res = (
            f" KB resolves it: {i['resolution']}"
            if i.get("resolved_by_kb") and i.get("resolution")
            else " The KB leaves it open."
        )
        lines.append(f"- {i['id']} [{i['kind']}] {i['topic']}: {i['description']}{res}")
    return "\n".join(lines)[:max_chars]


# ---- harness-side BM25 search (hybrid retrieval on top of the terminal_use shell) -------

_TOK = re.compile(r"[a-z0-9_]{2,}")


def _tokens(text: str) -> list[str]:
    return _TOK.findall(text.lower())


@lru_cache(maxsize=1)
def _bm25():
    from rank_bm25 import BM25Okapi

    ids = sorted(kb().docs)
    corpus = [
        _tokens(kb().docs[i]["title"] + " " + kb().docs[i]["content"]) for i in ids
    ]
    return ids, BM25Okapi(corpus)


def _snippet(text: str, terms: set[str], width: int = 420) -> str:
    """The window of the document with the most query terms, so the hit can be judged before reading."""
    words = text.split()
    if len(words) <= width // 6:
        return " ".join(words)
    best, best_at, step = -1, 0, 25
    for at in range(0, max(1, len(words) - 60), step):
        window = words[at : at + 70]
        score = sum(1 for w in window if w.lower().strip(".,:;()*`|") in terms)
        if score > best:
            best, best_at = score, at
    out = " ".join(words[best_at : best_at + 70])
    return ("… " if best_at else "") + out + " …"


def search(query: str, k: int = 8) -> list[tuple[str, float, str]]:
    """BM25 over all KB documents: [(doc_id, score, snippet)]."""
    ids, bm = _bm25()
    q = _tokens(query)
    if not q:
        return []
    scores = bm.get_scores(q)
    top = sorted(range(len(ids)), key=lambda j: -scores[j])[:k]
    terms = set(q)
    return [
        (ids[j], float(scores[j]), _snippet(kb().docs[ids[j]]["content"], terms))
        for j in top
        if scores[j] > 0
    ]


def search_text(query: str, k: int = 8) -> tuple[str, list[str]]:
    hits = search(query, k)
    if not hits:
        return f"No documents match: {query}", []
    lines = [f"Top {len(hits)} documents for: {query}"]
    for n, (d, s, snip) in enumerate(hits, 1):
        lines.append(
            f"{n}. {kb().docs[d]['title']}\n   ID: {d}  (file: {sanitize(d)}.md, score {s:.1f})\n   {snip}"
        )
    lines.append(
        "Read a document in full with: cat <file>. Quote rules from the full text."
    )
    return "\n".join(lines), [d for d, _, _ in hits]


# ---- skill cards: compiled procedures, loaded before deciding ---------------------------


@lru_cache(maxsize=4)
def skills(path: str) -> dict:
    try:
        return json.load(open(path))["skills"]
    except Exception as e:
        logger.warning(f"adapted harness: no skill cards loaded ({e})")
        return {}


@lru_cache(maxsize=4)
def _skill_bm25(path: str):
    from rank_bm25 import BM25Okapi

    sk = skills(path)
    ids = sorted(sk)
    return ids, (BM25Okapi([_tokens(sk[i]["text"]) for i in ids]) if ids else None)


def skill_search_text(
    cfg: HarnessConfig, query: str, k: int = 3
) -> tuple[str, list[str]]:
    """Find cards by describing the situation. Returns titles only (progressive disclosure)."""
    ids, bm = _skill_bm25(cfg.skills_path)
    q = _tokens(query)
    if not bm or not q:
        return "No skill cards available.", []
    scores = bm.get_scores(q)
    top = [
        ids[j]
        for j in sorted(range(len(ids)), key=lambda j: -scores[j])[:k]
        if scores[j] > 0
    ]
    if not top:
        return f"No skill card matches: {query}. Search the knowledge base instead.", []
    sk = skills(cfg.skills_path)
    lines = [f"Skill cards for: {query}"]
    for i in top:
        scen = "; ".join(sk[i]["scenarios"][:3]) or sk[i]["purpose"]
        lines.append(f"- {i}: {sk[i]['purpose']} (procedures: {scen})")
    lines.append(
        "Load the one that fits with load_skill(skill_id). If none fits, search the knowledge base."
    )
    return "\n".join(lines), top


def skill_text(cfg: HarnessConfig, skill_id: str) -> tuple[str, str]:
    """A card's text and its freshness: 'fresh', 'stale' (a source doc changed) or 'missing'."""
    import hashlib

    sk = skills(cfg.skills_path).get(str(skill_id).strip())
    if not sk:
        return (
            f"No skill card named {skill_id}. Use skill_search to find one.",
            "missing",
        )
    changed = [
        d
        for d, h in sk["sources"].items()
        if d not in kb().docs
        or hashlib.sha256(kb().docs[d]["content"].encode()).hexdigest()[:16] != h
    ]
    if changed:
        return (
            f"SKILL {skill_id} is STALE: its source document(s) changed since the card was compiled "
            f"({[sanitize(d) + '.md' for d in changed]}). Do not rely on the card: read those documents."
        ), "stale"
    return sk["text"], "fresh"
