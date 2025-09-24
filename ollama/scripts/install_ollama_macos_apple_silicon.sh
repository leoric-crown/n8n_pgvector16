#!/usr/bin/env bash
set -euo pipefail

# Install Ollama on macOS (Apple Silicon) via Homebrew and verify basics.
# Requires: macOS (Darwin), Apple Silicon (arm64), Homebrew.

echo "[+] Validating platform..."
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "[-] This installer is for macOS only (Darwin)." >&2
  exit 1
fi
if [[ "$(uname -m)" != "arm64" ]]; then
  echo "[-] This installer targets Apple Silicon (arm64)." >&2
  exit 1
fi

echo "[+] Checking Homebrew..."
BREW_BIN="$(command -v brew || true)"
if [[ -z "${BREW_BIN}" ]]; then
  if [[ -x "/opt/homebrew/bin/brew" ]]; then
    BREW_BIN="/opt/homebrew/bin/brew"
  else
    cat <<'MSG' >&2
[-] Homebrew not found.
Install Homebrew first (non-interactive example):
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

Then re-run this script.
MSG
    exit 1
  fi
fi

echo "[+] Installing/upgrading Ollama via Homebrew..."
"${BREW_BIN}" update || true
if "${BREW_BIN}" list --formula ollama >/dev/null 2>&1; then
  "${BREW_BIN}" upgrade ollama || true
else
  "${BREW_BIN}" install ollama
fi

echo "[+] Starting Ollama as a user service (launchd)..."
if "${BREW_BIN}" services list | grep -q '^ollama\b'; then
  "${BREW_BIN}" services restart ollama || "${BREW_BIN}" services start ollama
else
  "${BREW_BIN}" services start ollama
fi

echo "[+] Verifying API..."
sleep 2
if curl -sSf http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "[OK] Ollama API is responsive on :11434"
else
  echo "[-] Ollama API not responding on :11434" >&2
  echo "    Check service logs: \"${BREW_BIN}\" services log ollama" >&2
  exit 1
fi

cat <<'MSG'

Done.

Next steps (optional but recommended):
- Run ./tune_env_macos.sh to enable flash attention, KV cache quant, and sensible limits for Apple Silicon
- Pull a model (example):
    ollama pull llama3.2:3b-instruct
- Sanity-check generation (example):
    curl -s http://localhost:11434/api/generate \
      -H 'Content-Type: application/json' \
      -d '{"model":"llama3.2:3b-instruct","prompt":"Hello!"}' | sed 's/\r//g'

Tips:
- To view service logs: brew services log ollama
- To stop/start manually: brew services stop|start ollama

MSG
