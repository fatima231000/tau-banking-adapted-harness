"""Harness configuration: every switch in one place, read once from the environment.

Defaults are the final configuration. Ablate a component with its env var set to 0, e.g.
``HARNESS_INDEX=0`` or ``HARNESS_RULECARDS=0``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, replace

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
_KB_INDEX_DIR = os.path.join(_REPO, "adapted-harness", "kb_index")
_EVOLVE_DIR = os.path.join(_REPO, "adapted-harness", "evolve")


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
    decision_gate: bool = True  # bounce text that states a decision without a record
    decisions: bool = True  # decision_record, request conservation, free-text check
    # Off by default: on replay of 57 v8 decision records it upheld 91%, rejected 2 in passing
    # tasks and missed the decisive errors, so as a blocking gate it adds regressions, not gains.
    checker: bool = False  # independent model reviews each decision record (ablation)
    early_checklist: bool = True  # show contract + known issues at unlock time
    mix_virtual: bool = True  # harness tools may share a turn with real calls
    cache: bool = True  # prompt caching on the agent's model calls
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
    # Skill cards: compiled procedures with conflict rulings, loaded before deciding.
    skills: bool = False
    lean_gate: bool = False  # form-free check: required lookups before a write; request count before a transfer
    skills_path: str = field(default=os.path.join(_KB_INDEX_DIR, "out", "skills.json"))

    # Capability-enabling harness: no gates, nothing compiled from the KB.
    enable: bool = (
        False  # working-method instructions + one state line on customer turns
    )
    replay_thinking: bool = False  # send the model's own thinking blocks back each turn
    # Evolved candidate (adapted-harness/evolve): a JSON file with up to three elements, each
    # optional: "system" (a prompt section), "note" (a state line on customer turns, {n} = number
    # of human-agent requests), "review" (a self-check the agent runs once on a reply before it is
    # sent). No gates, no extra tools, nothing compiled from the knowledge base.
    candidate_path: str = ""

    def candidate(self) -> dict:
        if not self.candidate_path:
            return {}
        with open(self.candidate_path) as f:
            return json.load(f)

    @classmethod
    def preset(cls, name: str) -> "HarnessConfig":
        """Named configurations. "lean": cards + lean check + caching, every form-based gate off."""
        if name == "lean":
            return cls(
                gate=False,
                ledger=False,
                derived=False,
                contracts=False,
                conflicts=False,
                index=False,
                kb_search=False,
                decision_gate=False,
                decisions=False,
                early_checklist=False,
                workflows=False,
                known_issues=False,
                checker=False,
                skills=True,
                lean_gate=True,
            )
        if (
            name == "plain"
        ):  # the baseline agent plus prompt caching, nothing else (for oracle runs)
            return cls(
                gate=False,
                ledger=False,
                derived=False,
                contracts=False,
                conflicts=False,
                index=False,
                kb_search=False,
                decision_gate=False,
                decisions=False,
                early_checklist=False,
                workflows=False,
                known_issues=False,
                checker=False,
                skills=False,
                lean_gate=False,
                mix_virtual=False,
            )
        if (
            name == "evolved"
        ):  # the baseline agent + caching + the current best candidate
            return replace(
                cls.preset("plain"),
                candidate_path=os.path.join(_EVOLVE_DIR, "out", "best.json"),
            )
        if name == "enable":
            return cls(
                gate=False,
                ledger=False,
                derived=False,
                contracts=False,
                conflicts=False,
                index=False,
                kb_search=True,
                decision_gate=False,
                decisions=False,
                early_checklist=False,
                workflows=False,
                known_issues=False,
                checker=False,
                skills=False,
                lean_gate=False,
                enable=True,
                replay_thinking=True,
            )
        return cls()

    @classmethod
    def from_env(cls) -> "HarnessConfig":
        d = cls.preset(os.environ.get("HARNESS_PRESET", "").strip().lower())
        return cls(
            gate=_flag("HARNESS_GATE", d.gate),
            ledger=_flag("HARNESS_LEDGER", d.ledger),
            derived=_flag("HARNESS_DERIVED", d.derived),
            contracts=_flag("HARNESS_CONTRACTS", d.contracts),
            conflicts=_flag("HARNESS_CONFLICTS", d.conflicts),
            index=_flag("HARNESS_INDEX", d.index),
            kb_search=_flag("HARNESS_KBSEARCH", d.kb_search),
            decision_gate=_flag("HARNESS_DECISION", d.decision_gate),
            decisions=_flag("HARNESS_DECISIONS", d.decisions),
            checker=_flag("HARNESS_CHECKER", d.checker),
            early_checklist=_flag("HARNESS_EARLY", d.early_checklist),
            mix_virtual=_flag("HARNESS_MIX", d.mix_virtual),
            cache=_flag("HARNESS_CACHE", d.cache),
            rule_cards=_flag("HARNESS_RULECARDS", d.rule_cards),
            workflows=_flag("HARNESS_WORKFLOWS", d.workflows),
            known_issues=_flag("HARNESS_ISSUES", d.known_issues),
            arg_rules=_flag("HARNESS_ARGRULES", d.arg_rules),
            grep_cap=int(os.environ.get("HARNESS_GREP_CAP", d.grep_cap)),
            contracts_path=os.environ.get("HARNESS_CONTRACTS_PATH", d.contracts_path),
            index_path=os.environ.get("HARNESS_INDEX_PATH", d.index_path),
            rule_cards_path=os.environ.get("HARNESS_RULECARDS_PATH", d.rule_cards_path),
            skills=_flag("HARNESS_SKILLS", d.skills),
            enable=_flag("HARNESS_ENABLE", d.enable),
            candidate_path=os.environ.get("HARNESS_CANDIDATE", d.candidate_path),
            replay_thinking=_flag("HARNESS_REPLAY_THINKING", d.replay_thinking),
            lean_gate=_flag("HARNESS_LEANGATE", d.lean_gate),
            skills_path=os.environ.get("HARNESS_SKILLS_PATH", d.skills_path),
        )

    def summary(self) -> dict:
        return {
            k: getattr(self, k)
            for k in (
                "enable",
                "candidate_path",
                "replay_thinking",
                "skills",
                "lean_gate",
                "gate",
                "ledger",
                "derived",
                "contracts",
                "conflicts",
                "index",
                "kb_search",
                "decision_gate",
                "decisions",
                "checker",
                "early_checklist",
                "mix_virtual",
                "cache",
                "rule_cards",
                "workflows",
                "known_issues",
                "arg_rules",
                "grep_cap",
            )
        }
