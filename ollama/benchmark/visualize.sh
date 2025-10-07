#!/bin/bash
# Wrapper script for visualize_benchmarks.py

cd "$(dirname "$0")"
exec uv run --with-requirements requirements.txt python src/visualize_benchmarks.py "$@"
