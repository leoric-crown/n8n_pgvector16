#!/bin/bash
# Convenience wrapper for run_matrix.py
# Usage: ./matrix.sh [options]
# Example: ./matrix.sh --dry-run
# Example: ./matrix.sh --num-predict 2048 --temperature 0.5

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo uv run --with-requirements requirements.txt src/run_matrix.py "$@"
exec uv run --with-requirements requirements.txt src/run_matrix.py "$@"
