#!/usr/bin/env bash
set -euo pipefail

# Tune Ollama for NVIDIA GPUs (e.g., RTX 4090).
# Creates a systemd drop-in with environment configuration, then restarts Ollama.

# Optional flags:
#   -y, --yes   Proceed non-interactively (auto-backup and overwrite if needed)

ASSUME_YES=0
for arg in "$@"; do
  case "$arg" in
    -y|--yes) ASSUME_YES=1 ;;
    *) ;;
  esac
done

if [[ $EUID -ne 0 ]]; then
  echo "[!] This script should be run with sudo to write systemd overrides." >&2
  echo "    sudo $0" >&2
  exit 1
fi

OVERRIDE_DIR="/etc/systemd/system/ollama.service.d"
OVERRIDE_FILE="${OVERRIDE_DIR}/override.conf"

echo "[+] Preparing systemd drop-in for Ollama env..."
mkdir -p "${OVERRIDE_DIR}"

tmpfile="$(mktemp)"
trap 'rm -f "$tmpfile"' EXIT

cat >"$tmpfile" <<'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_MAX_LOADED_MODELS=2"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_KEEP_ALIVE=30m"
Environment="OLLAMA_GPU_OVERHEAD=134217728"  # 128MB VRAM reserved
EOF

changed=0
if [[ -f "${OVERRIDE_FILE}" ]]; then
  if cmp -s "$tmpfile" "${OVERRIDE_FILE}"; then
    echo "[=] Existing ${OVERRIDE_FILE} already matches desired configuration."
  else
    if [[ $ASSUME_YES -eq 1 ]]; then
      reply="y"
    else
      read -r -p "[?] ${OVERRIDE_FILE} exists and differs. Backup and overwrite? [y/N]: " reply || reply="n"
    fi
    case "$reply" in
      y|Y|yes|YES)
        ts="$(date +%Y%m%d%H%M%S)"
        backup="${OVERRIDE_FILE}.bak-${ts}"
        cp -a "${OVERRIDE_FILE}" "$backup"
        echo "[+] Backed up existing file to $backup"
        install -m 0644 "$tmpfile" "${OVERRIDE_FILE}"
        echo "[+] Wrote new ${OVERRIDE_FILE}"
        changed=1
        ;;
      *)
        echo "[i] Skipping overwrite. Leaving existing file unchanged."
        ;;
    esac
  fi
else
  install -D -m 0644 "$tmpfile" "${OVERRIDE_FILE}"
  echo "[+] Created ${OVERRIDE_FILE}"
  changed=1
fi

if [[ $changed -eq 1 ]]; then
  echo "[+] Reloading systemd and restarting Ollama..."
  systemctl daemon-reload
  systemctl restart ollama
  echo "[+] Checking service and API..."
  sleep 2
  systemctl --no-pager --full status ollama | sed -n '1,10p' || true
  curl -s http://localhost:11434/api/ps | jq '.' 2>/dev/null || curl -s http://localhost:11434/api/ps || true
  echo "[OK] NVIDIA tuning applied."
else
  echo "[i] No changes applied; skipping restart."
fi

echo "[i] Ollama is bound to 0.0.0.0:11434 (LAN)."
echo "    To change bind address or CORS, edit: ${OVERRIDE_FILE} and restart: systemctl restart ollama"
