"""Compatibility shim: the adapted harness now lives in ``tau2.agent.adapted``.

Kept so the registry and the diagnostics scripts (index_usage.py) keep importing from here.
"""

from tau2.agent.adapted import AdaptedLLMAgent, HarnessConfig, create_adapted_agent
from tau2.agent.adapted.kb import kb as _kb
from tau2.agent.adapted.kb import md_norm as _md_norm


def _index():
    """Old-style view for diagnostics: doc id -> [{"doc": other}], strongest first."""
    from tau2.agent.adapted.kb import index

    out = {}
    for d, e in index(HarnessConfig.from_env().index_path).items():
        others = (
            [o for o, _, _ in e["needs"]]
            + [o for o, _, _ in e["needed_by"]]
            + list(e["tools"])
        )
        out[d] = [{"doc": o} for o in dict.fromkeys(others)]
    return out


__all__ = [
    "AdaptedLLMAgent",
    "HarnessConfig",
    "create_adapted_agent",
    "_index",
    "_kb",
    "_md_norm",
]
