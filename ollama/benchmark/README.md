# Ollama Benchmark Tools

Comprehensive benchmarking utilities for Ollama models with support for:

- 🚀 Live streaming display with rich terminal UI
- 📊 Memory usage monitoring (RAM/VRAM split)
- 🔄 Multiple context window sizes testing
- 📈 Statistical analysis across runs
- 💾 Export to CSV, JSON, and Parquet formats

## Published Benchmark Results

This repository includes comprehensive benchmark results comparing LLM model performance on consumer hardware.

📊 **[View published benchmark analysis →](../../docs/BENCHMARKS.md)**

Key findings include context window scaling analysis (8K→100K tokens), memory efficiency comparisons, and real-world use
case recommendations for models running on RTX 4090 (24GB VRAM).

## Quick Start

### Installation

Using `uv` (recommended - fast and reliable):

```bash
cd ollama/benchmark

# Dependencies are managed automatically with uv
uv run --with-requirements requirements.txt benchmark_models.py --help
```

Or create a virtual environment:

```bash
cd ollama/benchmark
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### Basic Usage

#### Single Model Benchmark

```bash
# Using uv (recommended)
uv run --with-requirements requirements.txt benchmark_models.py phi4-mini:3.8b

# Or with activated venv
./benchmark_models.py phi4-mini:3.8b
```

#### Multiple Models

```bash
# Pattern matching
uv run --with-requirements requirements.txt benchmark_models.py -s "phi4|gemma3"

# Explicit list
uv run --with-requirements requirements.txt benchmark_models.py phi4-mini:3.8b gemma3:4b qwen3:8b
```

#### Context Window Matrix Test

```bash
# Run across multiple context sizes (8K, 16K, 32K, 64K, 100K)
uv run --with-requirements requirements.txt run_matrix.py

# Preview commands without running
uv run --with-requirements requirements.txt run_matrix.py --dry-run

# Override specific parameters
uv run --with-requirements requirements.txt run_matrix.py --num-predict 2048 --temperature 0.5
```

## Configuration

All tools support a **consistent configuration hierarchy**:

```text
CLI Flags > Environment Variables > YAML Config > Hardcoded Defaults
```

### Configuration Files

Stored in `config/` directory:

- `benchmark_config.yaml` - Default config for benchmark_models.py
- `context_matrix.yaml` - Matrix test configuration

See [config/README.md](config/README.md) for detailed configuration guide.

### Environment Variables

```bash
export OLLAMA_HOST=localhost
export OLLAMA_PORT=11434
export OLLAMA_NUM_CTX=16384
export OLLAMA_NUM_PREDICT=1024
export OLLAMA_TEMPERATURE=0.2

uv run --with-requirements requirements.txt benchmark_models.py -s "gpt-oss"
```

### Example Configurations

```bash
# Quick test with custom context
uv run --with-requirements requirements.txt benchmark_models.py \
  --num-ctx 8192 \
  --num-predict 512 \
  -s "phi4" \
  --csv results/phi4_8k.csv

# Statistical analysis with multiple runs
uv run --with-requirements requirements.txt benchmark_models.py \
  --repeat-runs 5 \
  --temperature 0.2 \
  phi4-mini:3.8b gemma3:4b

# Matrix test with overrides
uv run --with-requirements requirements.txt run_matrix.py \
  --num-predict 2048 \
  --repeat-runs 3
```

## Output

Results are automatically saved to **timestamped subdirectories** in `results/`:

```text
results/
├── 20250101-120000/
│   ├── benchmark-8k.csv
│   ├── benchmark-8k.json
│   ├── benchmark-16k.csv
│   └── benchmark-16k.json
└── 20250101-130000/
    └── single-model.csv
```

This keeps results from different benchmark runs cleanly organized.

**Supported formats:**

- CSV: Easy import to Excel/Pandas
- JSON: Structured data with all metrics
- Parquet: Efficient storage for large datasets

### Example Output

```text
┌──────────────────┬─────────┬───────────┬─────────┬──────────┬─────────┬──────────┬──────────┬───────────┬──────────┐
│ Model            │ Disk GB │ Preloaded │ Context │ RAM/VRAM │ MEM GB  │ Load (s) │ Eval (s) │ Tok/s     │ Total(s) │
├──────────────────┼─────────┼───────────┼─────────┼──────────┼─────────┼──────────┼──────────┼───────────┼──────────┤
│ phi4-mini:3.8b   │ 2.3     │ NO        │ 8192    │ 0%/100%  │ 4.2     │ 0.845    │ 2.134    │ 120.1     │ 3.021    │
│ gemma3:4b        │ 2.5     │ NO        │ 8192    │ 0%/100%  │ 4.8     │ 0.923    │ 1.891    │ 135.4     │ 2.856    │
│ deepseek-r1:8b   │ 4.7     │ NO        │ 8192    │ 3%/97%   │ 6.1     │ 1.234    │ 3.456    │ 74.1      │ 4.721    │
└──────────────────┴─────────┴───────────┴─────────┴──────────┴─────────┴──────────┴──────────┴───────────┴──────────┘
```

## Features

### Live Streaming Display

Real-time display of model responses during generation with:

- Token-by-token streaming
- Memory usage updates
- Progress tracking
- Auto-scrolling text display

### Memory Monitoring

Captures RAM/VRAM split from `ollama ps`:

- GPU percentage
- CPU percentage
- Total memory size
- Processor type

### Statistical Analysis

Multiple runs provide statistical insights:

- Mean tokens/second
- Standard deviation
- Min/Max values
- Performance variability

### Export Formats

Choose your preferred format:

```bash
uv run --with-requirements requirements.txt benchmark_models.py \
  --csv results/benchmark.csv \
  --json results/benchmark.json \
  --parquet results/benchmark.parquet \
  -s "all"
```

## Advanced Usage

### Custom Prompt

```bash
# Inline prompt
uv run --with-requirements requirements.txt benchmark_models.py \
  -p "Explain quantum computing in 100 words" \
  phi4-mini:3.8b

# From file
uv run --with-requirements requirements.txt benchmark_models.py \
  --prompt-file my_prompt.txt \
  phi4-mini:3.8b
```

### Remote Ollama Server

```bash
uv run --with-requirements requirements.txt benchmark_models.py \
  --host remote-server \
  --port 11434 \
  -s "all"
```

### Matrix Testing

The matrix runner executes benchmarks across multiple context window sizes:

```bash
# Default matrix (8K, 16K, 32K, 64K, 100K)
uv run --with-requirements requirements.txt run_matrix.py

# With parameter overrides
uv run --with-requirements requirements.txt run_matrix.py \
  --num-predict 2048 \
  --temperature 0.3 \
  --repeat-runs 5

# Custom config
uv run --with-requirements requirements.txt run_matrix.py \
  --config config/my_matrix.yaml
```

## Convenience Aliases

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias obench='cd /path/to/ollama/benchmark && uv run --with-requirements requirements.txt benchmark_models.py'
alias omatrix='cd /path/to/ollama/benchmark && uv run --with-requirements requirements.txt run_matrix.py'

# Then use:
obench -s "phi4"
omatrix --dry-run
```

Or create simple wrapper scripts in the project root:

```bash
#!/bin/bash
# benchmark.sh
cd "$(dirname "$0")/ollama/benchmark"
exec uv run --with-requirements requirements.txt benchmark_models.py "$@"
```

## Tips & Best Practices

### 1. Start with Default Models

```bash
uv run --with-requirements requirements.txt benchmark_models.py
# Tests: phi4-mini:3.8b, gemma3:4b, deepseek-r1:8b, qwen3:8b, gpt-oss:latest, qwen3-coder:30b
```

### 2. Use Labels for Comparisons

```bash
# Baseline run
uv run --with-requirements requirements.txt benchmark_models.py \
  --label "baseline" \
  --csv results/baseline.csv \
  -s "gpt-oss"

# After optimization
uv run --with-requirements requirements.txt benchmark_models.py \
  --label "optimized" \
  --csv results/optimized.csv \
  -s "gpt-oss"

# Compare in Pandas
python -c "
import pandas as pd
baseline = pd.read_csv('results/baseline.csv')
optimized = pd.read_csv('results/optimized.csv')
print(pd.concat([baseline, optimized]))
"
```

### 3. Statistical Runs

```bash
uv run --with-requirements requirements.txt benchmark_models.py \
  --repeat-runs 10 \
  --csv results/stats.csv \
  phi4-mini:3.8b
```

### 4. Memory Optimization Testing

```bash
# Test different keep-alive settings
export OLLAMA_KEEP_ALIVE=30s
uv run --with-requirements requirements.txt benchmark_models.py -s "all"

# Or via CLI
uv run --with-requirements requirements.txt benchmark_models.py \
  --keep-alive "5m" \
  -s "all"
```

## Troubleshooting

### "No module named 'rich'"

Install dependencies:

```bash
cd ollama/benchmark
uv pip install -r requirements.txt
```

### Python Environment Issues

Use `uv run` which handles environments automatically:

```bash
uv run --with-requirements requirements.txt benchmark_models.py --help
```

### Connection Errors

Check Ollama is running:

```bash
curl http://localhost:11434/api/tags
```

Or specify different host:

```bash
uv run --with-requirements requirements.txt benchmark_models.py --host remote-host --port 11434
```

### Models Not Found

List available models:

```bash
ollama ls
```

Pull missing models:

```bash
ollama pull phi4-mini:3.8b
```

## Documentation

- [config/README.md](config/README.md) - Configuration guide
- [CONFIG-ANALYSIS.md](CONFIG-ANALYSIS.md) - Technical analysis
- [CHANGES.md](CHANGES.md) - Recent improvements
- [MATRIX_TESTING.md](MATRIX_TESTING.md) - Matrix testing guide

## Examples

See the `examples/` directory for:

- Custom prompts
- Analysis scripts
- Visualization notebooks
- CI/CD integration examples

## Contributing

1. Test changes with `uv run`:

   ```bash
   uv run --with-requirements requirements.txt benchmark_models.py --debug
   ```

2. Run with dry-run mode first:

   ```bash
   uv run --with-requirements requirements.txt run_matrix.py --dry-run
   ```

3. Check results format:

   ```bash
   python -c "import pandas as pd; print(pd.read_csv('results/benchmark.csv'))"
   ```

## License

See project root for license information.
