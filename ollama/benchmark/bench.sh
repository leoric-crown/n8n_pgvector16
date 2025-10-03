#!/bin/bash
# Convenience wrapper for benchmark_models.py
# Usage: ./bench.sh [options]
# Example: ./bench.sh -s "phi4" --num-ctx 8192

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
echo uv run --with-requirements requirements.txt benchmark_models.py "$@"
exec uv run --with-requirements requirements.txt benchmark_models.py "$@"
