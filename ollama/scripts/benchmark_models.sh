#!/usr/bin/env bash
set -euo pipefail

# Simple non-streaming benchmarks against Ollama /api/generate.
# Prints tokens/sec and durations for a set of models.

HOST="${OLLAMA_HOST:-localhost}"
PORT="${OLLAMA_PORT:-11434}"
ENDPOINT="http://${HOST}:${PORT}/api/generate"

PROMPT=${PROMPT:-"In one short paragraph, explain how to evaluate small local LLMs fairly across devices. Keep it concise."}

# Update this list to match the models you are benchmarking.
MODELS=("${@}")
if [[ ${#MODELS[@]} -eq 0 ]]; then
  MODELS=(
    "deepseek-r1:7b"
    "qwen3:8b-instruct"
    "qwen3-coder"
    "phi4-mini:3.8b"
  )
fi

echo "Benchmarking against ${ENDPOINT}"
printf "\n%-36s  %10s  %10s  %10s\n" "MODEL" "TOKENS" "SEC" "TOK/S"
printf "%-36s  %10s  %10s  %10s\n" "------------------------------------" "----------" "----------" "----------"

for m in "${MODELS[@]}"; do
  RESP=$(curl -sS -X POST "$ENDPOINT" \
    -H 'Content-Type: application/json' \
    -d @- <<JSON
{ "model": "$m", "prompt": ${PROMPT@Q}, "stream": false, "options": { "temperature": 0.2, "num_predict": 256, "num_ctx": 4096 } }
JSON
  ) || { echo "[!] Request failed for $m" >&2; continue; }

  # Extract eval_count (tokens) and eval_duration (ns) if present
  TOKENS=$(echo "$RESP" | jq -r '.eval_count // .eval_tokens // 0' 2>/dev/null || echo 0)
  DURATION_NS=$(echo "$RESP" | jq -r '.eval_duration // .metrics.eval_duration // 0' 2>/dev/null || echo 0)

  if [[ "$DURATION_NS" =~ ^[0-9]+$ ]] && [[ "$TOKENS" =~ ^[0-9]+$ ]] && [[ "$DURATION_NS" -gt 0 ]]; then
    SEC=$(awk -v ns="$DURATION_NS" 'BEGIN { printf "%.3f", ns/1000000000 }')
    TOKS=$(awk -v t="$TOKENS" 'BEGIN { printf "%d", t }')
    TPS=$(awk -v t="$TOKENS" -v s="$SEC" 'BEGIN { if (s>0) printf "%.1f", t/s; else print "0.0" }')
  else
    SEC="n/a"; TOKS="n/a"; TPS="n/a"
  fi

  printf "%-36s  %10s  %10s  %10s\n" "$m" "$TOKS" "$SEC" "$TPS"
done

echo "\nTip: adjust PROMPT env var for different workloads."
