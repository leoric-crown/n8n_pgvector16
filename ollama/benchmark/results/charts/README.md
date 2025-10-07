# 📊 Benchmark Charts

> **Automatically generated performance visualizations from aggregated benchmark data**

______________________________________________________________________

## 🔄 Regenerate Charts

```bash
cd ../..  # Go to benchmark directory
./visualize.sh
```

### What Happens

1. 🔍 **Discovers all benchmark runs** from `results/*/` (any timestamped directories)
2. 📊 **Averages metrics** across runs for statistical reliability
3. 🎨 **Generates visualizations:**
   - `benchmark.png` — 🎯 **Combined view:** Performance + GPU utilization in one chart
   - `memory.png` — 💾 VRAM allocation across context sizes
   - `performance.png` — ⚡ Standalone performance view (reference)
   - `summary.md` — Text summary (auto-generated, not tracked in git)

______________________________________________________________________

## ⚙️ Options

```bash
# Use specific run (no aggregation)
./visualize.sh --single-run results/20251006-012211/

# Output as SVG
./visualize.sh --format svg

# Custom output directory
./visualize.sh -o /path/to/output
```

______________________________________________________________________

## 📂 Data Source

Charts **automatically aggregate** data from:

- **All timestamped directories** in `results/` (e.g., `20251006-012211/`)
- **All context sizes** found in the data (dynamic, not hardcoded)
- **All models** present in benchmark runs

> \[!NOTE\] Context sizes and models are determined by your `config/context_matrix.yaml` configuration, not hardcoded in
> the visualization script.

### Dynamic Detection

The script automatically:

- ✅ Finds all `results/202*` directories
- ✅ Detects context sizes from subdirectory names (`ctx-8k`, `ctx-16k`, etc.)
- ✅ Discovers models from JSON data
- ✅ Adapts chart layout to number of models/contexts

______________________________________________________________________

## 📍 Used In

These charts are referenced in:

- [`../../README.md`](../../README.md) — Ollama integration overview
- [`../../../../docs/BENCHMARKS.md`](../../../../docs/BENCHMARKS.md) — Main benchmark documentation

______________________________________________________________________

## 🎨 Chart Features

| Chart               | Shows                                       | Special Markers                                       |
| :------------------ | :------------------------------------------ | :---------------------------------------------------- |
| **benchmark.png**   | Combined: Performance (top) + GPU% (bottom) | Lines stacked above 100% = full GPU, Red X = CPU-only |
| **memory.png**      | VRAM allocated (model + KV cache)           | Yellow annotation = CPU-only (RAM-only)               |
| **performance.png** | Standalone tokens/sec view                  | Red X = CPU-only fallback                             |

> \[!NOTE\] **Memory** = Total VRAM allocated for model weights + KV cache at specified context size, **not** text
> processing overhead.
>
> \[!TIP\] Charts automatically show **error bars** when multiple runs are aggregated. GPU% lines stacked above 100%
> indicate multiple models all at full GPU utilization (offset for visibility).

______________________________________________________________________

<div align="center">

🔬 Data-driven model selection

[Back to Benchmark Tools](../../README.md)

</div>
