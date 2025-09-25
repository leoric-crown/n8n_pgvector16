#!/usr/bin/env bash
set -euo pipefail

# Single-request benchmarks against Ollama /api/generate (non-streaming).
# Prints tokens/sec and timing breakdown for a set of models.
# Middle-ground scope: simple flags, core metrics, optional CSV logging.

HAVE_JQ=0
HAVE_PY=0
PY_BIN=""

init_json_helpers() {
  # curl is required
  if ! command -v curl >/dev/null 2>&1; then
    echo "[-] curl is required. Please install curl and retry." >&2
    exit 1
  fi
  if command -v jq >/dev/null 2>&1; then
    HAVE_JQ=1
  fi
  if command -v python3 >/dev/null 2>&1; then
    HAVE_PY=1; PY_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    HAVE_PY=1; PY_BIN="python"
  fi

  if [[ $HAVE_JQ -eq 0 && $HAVE_PY -eq 0 ]]; then
    echo "[-] Neither jq nor Python was found. One of them is required." >&2
    echo "    Install jq:"
    echo "      macOS (Homebrew):  brew install jq"
    echo "      Debian/Ubuntu:     sudo apt-get update && sudo apt-get install -y jq"
    echo "      RHEL/CentOS/Fedora: sudo dnf install -y jq    (or: sudo yum install -y jq)"
    echo "      Arch:               sudo pacman -S jq"
    echo "      openSUSE:           sudo zypper install jq"
    echo "      Nix:                nix-env -iA nixpkgs.jq"
    echo "    OR install Python 3 to enable the fallback JSON parser."
    exit 1
  fi
}

# JSON helpers (prefer jq, fallback to Python)
json_stringify_stdin() {
  if [[ $HAVE_JQ -eq 1 ]]; then
    jq -Rs .
  else
    "$PY_BIN" -c 'import sys,json; print(json.dumps(sys.stdin.read()))'
  fi
}

json_get_num() {
  # Usage: json_get_num JSON DEFAULT KEY [KEY ...]
  local json="$1"; shift
  local def="$1"; shift
  if [[ $HAVE_JQ -eq 1 ]]; then
    local filter=""
    for k in "$@"; do
      if [[ -z "$filter" ]]; then filter=".$k"; else filter="$filter // .$k"; fi
    done
    echo "$json" | jq -r "${filter} // ${def}"
  else
    "$PY_BIN" - "$def" "$@" <<'PY' <<<"$json"
import sys, json
data = json.load(sys.stdin)
default = sys.argv[1]
keys = sys.argv[2:]
def get_path(d, path):
    cur = d
    for p in path.split('.'):
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur
for k in keys:
    v = get_path(data, k)
    if isinstance(v, (int, float)):
        print(v)
        sys.exit(0)
print(default)
PY
  fi
}

json_get_str() {
  # Usage: json_get_str JSON KEY [KEY ...]  (prints first non-empty string)
  local json="$1"; shift
  if [[ $HAVE_JQ -eq 1 ]]; then
    local filter=""
    for k in "$@"; do
      [[ -n "$filter" ]] && filter="$filter // ";
      filter="${filter}(.${k} // empty)"
    done
    echo "$json" | jq -r "${filter} // empty"
  else
    "$PY_BIN" - "$@" <<'PY' <<<"$json"
import sys, json
data = json.load(sys.stdin)
keys = sys.argv[1:]
def get_path(d, path):
    cur = d
    for p in path.split('.'):
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur
for k in keys:
    v = get_path(data, k)
    if isinstance(v, str) and v:
        print(v)
        sys.exit(0)
print("")
PY
  fi
}

# Defaults (overridable via flags or env)
HOST="${OLLAMA_HOST:-localhost}"
PORT="${OLLAMA_PORT:-11434}"
ENDPOINT="http://${HOST}:${PORT}/api/generate"

# Resolve script directory for default prompt path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PROMPT_MD="${SCRIPT_DIR}/benchmark_models.md"

# PROMPT can be set via env or flags; leave empty to allow default file fallback
PROMPT=${PROMPT:-}
TEMPERATURE=${TEMPERATURE:-0.2}
NUM_PREDICT=${NUM_PREDICT:-256}
NUM_CTX=${NUM_CTX:-4096}
SEED=${SEED:-}
DEBUG=0

LABEL=""
CSV_OUT=""
COLD=0

MODELS_INPUT=()

print_usage() {
  cat <<USAGE
Usage: $(basename "$0") [options] [model ...]

Options:
  -m, --models LIST       Comma-separated model list (alternative to positional args)
  -p, --prompt TEXT       Prompt text (overrides PROMPT env)
      --prompt-file FILE  Read prompt from file (default: benchmark_models.md here; if missing, uses embedded prompt)
      --num-predict N     Tokens to generate (default: ${NUM_PREDICT})
      --num-ctx N         Context length (default: ${NUM_CTX})
      --temperature F     Temperature (default: ${TEMPERATURE})
      --seed N            Seed for determinism
      --host HOST         Ollama host (default: ${HOST})
      --port PORT         Ollama port (default: ${PORT})
      --label NAME        Tag results (e.g., baseline, optimized)
      --csv FILE          Append results to CSV file
      --cold              Encourage cold runs (keep_alive: "0s")
      --debug             Print raw API errors/responses for troubleshooting
  -h, --help              Show this help

Examples:
  $0 deepseek-r1:7b qwen3:8b-instruct
  $0 --models "llama3.2:3b-instruct,phi4-mini:3.8b" --num-ctx 8192 --label optimized --csv results.csv
USAGE
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -m|--models)
        IFS=',' read -r -a MODELS_INPUT <<<"$2"; shift 2 ;;
      -p|--prompt)
        PROMPT="$2"; shift 2 ;;
      --prompt-file)
        PROMPT="$(cat "$2")"; shift 2 ;;
      --num-predict)
        NUM_PREDICT="$2"; shift 2 ;;
      --num-ctx)
        NUM_CTX="$2"; shift 2 ;;
      --temperature)
        TEMPERATURE="$2"; shift 2 ;;
      --seed)
        SEED="$2"; shift 2 ;;
      --host)
        HOST="$2"; shift 2 ;;
      --port)
        PORT="$2"; shift 2 ;;
      --label)
        LABEL="$2"; shift 2 ;;
      --csv)
        CSV_OUT="$2"; shift 2 ;;
      --cold)
        COLD=1; shift 1 ;;
      --debug)
        DEBUG=1; shift 1 ;;
      -h|--help)
        print_usage; exit 0 ;;
      --) shift; break ;;
      -*) echo "[-] Unknown option: $1" >&2; print_usage; exit 2 ;;
      *) MODELS_INPUT+=("$1"); shift ;;
    esac
  done
}

is_model_preloaded() {
  local model="$1"
  local ps_json
  ps_json=$(curl -sS "http://${HOST}:${PORT}/api/ps" 2>/dev/null || true)
  local names
  if [[ -n "$ps_json" ]]; then
    if [[ $HAVE_JQ -eq 1 ]]; then
      names=$(echo "$ps_json" | jq -r '.models[].name // empty')
    else
      names=$(echo "$ps_json" | "$PY_BIN" - <<'PY'
import sys, json
data = json.load(sys.stdin)
for m in data.get('models', []) or []:
    name = m.get('name')
    if name:
        print(name)
PY
)
    fi
  fi
  if echo "${names:-}" | grep -Fxq "$model"; then
    echo "yes"; return 0
  fi
  echo "no"
}

format_ns() {
  awk -v ns="$1" 'BEGIN { if (ns+0>0) printf "%.3f", ns/1000000000; else printf "n/a" }'
}

format_tps() {
  awk -v t="$1" -v s="$2" 'BEGIN { if (s+0>0) printf "%.1f", t/s; else printf "n/a" }'
}

append_csv_header_if_needed() {
  local f="$1"
  [[ -z "$f" ]] && return 0
  if [[ ! -f "$f" ]]; then
    echo "timestamp,label,model,preloaded,tokens,load_s,eval_s,tok_s,total_s,prompt_eval_s" >>"$f"
  fi
}

model_available_locally() {
  local model="$1"
  local src="${TAGS_JSON:-}"
  if [[ -z "$src" ]]; then
    src=$(curl -sS "http://${HOST}:${PORT}/api/tags" 2>/dev/null || true)
  fi
  local names
  if [[ -n "$src" ]]; then
    if [[ $HAVE_JQ -eq 1 ]]; then
      names=$(echo "$src" | jq -r '.models[].name // empty')
    else
      names=$(echo "$src" | "$PY_BIN" - <<'PY'
import sys, json
data = json.load(sys.stdin)
for m in data.get('models', []) or []:
    name = m.get('name')
    if name:
        print(name)
PY
)
    fi
  fi
  if echo "${names:-}" | grep -Fxq "$model"; then
    echo "yes"; return 0
  fi
  echo "no"
}

ensure_tags_json() {
  if [[ -z "${TAGS_JSON:-}" ]]; then
    TAGS_JSON=$(curl -sS "http://${HOST}:${PORT}/api/tags" 2>/dev/null || true)
  fi
}

disk_gb_for_model() {
  local model="$1"
  ensure_tags_json
  local bytes="0"
  if [[ -n "${TAGS_JSON:-}" ]]; then
    if [[ $HAVE_JQ -eq 1 ]]; then
      bytes=$(echo "$TAGS_JSON" | jq -r --arg m "$model" '([.models[] | select(.name==$m) | .size] | first) // 0')
    else
      bytes=$(echo "$TAGS_JSON" | "$PY_BIN" - "$model" <<'PY'
import sys, json
data = json.load(sys.stdin)
needle = sys.argv[1]
size = 0
for m in data.get('models', []) or []:
    if m.get('name') == needle:
        size = int(m.get('size') or 0)
        break
print(size)
PY
)
    fi
  fi
  awk -v b="$bytes" 'BEGIN { if (b+0>0) printf "%.1f", b/1073741824; else printf "n/a" }'
}

# --- main ---
init_json_helpers
ensure_tags_json
if [[ -z "${PROMPT}" ]]; then
  if [[ -f "${DEFAULT_PROMPT_MD}" ]]; then
    PROMPT="$(cat "${DEFAULT_PROMPT_MD}")"
  else
    PROMPT="Task: Write one neutral, self-contained paragraph explaining how to benchmark small local language models fairly across devices.

Requirements:
- Output exactly five sentences.
- Each sentence must contain 14-16 words.
- Use plain English; avoid brand names, URLs, or platform-specific details.
- Do not include lists, headings, code, markdown, apologies, or meta commentary.
- Provide only the paragraph content; no title, no introduction, no closing."
  fi
fi
parse_args "$@"

ENDPOINT="http://${HOST}:${PORT}/api/generate"

# Resolve models list (flags, then positionals, then defaults)
MODELS=("${MODELS_INPUT[@]}")
if [[ ${#MODELS[@]} -eq 0 ]]; then
  MODELS=(
    "phi4-mini:3.8b"
    "gemma3:4b"
    "deepseek-r1:8b"
    "qwen3:8b"
    "gpt-oss:latest"
    "qwen3-coder:30b"
  )
fi

append_csv_header_if_needed "$CSV_OUT"

echo "Benchmarking against ${ENDPOINT}"
if [[ -n "$LABEL" ]]; then
  echo "Label: $LABEL"
fi

# Show a minimal env snapshot helpful for demos
for k in OLLAMA_NUM_PARALLEL OLLAMA_MAX_LOADED_MODELS OLLAMA_FLASH_ATTENTION OLLAMA_KV_CACHE_TYPE OLLAMA_KEEP_ALIVE CUDA_VISIBLE_DEVICES; do
  v=${!k-}
  if [[ -n "${v:-}" ]]; then
    printf "env %-24s = %s\n" "$k" "$v"
  fi
done

printf "\n%-36s  %7s  %6s  %6s  %8s  %8s  %8s  %8s\n" "MODEL" "DISK_GB" "PREL" "CTX" "LOAD_S" "EVAL_S" "TOK/S" "TOTAL_S"
printf "%-36s  %7s  %6s  %6s  %8s  %8s  %8s  %8s\n" "------------------------------------" "-------" "----" "------" "--------" "--------" "--------" "--------"

for m in "${MODELS[@]}"; do
  PRELOADED=$(is_model_preloaded "$m")
  LOCAL=$(model_available_locally "$m")
  DISK_GB=$(disk_gb_for_model "$m")
  # Build request JSON
  keepalive_clause=""
  if [[ "$COLD" -eq 1 ]]; then
    keepalive_clause=", \"keep_alive\": \"0s\""
  fi

  seed_clause=""
  if [[ -n "${SEED}" ]]; then
    seed_clause=", \"seed\": ${SEED}"
  fi

  # JSON-encode the prompt to avoid shell-quoting issues in JSON
  if [[ $HAVE_JQ -eq 1 ]]; then
    PROMPT_JSON=$(printf '%s' "$PROMPT" | jq -Rs .)
  else
    PROMPT_JSON=$(printf '%s' "$PROMPT" | json_stringify_stdin)
  fi

  read -r -d '' JSON_BODY <<JSON || true
{ "model": "$m",
  "prompt": ${PROMPT_JSON},
  "stream": false${keepalive_clause},
  "options": { "temperature": ${TEMPERATURE}, "num_predict": ${NUM_PREDICT}, "num_ctx": ${NUM_CTX}${seed_clause} }
}
JSON

  RESP=$(curl -sS -X POST "$ENDPOINT" -H 'Content-Type: application/json' -d "$JSON_BODY") || {
    echo "[!] Request failed for $m" >&2; printf "%-36s  %7s  %6s  %6s  %8s  %8s  %8s  %8s\n" "$m" "$DISK_GB" "${PRELOADED^^}" "n/a" "n/a" "n/a" "n/a" "n/a"; continue;
  }

  if [[ "$LOCAL" != "yes" && $DEBUG -eq 1 ]]; then
    echo "[debug] Model '$m' not found in /api/tags" >&2
  fi

  # Extract metrics (tolerate field name variations)
  TOKENS=$(json_get_num "$RESP" 0 eval_count eval_tokens)
  EVAL_NS=$(json_get_num "$RESP" 0 eval_duration metrics.eval_duration)
  TOTAL_NS=$(json_get_num "$RESP" 0 total_duration metrics.total_duration)
  LOAD_NS=$(json_get_num "$RESP" 0 load_duration metrics.load_duration)
  PEV_NS=$(json_get_num "$RESP" 0 prompt_eval_duration metrics.prompt_eval_duration)
  ERR_MSG=$(json_get_str "$RESP" error)

  EVAL_S=$(format_ns "$EVAL_NS")
  TOTAL_S=$(format_ns "$TOTAL_NS")
  LOAD_S=$(format_ns "$LOAD_NS")
  PEV_S=$(format_ns "$PEV_NS")

  if [[ "$EVAL_S" != "n/a" ]]; then
    TOKS=$(awk -v t="$TOKENS" 'BEGIN { printf "%d", t }')
    TPS=$(format_tps "$TOKENS" "$EVAL_S")
  else
    TOKS="n/a"; TPS="n/a"
  fi

  # Obtain context window size from /api/ps after the run
  ctx_window_for_model() {
    local model="$1"; local ps_json; local ctx="0"
    ps_json=$(curl -sS "http://${HOST}:${PORT}/api/ps" 2>/dev/null || true)
    if [[ -n "$ps_json" ]]; then
      if [[ $HAVE_JQ -eq 1 ]]; then
        ctx=$(echo "$ps_json" | jq -r --arg m "$model" '([.models[] | select(.name==$m) | (.context_length // .ctx // .context // 0)] | first) // 0')
      else
        ctx=$(echo "$ps_json" | "$PY_BIN" - "$model" <<'PY'
import sys, json
needle = sys.argv[1]
data = json.load(sys.stdin)
val = 0
for mod in data.get('models', []) or []:
    if mod.get('name') == needle:
        for k in ('context_length','ctx','context'):
            v = mod.get(k)
            if isinstance(v, (int, float)):
                val = int(v)
                break
        break
print(val)
PY
)
      fi
    fi
    echo "${ctx:-0}"
  }

  CTX_WIN=$(ctx_window_for_model "$m")
  if [[ "${CTX_WIN}" =~ ^[0-9]+$ ]] && [[ "$CTX_WIN" -gt 0 ]]; then
    CTX="$CTX_WIN"
  else
    CTX="$NUM_CTX"
    [[ $DEBUG -eq 1 ]] && echo "[debug] context window not reported for $m; using requested ${NUM_CTX}" >&2
  fi

  printf "%-36s  %7s  %6s  %6s  %8s  %8s  %8s  %8s\n" "$m" "$DISK_GB" "${PRELOADED^^}" "$CTX" "$LOAD_S" "$EVAL_S" "$TPS" "$TOTAL_S"

  if [[ -n "$ERR_MSG" ]]; then
    if [[ $DEBUG -eq 1 ]]; then
      echo "[debug] Error for $m: $ERR_MSG" >&2
      echo "[debug] Raw response: $RESP" >&2
    else
      echo "[!] $m error: $ERR_MSG" >&2
    fi
  fi

  if [[ -n "$CSV_OUT" ]]; then
    ts=$(date -Iseconds 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "$ts,${LABEL},${m},${PRELOADED},${TOKENS},${LOAD_S},${EVAL_S},${TPS},${TOTAL_S},${PEV_S},${DISK_GB},${CTX}" >>"$CSV_OUT"
  fi
done

printf "\nTip: use --label and --csv to compare baseline vs optimized runs.\n"
