#!/bin/sh
# Run a split with the pinned baseline configuration.
#   adapted-harness/run.sh smoke|dev|test <save-name> [extra tau2 run args]
# Targeted rerun:  adapted-harness/run.sh dev rerun-015 --task-ids task_015
# (a later --task-ids replaces the split's list)
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
# shellcheck disable=SC2086
exec uv run tau2 run --domain banking_knowledge --agent llm_agent \
  --agent-llm claude-sonnet-5-5 --agent-llm-args '{}' \
  --user-llm claude-sonnet-5-5 --user-llm-args '{}' \
  --retrieval-config terminal_use --num-trials 1 --max-concurrency 4 \
  --task-ids $ids --save-to "$name" "$@"
