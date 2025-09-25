# Local LLM Model Selection Guide

Principles and a quick process to pick, size, and validate local models with Ollama. This guide favors durable
heuristics over one-off recommendations.

## How To Choose (Checklist)

- Define task: chat/assistant, coding, reasoning, vision, multilingual, embeddings.
- Set constraints: latency target, context length, offline requirement, memory (VRAM/unified).
- Shortlist 2–4 candidate families matching the task (e.g., instruct vs coder vs vision).
- Pick a starting quantization that fits memory; plan one up/down step for trade-offs.
- Test on your own prompts; compare output quality, latency, and memory headroom.

## Quick Evaluation Loop

1. Inspect a candidate

```bash
ollama show <model>
```

- Check parameters, quantization, and context window.

2. Pull and run

```bash
ollama pull <model>
ollama run <model>
```

- Use a representative prompt (for coding: paste a real snippet; for RAG: use a typical question; for multilingual:
  include target languages).

3. Compare latency and quality

- Time a fixed prompt/response across models; keep prompts and temperature equal.
- Inspect factuality, format adherence, and failure modes relevant to your task.

4. Check memory headroom

- Monitor system GPU/CPU memory during inference and while increasing context length.
- Leave margin for KV cache growth and other processes; if near limits, try a smaller model or lower-bit quantization.

## Sizing Rules of Thumb

- 3B–7B: fastest and lightest; good for simple chat, routing, light code assistance.
- 8B–13B: balanced quality/speed for many on-device assistants and coding tasks.
- 30B+: higher quality but heavier; often requires 4–5 bit quantization locally.
- Long context increases KV cache memory linearly with tokens; plan margin accordingly.

Use families aligned with the task: “instruct” for chat/assistants, “coder” for code, “vision/multimodal” for images,
dedicated “embed” models for RAG.

## Quantization Basics

- Higher bits (e.g., q6/q5): larger memory, higher fidelity, slower.
- Mid bits (e.g., q4_K): strong default for many 24GB-class systems.
- Ultra-low bits (e.g., iq2/iq3): smallest memory, noticeable quality loss; use only if constrained.

Start at a mid setting (q4_K) that fits memory. If quality isn’t sufficient, step up; if you need more headroom or
speed, step down.

## Context Window and KV Cache

Token context drives KV cache memory and latency. Managing this is often more impactful than switching models. See:

- [LLM Context Window Optimization Guide](./CONTEXT_WINDOW_OPTIMIZATION.md)

## Where To Browse Models and Compare

- Prefer recent “instruct/coder/vision/embed” variants from well-maintained families.
- Check model cards for intended use, license, context length, and eval notes.
- Use external leaderboards and blog posts to shortlist, then validate locally on your prompts.

For a small, evolving shortlist maintained in this repo, see:

- [Baseline Models](./BASELINE_MODELS.md)

## 2025 Snapshot: Families To Explore

Examples to start your shortlist (verify locally on your prompts):

- General/Multilingual: Qwen3 (e.g., `qwen3`) — <https://ollama.com/library/qwen3>
- Coding: Qwen3 Coder (e.g., `qwen3-coder`) — <https://ollama.com/library/qwen3-coder>
- Vision: Llama 3.2 Vision (e.g., `llama3.2-vision:11b`) — <https://ollama.com/blog/llama3.2-vision>
- Efficient assistants: Gemma 3 (e.g., `gemma3:4b`) — <https://ollama.com/library/gemma3:4b>
- Reasoning focus: DeepSeek R1 (e.g., `deepseek-r1:8b/32b`) — <https://ollama.com/library/deepseek-r1>
- Small + fast: Phi‑4 mini (e.g., `phi4-mini:3.8b`) — <https://ollama.com/library/phi4-mini>
- Embeddings: BGE-M3 (`bge-m3`) — <https://ollama.com/library/bge-m3>; Nomic Embed Text (`nomic-embed-text`) —
  <https://ollama.com/library/nomic-embed-text>

## See Also

- [Ollama Integration Guide](./OLLAMA_INTEGRATION.md)
