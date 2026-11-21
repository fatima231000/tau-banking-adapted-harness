"""Harness configuration: every switch in one place, read once from the environment.

Defaults are the final configuration. Ablate a component with its env var set to 0, e.g.
``HARNESS_INDEX=0`` or ``HARNESS_RULECARDS=0``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
_KB_INDEX_DIR = os.path.join(_REPO, "adapted-harness", "kb_index")


def _flag(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() not in ("0", "false", "off", "no")


@dataclass(frozen=True)
class HarnessConfig:
    gate: bool = True  # C1: precheck gate on state-changing calls
    ledger: bool = True  # C2: task ledger + grounding note on customer turns
    derived: bool = True  # C3: provenance of derived argument values + tool→doc hints
    contracts: bool = True  # KB-derived tool contracts (prerequisite lookups)
    conflicts: bool = True  # cross-document consistency check in the precheck
    index: bool = True  # kb_related connected-document lookup
    kb_search: bool = True  # harness BM25 search with snippets (hybrid with the shell)
    # Hand-curated, DEV-informed knowledge: off by default so results measure general
    # mechanisms only. Kept for ablations.
    rule_cards: bool = False  # curated cross-document rule resolutions
    workflows: bool = True  # procedure steps of read docs become an ordered to-do list
    known_issues: bool = (
        True  # per-tool conflicts/ambiguities the precheck must address
    )
    arg_rules: bool = False  # hand-picked KB argument formats (ablation only)
    grep_cap: int = 8  # grep results shown in full; the rest as title + id (0 = no cap)
    max_internal_calls: int = 8  # LLM calls per orchestrator turn
    max_rejections: int = (
        3  # gate rejections per action before it is let through (logged)
    )
    contracts_path: str = field(
        default=os.path.join(_KB_INDEX_DIR, "out", "contracts.json")
    )
    index_path: str = field(
        default_factory=lambda: next(
            (
                p
                for p in (
                    os.path.join(_KB_INDEX_DIR, "out", f)
                    for f in ("index_proc90.json", "index_all698.json")
                )
                if os.path.exists(p)
            ),
            os.path.join(_KB_INDEX_DIR, "out", "index_all698.json"),
        )
    )
    rule_cards_path: str = field(default=os.path.join(_KB_INDEX_DIR, "rule_cards.json"))
    workflows_path: str = field(
        default=os.path.join(_KB_INDEX_DIR, "out", "workflows.json")
    )
    known_issues_path: str = field(
        default=os.path.join(_KB_INDEX_DIR, "out", "known_issues.json")
    )
    arg_rules_path: str = field(default=os.path.join(_KB_INDEX_DIR, "arg_rules.json"))

    @classmethod
    def from_env(cls) -> "HarnessConfig":
        d = cls()
        return cls(
            gate=_flag("HARNESS_GATE", d.gate),
            ledger=_flag("HARNESS_LEDGER", d.ledger),
            derived=_flag("HARNESS_DERIVED", d.derived),
            contracts=_flag("HARNESS_CONTRACTS", d.contracts),
            conflicts=_flag("HARNESS_CONFLICTS", d.conflicts),
            index=_flag("HARNESS_INDEX", d.index),
            kb_search=_flag("HARNESS_KBSEARCH", d.kb_search),
            rule_cards=_flag("HARNESS_RULECARDS", d.rule_cards),
            workflows=_flag("HARNESS_WORKFLOWS", d.workflows),
            known_issues=_flag("HARNESS_ISSUES", d.known_issues),
            arg_rules=_flag("HARNESS_ARGRULES", d.arg_rules),
            grep_cap=int(os.environ.get("HARNESS_GREP_CAP", d.grep_cap)),
            contracts_path=os.environ.get("HARNESS_CONTRACTS_PATH", d.contracts_path),
            index_path=os.environ.get("HARNESS_INDEX_PATH", d.index_path),
            rule_cards_path=os.environ.get("HARNESS_RULECARDS_PATH", d.rule_cards_path),
        )

    def summary(self) -> dict:
        return {
            k: getattr(self, k)
            for k in (
                "gate",
                "ledger",
                "derived",
                "contracts",
                "conflicts",
                "index",
                "kb_search",
                "rule_cards",
                "workflows",
                "known_issues",
                "arg_rules",
                "grep_cap",
            )
        }
