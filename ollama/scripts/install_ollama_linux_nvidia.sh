#!/usr/bin/env bash
set -euo pipefail

sudo -v
# Install Ollama on Linux with NVIDIA GPU and verify basics.
# Requires: sudo, curl, NVIDIA driver installed.

echo "[+] Checking NVIDIA driver..."
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "[-] nvidia-smi not found. Install NVIDIA drivers first." >&2
  exit 1
fi
nvidia-smi --query-gpu=driver_version,name --format=csv,noheader || true

echo "[+] Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

echo "[+] Enabling and starting Ollama service..."
sudo systemctl enable ollama || true
sudo systemctl restart ollama || true

echo "[+] Verifying API..."
sleep 2
curl -s http://localhost:11434/api/tags >/dev/null && echo "[OK] Ollama API is responsive" || {
  echo "[-] Ollama API not responding on :11434" >&2
  exit 1
}

cat <<'MSG'

Done.

Next steps (optional but recommended):
- Run ./tune_env_nvidia.sh to enable flash attention, KV cache quant, and sensible limits
- Run ./pull_baseline_models.sh to fetch the baseline pack
- Run ./benchmark_models.sh to sanity‑check performance

MSG
