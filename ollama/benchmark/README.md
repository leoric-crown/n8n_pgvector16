# Ollama Benchmark Tool

A comprehensive Python benchmarking utility for Ollama models with rich terminal output, memory monitoring, and flexible
data export capabilities.

## Features

- 🎨 **Rich Colored Output**: Beautiful terminal tables with color-coded performance metrics
- 📊 **Memory Monitoring**: Real-time RAM/VRAM split capture via `ollama ps`
- 💾 **Multiple Export Formats**: CSV, JSON, and Parquet for data analysis
- 🌐 **Remote Support**: Works with remote Ollama instances
- 📈 **Statistical Analysis**: Mean, std dev, and percentiles for multiple runs
- ⚡ **Progress Tracking**: Live progress bars during benchmarks
- 🔧 **Flexible Configuration**: CLI args and YAML config file support

## Installation

```bash
cd ollama/benchmark
pip install -r requirements.txt
```

## Quick Start

```bash
# Benchmark default models
python benchmark_models.py

# Benchmark all available models
python benchmark_models.py --select "all"

# Benchmark specific models with custom settings
python benchmark_models.py --models "phi4-mini:3.8b,gemma3:4b" --num-ctx 8192

# Pattern-based model selection with memory monitoring
python benchmark_models.py --select "deepseek|gemma" --mem-split

# Export results to multiple formats
python benchmark_models.py --csv results.csv --json results.json --parquet results.parquet
```

## Usage Examples

### Basic Benchmarking

```bash
# Run with default settings
python benchmark_models.py

# Specify models directly
python benchmark_models.py phi4-mini:3.8b gemma3:4b deepseek-r1:8b

# Use pattern matching
python benchmark_models.py --select "deepseek"
```

### Advanced Usage

```bash
# Full benchmark with all features
python benchmark_models.py \
  --select "all" \
  --num-ctx 128 \
  --num-predict 256 \
  --mem-split \
  --repeat-runs 3 \
  --csv results.csv \
  --label "baseline"

# Remote Ollama instance
python benchmark_models.py \
  --host remote-server.com \
  --port 11434 \
  --select "all"

# Cold runs (unload models between tests)
python benchmark_models.py --cold --select "deepseek"
```

### Configuration File

Create a `benchmark_config.yaml` file:

```yaml
host: localhost
port: 11434
num_predict: 256
num_ctx: 4096
temperature: 0.2
mem_split: true
models:
  - phi4-mini:3.8b
  - gemma3:4b
  - deepseek-r1:8b
csv_output: results.csv
```

Then run with:

```bash
python benchmark_models.py --config benchmark_config.yaml
```

## Output Format

The tool displays a rich colored table with:

- **Model**: Model name and version
- **Disk GB**: Model size on disk
- **Preloaded**: Whether model was already in memory
- **Context**: Context window size used
- **RAM/VRAM**: Memory split percentage (optional)
- **Memory GB**: Total memory usage (optional)
- **Load (s)**: Model loading time
- **Eval (s)**: Token evaluation time
- **Tok/s**: Tokens per second (color-coded)
- **Total (s)**: Total execution time

### Color Coding

- **Tok/s Performance**:
  - 🟢 Bright Green: >100 tok/s (excellent)
  - 🟢 Green: 50-100 tok/s (good)
  - 🟡 Yellow: 25-50 tok/s (moderate)
  - 🔴 Red: \<25 tok/s (slow)

## Command-Line Options

### Model Selection

- `models`: Positional arguments for model names
- `-m, --models LIST`: Comma-separated model list
- `-s, --select REGEX`: Pattern matching for model selection

### Benchmark Parameters

- `-p, --prompt TEXT`: Custom prompt text
- `--prompt-file FILE`: Load prompt from file
- `--num-predict N`: Tokens to generate (default: 256)
- `--num-ctx N`: Context window size (default: 4096)
- `--temperature F`: Generation temperature (default: 0.2)
- `--seed N`: Random seed for deterministic results
- `--repeat-runs N`: Number of runs per model (default: 1)

### Connection Settings

- `--host HOST`: Ollama host (default: localhost)
- `--port PORT`: Ollama port (default: 11434)

### Output Options

- `--label NAME`: Label for benchmark run
- `--csv FILE`: Export to CSV
- `--json FILE`: Export to JSON
- `--parquet FILE`: Export to Parquet

### Advanced Options

- `--cold`: Force cold runs (unload between tests)
- `--mem-split`: Capture RAM/VRAM split (default: enabled)
- `--no-mem-split`: Disable memory monitoring
- `--keep-alive DURATION`: Model keep-alive time (default: 2s)
- `--ollama-bin PATH`: Path to ollama binary
- `--config FILE`: Load configuration from YAML
- `--debug`: Enable debug output

## Memory Monitoring

When `--mem-split` is enabled (default), the tool captures:

- RAM/VRAM percentage split
- Total memory usage in GB
- Processor type (CPU/GPU/Mixed)
- Context length from active model

This requires the `ollama` CLI to be available in PATH or specified via `--ollama-bin`.

## Export Formats

### CSV Export

Perfect for spreadsheet analysis and plotting:

```csv
model,timestamp,preloaded,tokens,load_s,eval_s,tokens_per_second,...
```

### JSON Export

Structured data for programmatic processing:

```json
[
  {
    "model": "phi4-mini:3.8b",
    "tokens_per_second": 166.0,
    "memory_gb": 2.3,
    ...
  }
]
```

### Parquet Export

Efficient columnar format for data science workflows (requires `pyarrow`).

## Tips

- Use `--label` and `--csv` to compare baseline vs optimized runs
- Run with `--repeat-runs` for statistical analysis
- Use `--cold` to test cold-start performance
- Pattern matching with `--select` supports regex for flexible model selection
- The tool works with remote Ollama instances without local installation

## Requirements

- Python 3.8+
- Ollama API endpoint (local or remote)
- Optional: `ollama` CLI for memory monitoring
