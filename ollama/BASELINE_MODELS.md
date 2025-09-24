# Baseline Models (Small, Local‑First)

This is the narrowed, battle‑ready shortlist (updated Sep 2025) for local inference on RTX 4090 (24GB VRAM) and MacBook
Pro M4 (24GB unified memory).

Use these to cover 90% of demo and daily needs with good speed/quality balance.

## Core (Current small SOTA)

- Reasoning: `deepseek-r1:7b` — strong open small‑model reasoning (R1 distill)
- General: `qwen3:8b-instruct` — new-gen 8B all‑rounder
- Coding: `qwen3-coder` (7B/8B if available) or fallback `qwen2.5-coder:7b-instruct`
- Speed/Efficiency: `phi4-mini:3.8b` — modern fast small model

## Optional

- Vision (smaller): `qwen2.5vl:7b` — efficient VLM
- Vision (alt): `minicpm-v:8b-2.6` — strong multimodal 2.6
- Vision (larger): `llama3.2-vision:11b-instruct`
- General (alt fast): `gemma3:4b-it` — compact general model
- Embeddings: `nomic-embed-text:v1.5` — RAG embeddings

## Notes

- Prefer Q4_K_M (or q4_0 for ultra‑small) for 7B–11B sizes
- Enable KV cache quantization (`OLLAMA_KV_CACHE_TYPE=q8_0`) and flash attention
- For 32B demos on M4 24GB, keep contexts short and only one model loaded

See also:

- RTX: `RTX_4090_OPTIMIZATION.md`
- Apple Silicon: `M4_PRO_OPTIMIZATION.md`
- Full options: `MODEL_SELECTION_GUIDE.md`
