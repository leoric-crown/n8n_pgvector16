# 📊 Benchmark Tools

> **Comprehensive performance testing for Ollama models across context window sizes**

______________________________________________________________________

## ⚡ Quick Start

```bash
# Test single model
./bench.sh phi4-mini:3.8b

# Test multiple by pattern
./bench.sh -s "phi4|gemma3"

# Full context matrix (8K → 128K)
./matrix.sh

# Generate charts from results
./visualize.sh
```

______________________________________________________________________

## 📏 What Gets Measured

| **Metric**         | **Description**                                         |
| :----------------- | :------------------------------------------------------ |
| ⚡ **Performance** | Tokens/second across context sizes                      |
| 💾 **Memory**      | VRAM allocated (model + KV cache) and GPU utilization % |
| 📊 **Stability**   | Performance variance across runs                        |
| 📉 **Degradation** | Speed changes as context grows                          |

______________________________________________________________________

## 📂 Output Structure

Results saved to timestamped directories in `results/`:

```text
results/
├── 20251006-012211/           # Latest run
│   ├── ctx-8k/
│   │   ├── benchmark.json     # Raw data
│   │   └── benchmark.csv      # Spreadsheet format
│   ├── ctx-16k/
│   └── ...
└── charts/                     # Generated visualizations
    ├── performance.png         # Main performance chart
    ├── memory.png              # Memory usage chart
    ├── efficiency.png          # Memory vs speed
    ├── gpu_utilization.png     # GPU/RAM split
    └── summary.md              # Text summary
```

> \[!TIP\] Charts automatically aggregate data across **all runs** for statistical reliability

______________________________________________________________________

## 📈 Visualization

```bash
# Generate charts from all runs (aggregated + averaged)
./visualize.sh

# Use specific run
./visualize.sh results/20251006-012211/

# Output SVG instead of PNG
./visualize.sh --format svg
```

<details>
<summary><b>What the visualizations show</b></summary>

<br>

- **benchmark.png** — 🎯 Combined performance + GPU utilization view
- **memory.png** — 💾 VRAM allocation across context sizes
- **performance.png** — ⚡ Standalone performance view (reference)

</details>

______________________________________________________________________

## 🎯 Common Tasks

### Quick performance check

```bash
./bench.sh phi4-mini:3.8b gemma3:4b
```

### Test with custom context

```bash
./bench.sh --num-ctx 32768 --num-predict 1024 qwen3:8b
```

### Statistical runs

```bash
./bench.sh --repeat-runs 5 gpt-oss
```

### Full matrix test

```bash
./matrix.sh --num-predict 2048
```

______________________________________________________________________

## ⚙️ Configuration

Default settings in `config/`:

| File                    | Purpose                   |
| :---------------------- | :------------------------ |
| `benchmark_config.yaml` | Single benchmark defaults |
| `context_matrix.yaml`   | Matrix test configuration |

**Override via CLI or environment variables:**

```bash
export OLLAMA_NUM_CTX=16384
./bench.sh -s "all"
```

<details>
<summary><b>Example: Custom matrix run</b></summary>

<br>

Edit `config/context_matrix.yaml`:

```yaml
matrix:
  context_sizes:
    - 8192   # 8K
    - 16384  # 16K
    - 32768  # 32K
    - 65536  # 64K
    - 102400 # 100K

  models:
    - phi4-mini:3.8b
    - qwen3:8b
    - gpt-oss

benchmark:
  repeat_runs: 10  # Run each config 10 times
```

Then: `./matrix.sh`

</details>

______________________________________________________________________

## 📦 Requirements

Automatically handled by `uv`. Or manually:

```bash
pip install -r requirements.txt
```

Dependencies:

- `matplotlib` — Chart generation
- `pandas` — Data processing
- `rich` — Terminal UI
- `pyyaml` — Configuration

______________________________________________________________________

## 🏆 Published Results

See `results/charts/` for visual analysis on **RTX 4090 24GB VRAM**

### Key Findings

| Model          | Highlight                                            |
| :------------- | :--------------------------------------------------- |
| 🏆 `gpt-oss`   | Best capability + long context (21B, 100K @ 91% GPU) |
| 🎯 `qwen3:8b`  | Most stable across all sizes (±4% variance)          |
| 💚 `gemma3:4b` | Most memory efficient (12GB @ 128K)                  |
| ⚡ `phi4-mini` | Fastest at short context, crashes beyond 64K         |

> \[!NOTE\] These results are from **aggregated runs** (multiple benchmarks averaged for reliability)

______________________________________________________________________

## 🔧 Troubleshooting

<details>
<summary><b>❌ Connection errors</b></summary>

<br>

```bash
curl http://localhost:11434/api/tags  # Check Ollama is running
```

</details>

<details>
<summary><b>🐍 Missing dependencies</b></summary>

<br>

```bash
uv pip install -r requirements.txt
```

</details>

<details>
<summary><b>🔍 Model not found</b></summary>

<br>

```bash
ollama list         # Check installed
ollama pull <model> # Install missing
```

</details>

______________________________________________________________________

## 📚 Documentation

- **This file** — Quick reference and common tasks
- **[config/README.md](config/README.md)** — Detailed configuration options
- **[config/context_matrix.yaml](config/context_matrix.yaml)** — Self-documenting matrix config

______________________________________________________________________

## 💡 Tips

> **Run `./matrix.sh --dry-run`** to preview commands before executing

**Use labels** for tracking different configurations:

```bash
./bench.sh --label "baseline" --csv results/baseline.csv -s "all"
```

**Check progress** during long runs:

```bash
tail -f results/*/ctx-*/benchmark.csv
```

______________________________________________________________________

<div align="center">

📈 Data-driven insights for model selection

[Main README](../README.md) · [Model Selection Guide](../MODEL_SELECTION_GUIDE.md) · [Charts](results/charts/)

</div>
