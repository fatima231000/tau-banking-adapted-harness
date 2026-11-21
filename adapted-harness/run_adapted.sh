#!/bin/sh
# Run a split with the adapted harness: the pinned baseline config (terminal_use shell retrieval)
# with --agent adapted_agent.
#   adapted-harness/run_adapted.sh smoke|dev|test <save-name> [extra tau2 run args]
#
# HARNESS_PRESET picks the harness (default: evolved). See src/tau2/agent/adapted/config.py.
#   evolved  baseline agent + prompt caching + the evolved candidate in
#            adapted-harness/evolve/out/best.json (prompt section, state line, self-check)
#   plain    baseline agent + prompt caching only
#   lean, enable, "" (v8 gates)   earlier versions, kept for comparison; see notes/REPORT.md
# HARNESS_CANDIDATE=<file>  run any candidate file on top of the plain preset
# HARNESS_RETRIEVAL=<config>  retrieval ablation (e.g. golden_retrieval); default terminal_use
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
export HARNESS_PRESET="${HARNESS_PRESET:-evolved}"   # evolved = baseline agent + adapted-harness/evolve/out/best.json
echo "harness preset=${HARNESS_PRESET:-none} retrieval=$retrieval" >&2
# shellcheck disable=SC2086
exec uv run tau2 run --domain banking_knowledge --agent adapted_agent \
  --agent-llm claude-sonnet-5-5 --agent-llm-args '{}' \
  --user-llm claude-sonnet-5-5 --user-llm-args '{}' \
  --retrieval-config "$retrieval" --num-trials 1 --max-concurrency 4 \
  --task-ids $ids --save-to "$name" "$@"
