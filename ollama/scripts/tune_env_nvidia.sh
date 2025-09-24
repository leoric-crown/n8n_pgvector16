#!/usr/bin/env bash
set -euo pipefail

# Tune Ollama for NVIDIA GPUs (e.g., RTX 4090).
# Creates a systemd drop-in with environment configuration, then restarts Ollama.

if [[ $EUID -ne 0 ]]; then
  echo "[!] This script should be run with sudo to write systemd overrides." >&2
  echo "    sudo $0" >&2
  exit 1
fi

echo "[+] Creating systemd drop-in for Ollama env..."
mkdir -p /etc/systemd/system/ollama.service.d
cat >/etc/systemd/system/ollama.service.d/override.conf <<'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_MAX_LOADED_MODELS=2"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_KEEP_ALIVE=30m"
Environment="OLLAMA_GPU_OVERHEAD=2147483648"  # 2GB VRAM reserved
# Optional: limit to GPU 0
Environment="CUDA_VISIBLE_DEVICES=0"
EOF

echo "[+] Reloading systemd and restarting Ollama..."
systemctl daemon-reload
systemctl restart ollama

echo "[+] Checking service and API..."
sleep 2
systemctl --no-pager --full status ollama | sed -n '1,10p' || true
curl -s http://localhost:11434/api/ps | jq '.' 2>/dev/null || curl -s http://localhost:11434/api/ps || true

echo "[OK] NVIDIA tuning applied."
echo "[i] Ollama is bound to 0.0.0.0:11434 (LAN)."
echo "    To change bind address or CORS, edit: /etc/systemd/system/ollama.service.d/override.conf and restart: systemctl restart ollama"
