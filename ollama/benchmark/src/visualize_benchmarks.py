#!/usr/bin/env python3
"""
Generate visual benchmark reports from JSON data.

Creates publication-quality graphs showing model performance
across different context window sizes. Aggregates data across
multiple benchmark runs for statistical reliability.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import sys
from collections import defaultdict
from statistics import mean, stdev

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.ticker import ScalarFormatter
    import seaborn as sns
except ImportError as e:
    print(f"Error: Required visualization library not installed: {e}")
    print("Install with:")
    print("  uv pip install matplotlib seaborn")
    print("  or: pip install matplotlib seaborn")
    sys.exit(1)

# Set seaborn style for beautiful charts
sns.set_theme(style="whitegrid", context="notebook", palette="husl")
sns.set_palette("husl")


def load_all_benchmark_runs(results_base: Path) -> List[Path]:
    """Find all benchmark run directories."""
    if not results_base.exists():
        return []

    # Find all timestamped result directories
    run_dirs = sorted([d for d in results_base.iterdir()
                      if d.is_dir() and d.name.startswith("202")])
    return run_dirs


def load_benchmark_data(results_dir: Path) -> Dict[str, List[dict]]:
    """Load all benchmark JSON files from a results directory."""
    data = {}

    # Find all context size subdirectories
    for ctx_dir in sorted(results_dir.glob("ctx-*")):
        json_file = ctx_dir / "benchmark.json"
        if json_file.exists():
            with open(json_file) as f:
                ctx_label = ctx_dir.name.replace("ctx-", "").replace("k", "K")
                data[ctx_label] = json.load(f)

    return data


def aggregate_runs(all_runs: List[Dict[str, List[dict]]]) -> Dict[str, List[dict]]:
    """Aggregate multiple benchmark runs, averaging metrics per model/context."""
    # Structure: {context_size: {model_name: [list of results]}}
    aggregated = defaultdict(lambda: defaultdict(list))

    # Collect all results
    for run_data in all_runs:
        for ctx_size, benchmarks in run_data.items():
            for result in benchmarks:
                model_name = result["model"]
                aggregated[ctx_size][model_name].append(result)

    # Average the metrics
    averaged = {}
    for ctx_size, models in aggregated.items():
        averaged[ctx_size] = []
        for model_name, results in models.items():
            # Helper to safely get field with fallback
            def safe_mean(field, default=0):
                values = [r.get(field, default) for r in results if field in r]
                return mean(values) if values else default

            def safe_int_mean(field, default=0):
                values = [r.get(field, default) for r in results if field in r]
                return int(mean(values)) if values else default

            # Metrics to average
            avg_result = {
                "model": model_name,
                "context_length": results[0].get("context_length", 0),
                "tokens_per_second": safe_mean("tokens_per_second"),
                "memory_gb": safe_mean("memory_gb"),
                "gpu_percent": safe_int_mean("gpu_percent", 100),
                "cpu_percent": safe_int_mean("cpu_percent", 0),
                "disk_gb": results[0].get("disk_gb", 0),
                "load_s": safe_mean("load_s"),
                "eval_s": safe_mean("eval_s"),
                "total_s": safe_mean("total_s"),
                "processor": results[0].get("processor", "Unknown"),
                "run_count": len(results),
            }

            # Add standard deviation if multiple runs
            if len(results) > 1:
                tps_values = [r["tokens_per_second"] for r in results if "tokens_per_second" in r]
                mem_values = [r["memory_gb"] for r in results if "memory_gb" in r]
                if len(tps_values) > 1:
                    avg_result["tps_stdev"] = stdev(tps_values)
                if len(mem_values) > 1:
                    avg_result["mem_stdev"] = stdev(mem_values)

            averaged[ctx_size].append(avg_result)

    return averaged


def organize_by_model(data: Dict[str, List[dict]]) -> Dict[str, Dict[str, dict]]:
    """Reorganize data by model name for easier plotting."""
    models = {}

    for ctx_size, benchmarks in data.items():
        for result in benchmarks:
            model_name = result["model"]
            if model_name not in models:
                models[model_name] = {}
            models[model_name][ctx_size] = result

    return models


def get_color_palette(num_colors: int) -> List[str]:
    """Get a consistent seaborn color palette for all charts."""
    # Use a vibrant, distinguishable palette
    if num_colors <= 6:
        return sns.color_palette("bright", n_colors=num_colors).as_hex()
    else:
        return sns.color_palette("husl", n_colors=num_colors).as_hex()


def get_model_colors(model_names: List[str]) -> Dict[str, str]:
    """Assign consistent colors to models across all charts."""
    sorted_models = sorted(model_names)
    colors = get_color_palette(len(sorted_models))
    return {model: color for model, color in zip(sorted_models, colors)}


def create_combined_plot(models: Dict[str, Dict[str, dict]], output_path: Path, color_map: Dict[str, str]):
    """Create combined performance + resource utilization plot."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), height_ratios=[2, 1])

    # Auto-detect context sizes from data
    all_ctx = set()
    for model_data in models.values():
        all_ctx.update(model_data.keys())
    ctx_order = sorted(all_ctx, key=lambda x: int(x.replace('K', '').replace('M', '000')))
    ctx_values = [int(ctx.replace('K', '').replace('M', '000')) for ctx in ctx_order]

    # Check if we have aggregated data (with stdev)
    has_stdev = any("tps_stdev" in model_data[ctx]
                    for model_data in models.values()
                    for ctx in model_data.keys())

    # ==========================
    # TOP PLOT: PERFORMANCE LINES
    # ==========================
    for model_name, model_data in sorted(models.items()):
        tokens_per_sec = []
        ctx_present = []
        error_bars = [] if has_stdev else None
        gpu_percents = []

        for ctx in ctx_order:
            if ctx in model_data:
                tokens_per_sec.append(model_data[ctx]["tokens_per_second"])
                ctx_present.append(ctx_values[ctx_order.index(ctx)])
                gpu_percents.append(model_data[ctx]["gpu_percent"])
                if has_stdev and "tps_stdev" in model_data[ctx]:
                    error_bars.append(model_data[ctx]["tps_stdev"])
                elif has_stdev:
                    error_bars.append(0)

        if tokens_per_sec:
            color = color_map[model_name]
            label = model_name.replace(":latest", "")

            if has_stdev and error_bars:
                ax1.errorbar(ctx_present, tokens_per_sec, yerr=error_bars,
                           marker='o', linewidth=3, markersize=10,
                           color=color, label=label, alpha=0.85,
                           capsize=5, capthick=2, elinewidth=2)
            else:
                ax1.plot(ctx_present, tokens_per_sec,
                        marker='o', linewidth=3, markersize=10,
                        color=color, label=label, alpha=0.85)

            # Mark CPU-only points
            for ctx_val, tps, gpu_pct in zip(ctx_present, tokens_per_sec, gpu_percents):
                if gpu_pct == 0:
                    ax1.plot(ctx_val, tps, marker='X', markersize=14,
                            color='#d62728', markeredgecolor='#8b0000', markeredgewidth=2.5,
                            zorder=10)

    ax1.set_ylabel("Tokens per Second", fontsize=14, fontweight='bold')
    title_suffix = " (aggregated)" if has_stdev else ""
    ax1.set_title(f"⚡ LLM Performance & Resource Utilization{title_suffix}\nRTX 4090 24GB VRAM",
              fontsize=18, fontweight='bold', pad=20)
    ax1.legend(fontsize=12, loc='upper right', framealpha=0.95, edgecolor='gray', ncol=2)
    ax1.set_xticks(ctx_values)
    ax1.set_xticklabels([])  # Hide x-labels on top plot
    ax1.tick_params(axis='y', labelsize=11)

    # ==========================
    # BOTTOM PLOT: GPU% LINES
    # ==========================
    # Add small offsets to separate overlapping 100% lines (stack them above 100%)
    model_list = sorted(models.keys())
    offset_per_model = {model: idx * 1.5 for idx, model in enumerate(model_list)}

    for model_name, model_data in sorted(models.items()):
        gpu_percent = []
        ctx_present = []

        for ctx in ctx_order:
            if ctx in model_data:
                pct = model_data[ctx]["gpu_percent"]
                # Add small offset for models at 100% to stack them visibly
                if pct == 100:
                    pct = 100 + offset_per_model[model_name]
                gpu_percent.append(pct)
                ctx_present.append(ctx_values[ctx_order.index(ctx)])

        if gpu_percent:
            color = color_map[model_name]
            label = model_name.replace(":latest", "")

            # Plot GPU utilization line
            ax2.plot(ctx_present, gpu_percent,
                    marker='s', linewidth=3, markersize=8,
                    color=color, label=label, alpha=0.85)

            # Mark CPU-only points (0% GPU)
            for ctx_val, gpu_pct in zip(ctx_present, gpu_percent):
                if gpu_pct == 0:
                    ax2.plot(ctx_val, gpu_pct, marker='X', markersize=14,
                            color='#d62728', markeredgecolor='#8b0000', markeredgewidth=2.5,
                            zorder=10)

    ax2.set_xlabel("Context Window Size (K tokens)", fontsize=14, fontweight='bold')
    ax2.set_ylabel("GPU Utilization %", fontsize=13, fontweight='bold')
    ax2.set_xticks(ctx_values)
    ax2.set_xticklabels(ctx_order, fontsize=11)
    ax2.set_ylim(-5, 112)  # Extended to show stacked 100% lines
    ax2.tick_params(axis='both', labelsize=11)

    # 100% reference line
    ax2.axhline(y=100, color='#2ca02c', linestyle=':', alpha=0.5, linewidth=2, zorder=0)

    # 0% reference line (CPU fallback)
    ax2.axhline(y=0, color='#d62728', linestyle='--', alpha=0.5, linewidth=2, zorder=0)
    ax2.text(max(ctx_values) * 0.98, 5, 'CPU-only fallback', fontsize=10, alpha=0.7, ha='right',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#ffe680', alpha=0.7, edgecolor='gray'))

    sns.despine(ax=ax1)
    sns.despine(ax=ax2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved: {output_path}")
    plt.close()


def create_performance_plot(models: Dict[str, Dict[str, dict]], output_path: Path, color_map: Dict[str, str]):
    """Create main performance plot: context size vs tokens/sec."""
    fig, ax = plt.subplots(figsize=(14, 8))

    # Auto-detect context sizes from data
    all_ctx = set()
    for model_data in models.values():
        all_ctx.update(model_data.keys())
    ctx_order = sorted(all_ctx, key=lambda x: int(x.replace('K', '').replace('M', '000')))
    ctx_values = [int(ctx.replace('K', '').replace('M', '000')) for ctx in ctx_order]

    # Check if we have aggregated data (with stdev)
    has_stdev = any("tps_stdev" in model_data[ctx]
                    for model_data in models.values()
                    for ctx in model_data.keys())

    # Plot each model
    for model_name, model_data in sorted(models.items()):
        tokens_per_sec = []
        ctx_present = []
        error_bars = [] if has_stdev else None
        gpu_percents = []

        for ctx in ctx_order:
            if ctx in model_data:
                tokens_per_sec.append(model_data[ctx]["tokens_per_second"])
                ctx_present.append(ctx_values[ctx_order.index(ctx)])
                gpu_percents.append(model_data[ctx]["gpu_percent"])
                if has_stdev and "tps_stdev" in model_data[ctx]:
                    error_bars.append(model_data[ctx]["tps_stdev"])
                elif has_stdev:
                    error_bars.append(0)

        if tokens_per_sec:
            color = color_map[model_name]
            # Keep model suffixes for clarity, only remove :latest
            label = model_name.replace(":latest", "")

            if has_stdev and error_bars:
                ax.errorbar(ctx_present, tokens_per_sec, yerr=error_bars,
                           marker='o', linewidth=3, markersize=10,
                           color=color, label=label, alpha=0.85,
                           capsize=5, capthick=2, elinewidth=2)
            else:
                ax.plot(ctx_present, tokens_per_sec,
                        marker='o', linewidth=3, markersize=10,
                        color=color, label=label, alpha=0.85)

            # Mark CPU-only points (severe performance degradation)
            for ctx_val, tps, gpu_pct in zip(ctx_present, tokens_per_sec, gpu_percents):
                if gpu_pct == 0:  # CPU-only fallback
                    ax.plot(ctx_val, tps, marker='X', markersize=14,
                            color='#d62728', markeredgecolor='#8b0000', markeredgewidth=2.5,
                            zorder=10)

    ax.set_xlabel("Context Window Size (K tokens)", fontsize=14, fontweight='bold')
    ax.set_ylabel("Tokens per Second", fontsize=14, fontweight='bold')

    # Title shows if aggregated
    title_suffix = " (aggregated)" if has_stdev else ""
    ax.set_title(f"⚡ LLM Performance Across Context Sizes{title_suffix}\nRTX 4090 24GB VRAM",
              fontsize=17, fontweight='bold', pad=20)

    ax.legend(fontsize=12, loc='best', framealpha=0.95, edgecolor='gray')

    # Set x-axis to match context sizes
    ax.set_xticks(ctx_values)
    ax.set_xticklabels(ctx_order, fontsize=11)
    ax.tick_params(axis='y', labelsize=11)

    sns.despine()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved: {output_path}")
    plt.close()


def create_memory_plot(models: Dict[str, Dict[str, dict]], output_path: Path, color_map: Dict[str, str]):
    """Create memory usage plot: context size vs VRAM."""
    fig, ax = plt.subplots(figsize=(14, 8))

    # Auto-detect context sizes from data
    all_ctx = set()
    for model_data in models.values():
        all_ctx.update(model_data.keys())
    ctx_order = sorted(all_ctx, key=lambda x: int(x.replace('K', '').replace('M', '000')))
    ctx_values = [int(ctx.replace('K', '').replace('M', '000')) for ctx in ctx_order]

    for model_name, model_data in sorted(models.items()):
        memory_gb = []
        ctx_present = []
        gpu_percents = []

        for ctx in ctx_order:
            if ctx in model_data:
                memory_gb.append(model_data[ctx]["memory_gb"])
                ctx_present.append(ctx_values[ctx_order.index(ctx)])
                gpu_percents.append(model_data[ctx]["gpu_percent"])

        if memory_gb:
            color = color_map[model_name]
            # Keep model suffixes for clarity, only remove :latest
            label = model_name.replace(":latest", "")

            # Plot main line
            ax.plot(ctx_present, memory_gb,
                    marker='s', linewidth=3, markersize=10,
                    color=color, label=label, alpha=0.85)

            # Mark CPU-only points with different marker
            for i, (ctx_val, mem, gpu_pct) in enumerate(zip(ctx_present, memory_gb, gpu_percents)):
                if gpu_pct == 0:  # CPU-only fallback (memory appears lower due to VRAM freed)
                    ax.plot(ctx_val, mem, marker='X', markersize=14,
                            color='#d62728', markeredgecolor='#8b0000', markeredgewidth=2.5,
                            zorder=10)
                    # Annotate CPU-only
                    ax.annotate('CPU-only\n(RAM-only)', xy=(ctx_val, mem),
                               xytext=(5, 5), textcoords='offset points',
                               fontsize=10, alpha=0.9,
                               bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffe680', alpha=0.85, edgecolor='gray'))

    ax.set_xlabel("Context Window Size (K tokens)", fontsize=14, fontweight='bold')
    ax.set_ylabel("Memory Usage (GB)", fontsize=14, fontweight='bold')
    ax.set_title("💾 VRAM Allocation vs Context Size\nRTX 4090 24GB VRAM",
              fontsize=17, fontweight='bold', pad=20)

    ax.legend(fontsize=12, loc='best', framealpha=0.95, edgecolor='gray')
    ax.set_xticks(ctx_values)
    ax.set_xticklabels(ctx_order, fontsize=11)
    ax.tick_params(axis='y', labelsize=11)

    # Add 24GB VRAM limit line
    ax.axhline(y=24, color='#d62728', linestyle='--', alpha=0.6, linewidth=2.5, zorder=0)
    ax.text(max(ctx_values) * 0.95, 25.5, '24GB VRAM limit', fontsize=11, alpha=0.85, ha='right',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.7, edgecolor='none'))

    sns.despine()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved: {output_path}")
    plt.close()


def create_efficiency_plot(models: Dict[str, Dict[str, dict]], output_path: Path, color_map: Dict[str, str]):
    """Create efficiency plot: memory vs performance."""
    fig, ax = plt.subplots(figsize=(14, 8))

    # Auto-detect context sizes
    all_ctx = set()
    for model_data in models.values():
        all_ctx.update(model_data.keys())
    ctx_order = sorted(all_ctx, key=lambda x: int(x.replace('K', '').replace('M', '000')))

    for model_name, model_data in sorted(models.items()):
        for ctx in ctx_order:
            if ctx in model_data:
                result = model_data[ctx]
                memory = result["memory_gb"]
                tps = result["tokens_per_second"]
                gpu_pct = result["gpu_percent"]

                color = color_map[model_name]

                # Size represents context size
                size = 150 + (ctx_order.index(ctx) * 150)

                # Alpha based on GPU usage (dimmer if using RAM)
                alpha = 0.85 if gpu_pct == 100 else 0.35

                # Mark CPU-only with red edge
                edge_color = '#d62728' if gpu_pct == 0 else 'white'
                edge_width = 3 if gpu_pct == 0 else 1.5

                ax.scatter(memory, tps, s=size, c=[color], alpha=alpha,
                           edgecolors=edge_color, linewidths=edge_width, zorder=5)

    # Create custom legend
    legend_elements = []
    for model_name in sorted(models.keys()):
        color = color_map[model_name]
        # Keep model suffixes for clarity, only remove :latest
        label = model_name.replace(":latest", "")
        legend_elements.append(mpatches.Patch(color=color, label=label))

    ax.set_xlabel("Memory Usage (GB)", fontsize=14, fontweight='bold')
    ax.set_ylabel("Tokens per Second", fontsize=14, fontweight='bold')
    ax.set_title("⚖️ Performance Efficiency: Memory vs Speed\nBubble size = context window | Dim = RAM spillover",
              fontsize=17, fontweight='bold', pad=20)

    ax.legend(handles=legend_elements, fontsize=12, loc='best', framealpha=0.95, edgecolor='gray')
    ax.tick_params(axis='both', labelsize=11)

    # Add 24GB vertical line
    ax.axvline(x=24, color='#d62728', linestyle='--', alpha=0.6, linewidth=2.5, zorder=0)
    ax.text(24.5, ax.get_ylim()[1]*0.95, '24GB VRAM limit', fontsize=11, alpha=0.85,
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.7, edgecolor='none'))

    sns.despine()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved: {output_path}")
    plt.close()


def create_gpu_utilization_plot(models: Dict[str, Dict[str, dict]], output_path: Path, color_map: Dict[str, str]):
    """Create GPU utilization stacked bar chart."""
    fig, ax = plt.subplots(figsize=(14, 8))

    # Auto-detect context sizes
    all_ctx = set()
    for model_data in models.values():
        all_ctx.update(model_data.keys())
    ctx_order = sorted(all_ctx, key=lambda x: int(x.replace('K', '').replace('M', '000')))

    # Use all models found in data (sorted for consistency)
    model_order = sorted(models.keys())

    # Prepare data
    gpu_data = {model: [] for model in model_order}
    cpu_data = {model: [] for model in model_order}

    for model in model_order:
        for ctx in ctx_order:
            if ctx in models[model]:
                gpu_data[model].append(models[model][ctx]["gpu_percent"])
                cpu_data[model].append(models[model][ctx]["cpu_percent"])
            else:
                gpu_data[model].append(0)
                cpu_data[model].append(0)

    # Bar positions
    x = range(len(ctx_order))
    width = 0.8 / len(model_order)  # Dynamic width based on number of models

    for i, model in enumerate(model_order):
        offset = (i - len(model_order)/2) * width + width/2
        positions = [p + offset for p in x]

        # Keep model suffixes for clarity, only remove :latest
        label = model.replace(":latest", "")
        color = color_map[model]

        # GPU portion (bottom)
        ax.bar(positions, gpu_data[model], width, label=label,
               color=color, alpha=0.85, edgecolor='white', linewidth=1)

        # CPU portion (top) - only if present
        if any(cpu_data[model]):
            ax.bar(positions, cpu_data[model], width, bottom=gpu_data[model],
                   color=color, alpha=0.3, hatch='///', edgecolor='white', linewidth=1)

    ax.set_xlabel("Context Window Size", fontsize=14, fontweight='bold')
    ax.set_ylabel("GPU Utilization %", fontsize=14, fontweight='bold')
    ax.set_title("🔧 GPU vs RAM Utilization Across Context Sizes\nHatched = RAM spillover",
                 fontsize=17, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(ctx_order, fontsize=11)
    ax.set_ylim(0, 105)
    ax.tick_params(axis='both', labelsize=11)
    ax.legend(fontsize=12, loc='lower left', framealpha=0.95, edgecolor='gray')

    # Add 100% reference line
    ax.axhline(y=100, color='#2ca02c', linestyle=':', alpha=0.5, linewidth=2, zorder=0)
    ax.text(0.02, 102, '100% GPU', fontsize=10, alpha=0.6,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='none'))

    sns.despine()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved: {output_path}")
    plt.close()


def generate_summary_stats(models: Dict[str, Dict[str, dict]], run_count: int = 1) -> str:
    """Generate text summary of key findings."""
    lines = []
    lines.append("# Benchmark Summary\n\n")

    # Add metadata
    if run_count > 1:
        lines.append(f"**Data aggregated from {run_count} benchmark runs** (averaged metrics)\n\n")
    else:
        lines.append("**Single benchmark run**\n\n")

    lines.append("**Hardware:** RTX 4090 24GB VRAM\n\n")
    lines.append("---\n\n")

    # Find best performers at 100K
    if any("100K" in m for m in models.values()):
        lines.append("## Top Performers at 100K Context\n\n")
        performers_100k = []
        for model_name, data in models.items():
            if "100K" in data and data["100K"]["gpu_percent"] >= 90:
                tps = data["100K"]["tokens_per_second"]
                mem = data["100K"]["memory_gb"]
                gpu_pct = data["100K"]["gpu_percent"]
                performers_100k.append((model_name, tps, mem, gpu_pct))

        performers_100k.sort(key=lambda x: x[1], reverse=True)
        for model, tps, mem, gpu_pct in performers_100k[:3]:
            stdev_info = ""
            if "100K" in models[model] and "tps_stdev" in models[model]["100K"]:
                stdev = models[model]["100K"]["tps_stdev"]
                stdev_info = f" (±{stdev:.1f})"
            lines.append(f"- **{model}**: {tps:.1f}{stdev_info} t/s @ {mem:.1f}GB VRAM ({gpu_pct}% GPU)\n")

    lines.append("\n## Memory Efficiency\n\n")
    for model_name, data in models.items():
        if "8K" in data and "100K" in data:
            mem_8k = data["8K"]["memory_gb"]
            mem_100k = data["100K"]["memory_gb"]
            growth = mem_100k - mem_8k
            lines.append(f"- **{model_name}**: {mem_8k:.1f}GB → {mem_100k:.1f}GB (+{growth:.1f}GB growth)\n")

    lines.append("\n## Performance Stability\n\n")
    for model_name, data in models.items():
        ctx_sizes = ["8K", "16K", "32K", "64K", "100K"]
        tps_values = [data[ctx]["tokens_per_second"] for ctx in ctx_sizes if ctx in data]
        if len(tps_values) >= 3:
            min_tps = min(tps_values)
            max_tps = max(tps_values)
            variance_pct = ((max_tps - min_tps) / max_tps * 100) if max_tps > 0 else 0
            if variance_pct < 10:
                stability = "Excellent"
            elif variance_pct < 30:
                stability = "Good"
            else:
                stability = "Poor"
            lines.append(f"- **{model_name}**: {stability} ({variance_pct:.1f}% variance)\n")

    return "".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark visualizations")
    parser.add_argument("results_dir", type=Path, nargs="?",
                       help="Path to benchmark results directory (e.g., results/20251006-012211) or results base directory")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("results/charts"),
                       help="Output directory for charts (default: results/charts)")
    parser.add_argument("--format", choices=["png", "svg", "pdf"], default="png",
                       help="Output format (default: png)")
    parser.add_argument("--aggregate", action="store_true", default=True,
                       help="Aggregate all benchmark runs (default: True)")
    parser.add_argument("--single-run", action="store_true",
                       help="Use only single/latest run instead of aggregating")

    args = parser.parse_args()

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Determine if we're aggregating or using single run
    use_aggregate = args.aggregate and not args.single_run

    # Find results directories
    if not args.results_dir:
        results_base = Path(__file__).parent / "results"
    else:
        results_base = args.results_dir
        # If given a specific run directory, use its parent
        if args.results_dir.name.startswith("202"):
            results_base = args.results_dir.parent

    if not results_base.exists():
        print("Error: No results directory found")
        return 1

    # Load data
    run_count = 1  # Track number of runs

    if use_aggregate:
        # Load ALL runs and aggregate
        run_dirs = load_all_benchmark_runs(results_base)
        if not run_dirs:
            print("Error: No benchmark result directories found")
            return 1

        print(f"\nAggregating data from {len(run_dirs)} benchmark runs:")
        for run_dir in run_dirs:
            print(f"  - {run_dir.name}")

        all_runs = []
        for run_dir in run_dirs:
            run_data = load_benchmark_data(run_dir)
            if run_data:
                all_runs.append(run_data)

        if not all_runs:
            print("Error: No benchmark data found in any run")
            return 1

        print(f"\nAggregating {len(all_runs)} runs...")
        data = aggregate_runs(all_runs)
        run_count = len(all_runs)
        print(f"✓ Averaged metrics across {run_count} runs")
    else:
        # Use single/latest run
        if args.results_dir and args.results_dir.name.startswith("202"):
            result_dir = args.results_dir
        else:
            result_dirs = load_all_benchmark_runs(results_base)
            if not result_dirs:
                print("Error: No benchmark result directories found")
                return 1
            result_dir = result_dirs[-1]

        print(f"\nUsing single run: {result_dir.name}")
        data = load_benchmark_data(result_dir)
        if not data:
            print("Error: No benchmark data found")
            return 1

    print(f"Found {len(data)} context sizes: {', '.join(data.keys())}")

    models = organize_by_model(data)
    print(f"Found {len(models)} models: {', '.join(models.keys())}")

    # Create consistent color mapping for all charts
    color_map = get_model_colors(list(models.keys()))

    # Generate plots
    print("\nGenerating visualizations...")

    # Single combined chart tells the complete story
    create_combined_plot(models, args.output_dir / f"benchmark.{args.format}", color_map)

    # Also keep separate charts for reference
    create_performance_plot(models, args.output_dir / f"performance.{args.format}", color_map)
    create_memory_plot(models, args.output_dir / f"memory.{args.format}", color_map)

    # Generate summary
    summary_path = args.output_dir / "summary.md"
    with open(summary_path, "w") as f:
        f.write(generate_summary_stats(models, run_count))
    print(f"✓ Saved: {summary_path}")

    print(f"\n✅ Complete! Charts saved to: {args.output_dir}")
    print(f"\nUse in docs with:")
    print(f"  ![Performance]({args.output_dir / f'performance.{args.format}'})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
