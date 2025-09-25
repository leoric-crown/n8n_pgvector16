# Baseline Models (Small, Local-First)

This is a narrowed, battle-ready shortlist (updated Sep 2025) for local inference on 24GB systems.

Use these models to cover 90% of demo and daily needs with a good balance of speed and quality. For more options, see
the full [Model Selection Guide](./MODEL_SELECTION_GUIDE.md).

## Quick Start

- **Reasoning**: `deepseek-r1:8b` (~5.2GB on disk)
  - Strong open small-model reasoning.
- **General**: `qwen3:8b` (~5.2GB on disk)
  - New-generation 8B parameter all-rounder.
- **Coding**: `qwen3-coder` (~19GB on disk)
  - Current coding-specific family; smallest size is 30B, you may need to try `qwen2.5-coder` due to context window
    constraints on consumer hardware.
- **Speed/Efficiency**: `phi4-mini:3.8b` (~2.5GB on disk)
  - A modern, fast, and very small model for quick tasks.

## Notes

- For most models in the 7B-11B range, the `q4_K_M` quantization offers the best balance of performance and quality.
- For optimal performance, ensure Flash Attention and KV cache quantization are enabled in your environment. See
  [Ollama Integration Guide](./OLLAMA_INTEGRATION.md) for tuning scripts.
