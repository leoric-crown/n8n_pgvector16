#!/usr/bin/env bash
set -euo pipefail

# Tune Ollama on macOS (Apple Silicon) installed via Homebrew.
# Uses launchctl to set env for current login session and restarts the Homebrew service.
# Note: launchctl env does not persist across reboot; repeat after login or edit the Homebrew launchd plist.

# Platform guards: macOS + Apple Silicon only
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "[-] This script is for macOS (Darwin) only." >&2
  exit 1
fi
if [[ "$(uname -m)" != "arm64" ]]; then
  echo "[-] This script targets Apple Silicon (arm64)." >&2
  exit 1
fi

echo "[+] Setting Ollama environment variables for this session..."

launchctl setenv OLLAMA_NUM_PARALLEL 4
launchctl setenv OLLAMA_MAX_LOADED_MODELS 2
launchctl setenv OLLAMA_FLASH_ATTENTION 1
launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0
launchctl setenv OLLAMA_KEEP_ALIVE 30m

echo "[+] Restarting Ollama (Homebrew service)..."
# Prefer direct launchctl restart of the Homebrew launch agent. Fallback to `brew services restart` if available.
if launchctl print "gui/$(id -u)/homebrew.mxcl.ollama" >/dev/null 2>&1; then
  launchctl kickstart -k "gui/$(id -u)/homebrew.mxcl.ollama" || true
else
  if command -v brew >/dev/null 2>&1; then
    brew services restart ollama || brew services start ollama || true
  else
    echo "[!] Homebrew service not detected. Ensure Ollama is installed via Homebrew and running as a user service." >&2
  fi
fi
sleep 2

echo "[+] Verifying API..."
curl -s http://localhost:11434/api/ps | jq '.' 2>/dev/null || curl -s http://localhost:11434/api/ps || true

cat <<'MSG'

[OK] macOS tuning applied to current session.

To persist env across reboots, edit the Homebrew LaunchAgent plist:
  ~/Library/LaunchAgents/homebrew.mxcl.ollama.plist

Add these variables to the existing EnvironmentVariables dict:
  <key>OLLAMA_NUM_PARALLEL</key>
  <string>4</string>
  <key>OLLAMA_MAX_LOADED_MODELS</key>
  <string>2</string>
  <key>OLLAMA_KEEP_ALIVE</key>
  <string>30m</string>

Note: OLLAMA_FLASH_ATTENTION and OLLAMA_KV_CACHE_TYPE might already be set as defaults.

After editing, reload the service:
  launchctl unload ~/Library/LaunchAgents/homebrew.mxcl.ollama.plist && \
  launchctl load -w ~/Library/LaunchAgents/homebrew.mxcl.ollama.plist

MSG
