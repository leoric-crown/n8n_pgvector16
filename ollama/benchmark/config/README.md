# Configuration Files

This directory contains YAML configuration files for the Ollama benchmark tools.

## Available Configuration Files

### benchmark_config.yaml

Default configuration for `benchmark_models.py` - the main benchmarking tool.

**Usage:**

```bash
# Auto-loads if present (default behavior)
./benchmark_models.py

# Explicitly specify
./benchmark_models.py --config config/benchmark_config.yaml

# Override with CLI flags
./benchmark_models.py --num-ctx 16384 --temperature 0.5
```

### context_matrix.yaml

Configuration for `run_matrix.py` - runs benchmarks across multiple context window sizes.

**Usage:**

```bash
# Auto-loads from config/context_matrix.yaml
./run_matrix.py

# Use custom config
./run_matrix.py --config my_custom_matrix.yaml

# Override parameters via CLI
./run_matrix.py --num-predict 2048 --temperature 0.3
```

## Configuration Precedence

Both tools follow a **consistent precedence hierarchy**:

```text
CLI Flags > Environment Variables > YAML Config > Hardcoded Defaults
(highest)                                            (lowest)
```

### Example: num_predict Parameter

```bash
# Scenario 1: Only defaults
./benchmark_models.py
# Result: num_predict = 256 (hardcoded default)

# Scenario 2: YAML config sets num_predict: 1024
./benchmark_models.py --config config/benchmark_config.yaml
# Result: num_predict = 1024 (from YAML)

# Scenario 3: Environment variable set
export OLLAMA_NUM_PREDICT=512
./benchmark_models.py --config config/benchmark_config.yaml
# Result: num_predict = 512 (env var overrides YAML)

# Scenario 4: CLI flag provided
export OLLAMA_NUM_PREDICT=512
./benchmark_models.py --config config/benchmark_config.yaml --num-predict 2048
# Result: num_predict = 2048 (CLI wins over everything)
```

## Environment Variables

The following environment variables are supported by `benchmark_models.py`:

| Environment Variable | Config Parameter | Type   | Example     |
| -------------------- | ---------------- | ------ | ----------- |
| `OLLAMA_HOST`        | host             | string | `localhost` |
| `OLLAMA_PORT`        | port             | int    | `11434`     |
| `OLLAMA_NUM_PREDICT` | num_predict      | int    | `1024`      |
| `OLLAMA_NUM_CTX`     | num_ctx          | int    | `8192`      |
| `OLLAMA_TEMPERATURE` | temperature      | float  | `0.2`       |
| `OLLAMA_KEEP_ALIVE`  | keep_alive       | string | `5m`        |
| `OLLAMA_DEBUG`       | debug            | bool   | `true`      |

**Docker/CI Example:**

```bash
docker run \
  -e OLLAMA_HOST=ollama-server \
  -e OLLAMA_NUM_CTX=16384 \
  -e OLLAMA_NUM_PREDICT=1024 \
  my-benchmark-image
```

## Output Organization

Results are automatically saved in **timestamped subdirectories** for better organization:

```text
results/
├── 20250101-120000/        # Run timestamp
│   ├── benchmark-8k.csv
│   ├── benchmark-8k.json
│   ├── benchmark-16k.csv
│   └── benchmark-16k.json
└── 20250101-130000/        # Another run
    ├── benchmark-8k.csv
    └── benchmark-8k.json
```

This keeps results from different benchmark runs cleanly separated.

**Behavior:**

- `run_matrix.py`: All results from a single matrix run go into one timestamped directory
- `benchmark_models.py`: Creates timestamped directory if you specify just a filename
- Use full paths (e.g., `results/baseline.csv`) to avoid automatic timestamping

## CLI Parameter Overrides

### benchmark_models.py

```bash
# All parameters can be overridden via CLI
./benchmark_models.py \
  --num-ctx 32768 \
  --num-predict 2048 \
  --temperature 0.5 \
  --repeat-runs 3 \
  --keep-alive "5m" \
  -s "gpt-oss"
```

### run_matrix.py

```bash
# Override specific parameters while keeping matrix definition from YAML
./run_matrix.py \
  --num-predict 2048 \
  --temperature 0.3 \
  --repeat-runs 5 \
  --keep-alive "10m"
```

## Configuration Philosophy

### Why This Design?

1. **Defaults** → Quick start without any setup
2. **YAML Config** → Project-level shared settings (committed to git)
3. **Environment Variables** → Deployment-specific settings (Docker, K8s, CI/CD)
4. **CLI Flags** → Experiment and one-off runs (highest priority)

### Best Practices

#### For Development

```bash
# Keep a local config with your preferences
cp config/benchmark_config.yaml config/benchmark_config.local.yaml
# Edit config/benchmark_config.local.yaml
./benchmark_models.py --config config/benchmark_config.local.yaml
```

#### For CI/CD

```yaml
# .github/workflows/benchmark.yml
env:
  OLLAMA_HOST: ollama-server
  OLLAMA_NUM_CTX: 8192
  OLLAMA_NUM_PREDICT: 1024

jobs:
  benchmark:
    steps:
      - run: ./benchmark_models.py --select "gpt-oss|gemma3"
```

#### For Production Monitoring

```bash
# Use YAML for stable baseline, env vars for deployment specifics
export OLLAMA_HOST=prod-ollama-lb.internal
export OLLAMA_PORT=11434
./benchmark_models.py --config config/prod_baseline.yaml
```

## Usage Examples

### Single Model Benchmark

```bash
# Minimal - use defaults
./benchmark_models.py phi4-mini:3.8b

# With config
./benchmark_models.py --config config/benchmark_config.yaml -s "phi4"

# Full control
./benchmark_models.py phi4-mini:3.8b \
  --num-ctx 16384 \
  --num-predict 1024 \
  --temperature 0.2 \
  --csv results/phi4_baseline.csv
```

### Matrix Benchmark

```bash
# Use config/context_matrix.yaml (default)
./run_matrix.py

# Override parameters
./run_matrix.py --num-predict 2048 --temperature 0.5

# Dry run to preview
./run_matrix.py --dry-run
```

## Troubleshooting

### Config file not found

```bash
# Check path relative to script location
ls -la config/

# Use absolute path if needed
./benchmark_models.py --config /full/path/to/config.yaml
```

### Environment variables not working

```bash
# Verify they're set
env | grep OLLAMA_

# Test precedence
export OLLAMA_NUM_PREDICT=999
./benchmark_models.py --debug  # Should show 999 in config
```

### CLI overrides not applied

```bash
# Ensure you're using the correct flag names
./benchmark_models.py --help  # Shows all available flags

# Check for typos (use -- for long flags)
./benchmark_models.py --num-ctx 8192  # Correct
./benchmark_models.py -num-ctx 8192   # Wrong (missing -)
```

## Related Documentation

- [CONFIG-ANALYSIS.md](../CONFIG-ANALYSIS.md) - Detailed technical analysis
- [MATRIX_TESTING.md](../MATRIX_TESTING.md) - Matrix testing guide
- [README.md](../README.md) - Main benchmark tool documentation
