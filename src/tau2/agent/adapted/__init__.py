"""Adapted harness for τ-Banking (banking_knowledge).

Modules:
  config         HarnessConfig: every switch, read once from HARNESS_* env vars
  prompts        protocol, cross-document reasoning and index sections; system-prompt builder
  virtual_tools  precheck / update_ledger / kb_related schemas (answered inside the agent)
  kb             agent-side KB view, tool contracts, rule cards, connected-document index
  context        context/input builder: annotations, grep cap, what the agent has seen
  gate           pre-action gate: gated calls and precheck assertions
  agent          AdaptedLLMAgent and the create_adapted_agent factory
"""

from tau2.agent.adapted.agent import AdaptedLLMAgent, create_adapted_agent
from tau2.agent.adapted.config import HarnessConfig

__all__ = ["AdaptedLLMAgent", "HarnessConfig", "create_adapted_agent"]
