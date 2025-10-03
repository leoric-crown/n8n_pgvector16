# Quick Start Guide

## TL;DR - Just Run It

```bash
cd ollama/benchmark

# Single model benchmark (easiest)
./bench.sh phi4-mini:3.8b

# Multiple models by pattern
./bench.sh -s "phi4|gemma3"

# Context matrix test (8K, 16K, 32K, 64K, 100K)
./matrix.sh

# Preview matrix without running
./matrix.sh --dry-run
```

## Installation

**No setup required!** The wrapper scripts use `uv` to manage dependencies automatically.

If you want a traditional venv:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Basic Commands

### Benchmark Single Model

```bash
./bench.sh phi4-mini:3.8b
```

### Benchmark Multiple Models

```bash
# By pattern
./bench.sh -s "phi4|gemma3|deepseek"

# Explicit list
./bench.sh phi4-mini:3.8b gemma3:4b qwen3:8b

# All available models
./bench.sh -s all
```

### Custom Parameters

```bash
./bench.sh \
  --num-ctx 16384 \
  --num-predict 1024 \
  --temperature 0.5 \
  -s "gpt-oss"
```

### Matrix Test (Multiple Context Sizes)

```bash
# Run full matrix
./matrix.sh

# Override parameters
./matrix.sh --num-predict 2048 --temperature 0.3

# Preview what will run
./matrix.sh --dry-run
```

## Configuration

Files in `config/` directory:

- `benchmark_config.yaml` - Defaults for bench.sh
- `context_matrix.yaml` - Matrix configuration

### Quick Config Edit

```bash
# Edit defaults
nano config/benchmark_config.yaml

# Edit matrix settings
nano config/context_matrix.yaml
```

### Environment Variables

```bash
export OLLAMA_NUM_CTX=16384
export OLLAMA_NUM_PREDICT=1024
./bench.sh -s "all"
```

### Precedence

```text
CLI Flags > Environment Variables > YAML Config > Defaults
```

## Output

Results are saved in **timestamped subdirectories** in `results/`:

```text
results/
└── 20250101-120000/        # Timestamp of the run
    ├── benchmark-8k.csv
    ├── benchmark-8k.json
    ├── benchmark-16k.csv
    └── benchmark-16k.json
```

This keeps each benchmark run's files organized together.

### Export Options

```bash
./bench.sh \
  --csv results/my_benchmark.csv \
  --json results/my_benchmark.json \
  -s "phi4"
```

## Common Tasks

### Compare Baseline vs Optimized

```bash
# Baseline
./bench.sh --label "baseline" --csv results/baseline.csv -s "gpt-oss"

# After tuning
export OLLAMA_NUM_PARALLEL=2
./bench.sh --label "optimized" --csv results/optimized.csv -s "gpt-oss"
```

### Statistical Analysis

```bash
./bench.sh --repeat-runs 10 phi4-mini:3.8b
```

### Test All Context Sizes

```bash
./matrix.sh  # Tests 8K, 16K, 32K, 64K, 100K automatically
```

### Remote Ollama Server

```bash
./bench.sh --host remote-server --port 11434 -s "all"
```

## Help

```bash
./bench.sh --help
./matrix.sh --help
```

## Examples

### Quick Performance Check

```bash
./bench.sh phi4-mini:3.8b gemma3:4b
```

### Deep Context Testing

```bash
./matrix.sh --num-predict 2048
```

### Production Benchmark

```bash
./bench.sh \
  --num-ctx 8192 \
  --num-predict 1024 \
  --repeat-runs 5 \
  --csv results/prod_baseline_$(date +%Y%m%d).csv \
  -s "gpt-oss"
```

### Memory Efficiency Test

```bash
# Test keep-alive impact
./bench.sh --keep-alive "5m" -s "all"
```

## Troubleshooting

### "uv: command not found"

Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Connection refused"

Start Ollama:

```bash
ollama serve
```

### "Model not found"

Pull the model:

```bash
ollama pull phi4-mini:3.8b
```

### View Results

```bash
# CSV
cat results/benchmark-8k-*.csv

# JSON (pretty)
cat results/benchmark-8k-*.json | python -m json.tool

# With pandas
python -c "import pandas as pd; print(pd.read_csv('results/benchmark-8k-*.csv'))"
```

## Tips

1. **Start small**: Test one model first

   ```bash
   ./bench.sh phi4-mini:3.8b
   ```

2. **Use dry-run**: Preview before running

   ```bash
   ./matrix.sh --dry-run
   ```

3. **Use labels**: Track different configurations

   ```bash
   ./bench.sh --label "v1" --csv results/v1.csv -s "all"
   ```

4. **Statistical runs**: Multiple runs for reliability

   ```bash
   ./bench.sh --repeat-runs 5 phi4-mini:3.8b
   ```

5. **Pattern matching**: Flexible model selection

   ```bash
   ./bench.sh -s "^phi4"  # Models starting with phi4
   ./bench.sh -s "8b$"    # Models ending with 8b
   ```

## Documentation

- [README.md](README.md) - Full documentation
- [config/README.md](config/README.md) - Configuration guide
- [CONFIG-ANALYSIS.md](CONFIG-ANALYSIS.md) - Technical details
- [CHANGES.md](CHANGES.md) - Recent improvements

## That's It

You're ready to benchmark. Start with:

```bash
./bench.sh -s "phi4"
```

See live streaming output, memory usage, and tokens/sec. Results auto-saved to `results/`.
