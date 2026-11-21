#!/bin/sh
# Run a split with the adapted harness: the pinned baseline config (terminal_use shell retrieval)
# with --agent adapted_agent; the harness adds kb_related (connected-document index) on top.
# Retrieval ablation: HARNESS_RETRIEVAL=bm25_grep swaps the shell for KB_search + grep.
#   adapted-harness/run_adapted.sh smoke|dev|test <save-name> [extra tau2 run args]
# Components (default all on; see src/tau2/agent/adapted/config.py); ablate with e.g. HARNESS_INDEX=0:
#   HARNESS_GATE    C1 pre-action precheck gate
#   HARNESS_LEDGER  C2 task ledger + grounding note on customer turns
#   HARNESS_DERIVED C3 derived-argument rule citations + tool→doc hints at unlock
#   HARNESS_CONTRACTS  enforce KB-derived tool contracts (adapted-harness/kb_index/out/contracts.json)
#   HARNESS_CONFLICTS  cross-document consistency check in the precheck
#   HARNESS_INDEX      kb_related connected-document lookup
#   HARNESS_RULECARDS  curated cross-document rule resolutions (adapted-harness/kb_index/rule_cards.json)
#   HARNESS_GREP_CAP   grep hits shown in full (default 8)
set -e
if [ $# -lt 2 ]; then
  echo "usage: $0 smoke|dev|test <save-name> [extra tau2 run args]" >&2
  exit 1
fi
cd "$(dirname "$0")/.."
split="$1"; name="$2"; shift 2
ids=$(cat "adapted-harness/splits/$split.txt")
[ -f .env ] || { echo "missing .env with ANTHROPIC_API_KEY at the repo root" >&2; exit 1; }
set -a; . ./.env; set +a
retrieval="${HARNESS_RETRIEVAL:-terminal_use}"
echo "harness retrieval=$retrieval (component switches are logged by the agent factory)" >&2
# shellcheck disable=SC2086
exec uv run tau2 run --domain banking_knowledge --agent adapted_agent \
  --agent-llm claude-sonnet-5-5 --agent-llm-args '{}' \
  --user-llm claude-sonnet-5-5 --user-llm-args '{}' \
  --retrieval-config "$retrieval" --num-trials 1 --max-concurrency 4 \
  --task-ids $ids --save-to "$name" "$@"
