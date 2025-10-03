# Context Window Performance Benchmarks

**Hardware:** RTX 4090 24GB VRAM | **Date:** September 30, 2025

## Executive Summary

**GPT-OSS offers the best combination of model capability and long-context efficiency on consumer hardware.**

Multiple models can technically handle 100K context (qwen3:8b, gemma3:4b both stay at 100% GPU). However:

- qwen3:8b is an 8B parameter model with limited reasoning/tool capabilities
- gemma3:4b is a 4B parameter model with even more limited capabilities
- GPT-OSS is a 21B parameter model (large & capable) that ALSO handles 100K efficiently

At 100K context:

- GPT-OSS: 152.7 t/s @ 100% GPU (21B params - large capable model)
- qwen3:8b: 119 t/s @ 100% GPU (8B params - smaller, less capable)
- gemma3:4b: 54 t/s @ 100% GPU (4B params - tiny, limited capability)
- phi4-mini/deepseek-r1: Crash to RAM (16-20 t/s)
- qwen3-coder: Falls back to CPU-only (13 t/s)

**The breakthrough: Combining large model capability WITH long context efficiency via MXFP4.**

______________________________________________________________________

## Complete Performance Matrix

| Model               | 8K          | 16K         | 32K         | 64K         | 100K           |
| ------------------- | ----------- | ----------- | ----------- | ----------- | -------------- |
| **GPT-OSS**         | **152 t/s** | **153 t/s** | **153 t/s** | **152 t/s** | **153 t/s** ✅ |
|                     | 100% GPU    | 100% GPU    | 100% GPU    | 100% GPU    | **100% GPU**   |
|                     | 15GB        | 16GB        | 17GB        | 21GB        | **24GB**       |
| **qwen3:8b**        | 122 t/s     | 121 t/s     | 121 t/s     | 120 t/s     | 119 t/s ✅     |
|                     | 100% GPU    | 100% GPU    | 100% GPU    | 100% GPU    | **100% GPU**   |
|                     | 8GB         | 10GB        | 15GB        | 18GB        | **18GB**       |
| **phi4-mini:3.8b**  | 175 t/s     | 174 t/s     | 175 t/s     | 33 t/s ⚠️   | 20 t/s ⚠️      |
|                     | 100% GPU    | 100% GPU    | 100% GPU    | 18%/82%     | **46%/54%**    |
|                     | 6GB         | 10GB        | 16GB        | 29GB        | **44GB**       |
| **deepseek-r1:8b**  | 122 t/s     | 120 t/s     | 124 t/s     | 33 t/s ⚠️   | 16 t/s ⚠️      |
|                     | 100% GPU    | 100% GPU    | 100% GPU    | 12%/88%     | **40%/60%**    |
|                     | 8GB         | 10GB        | 15GB        | 26GB        | **37GB**       |
| **gemma3:4b**       | 53 t/s      | 54 t/s      | 53 t/s      | 51 t/s      | 54 t/s ✅      |
|                     | 100% GPU    | 100% GPU    | 100% GPU    | 100% GPU    | **100% GPU**   |
|                     | 6GB         | 6GB         | 7GB         | 9GB         | **10GB**       |
| **qwen3-coder:30b** | 138 t/s     | 46 t/s ⚠️   | 24 t/s ⚠️   | 16 t/s ⚠️   | 13 t/s ❌      |
|                     | 100% GPU    | 11%/89%     | 30%/70%     | 52%/48%     | **100% CPU**   |
|                     | 23GB        | 26GB        | 34GB        | 49GB        | **38GB**       |

______________________________________________________________________

## Key Insights

### 🏆 GPT-OSS Performance Highlights

**Consistency Across All Context Sizes:**

- 8K: 152.1 t/s @ 15GB VRAM
- 16K: 153.0 t/s @ 16GB VRAM
- 32K: 152.8 t/s @ 17GB VRAM
- 64K: 152.2 t/s @ 21GB VRAM
- 100K: 152.7 t/s @ 24GB VRAM

**The Magic:** MXFP4 quantization keeps memory growth linear and manageable:

- +1GB for 16K
- +1GB for 32K
- +4GB for 64K
- +3GB for 100K

**Total memory growth: 9GB from 8K to 100K context** (vs competitors: 30-40GB)

### 🎯 Winner Categories

#### Best Capability + Context Combo: GPT-OSS

- Large 21B parameter model maintaining 150+ t/s at 100K context
- 100% GPU utilization across all context sizes
- Fits entirely in 24GB VRAM even at 100K
- Combines reasoning/tool capability with long context efficiency

#### Efficient Small Model: qwen3:8b

- 8B parameter model: 119 t/s @ 100% GPU at 100K
- Uses only 18GB VRAM at 100K
- Consistent performance, but limited reasoning/tool capabilities

#### Tiny But Reliable: gemma3:4b

- 4B parameter model: 54 t/s @ 100% GPU at 100K
- Only 10GB VRAM at 100K context
- Very limited capabilities, but handles context technically

#### Speed Demon (Short Context): phi4-mini:3.8b

- 175 t/s at 8-32K context
- Best for quick tasks with small context
- Falls apart at 64K+ (RAM spillover)

### ⚠️ Models That Struggle at Large Context

#### deepseek-r1:8b

- Great until 32K (124 t/s)
- Hits RAM at 64K: 33 t/s (12%/88% split)
- Terrible at 100K: 16 t/s (40%/60% split)

#### phi4-mini:3.8b

- Blazing fast until 32K (175 t/s)
- Crashes at 64K: 33 t/s (18%/82% split)
- Terrible at 100K: 20 t/s (46%/54% split)

#### qwen3-coder:30b

- Too large for consumer GPU
- Spills to RAM at 16K
- **CPU-only at 100K: 13 t/s** (100% CPU, 0% GPU!)
- Not viable for long context work

______________________________________________________________________

## Performance Degradation Analysis

### Context Size Impact on Speed

**GPT-OSS:** ±0.5% variance (152-153 t/s) - **FLAT LINE**

**qwen3:8b:** -2.5% degradation (122 → 119 t/s) - **MINIMAL**

**phi4-mini:3.8b:** -89% crash (175 → 20 t/s) - **CLIFF**

**deepseek-r1:8b:** -87% crash (122 → 16 t/s) - **CLIFF**

**qwen3-coder:30b:** -91% crash (138 → 13 t/s) - **CLIFF + CPU FALLBACK**

### RAM Spillover Thresholds

| Model       | Stays 100% GPU Until | Spillover Starts | Critical Point   |
| ----------- | -------------------- | ---------------- | ---------------- |
| GPT-OSS     | **100K+**            | Never            | N/A              |
| qwen3:8b    | **100K+**            | Never            | N/A              |
| gemma3:4b   | **100K+**            | Never            | N/A              |
| phi4-mini   | 32K                  | 64K (18% RAM)    | 100K (46% RAM)   |
| deepseek-r1 | 32K                  | 64K (12% RAM)    | 100K (40% RAM)   |
| qwen3-coder | 8K                   | 16K (11% RAM)    | 100K (100% CPU!) |

______________________________________________________________________

## Memory Efficiency Comparison

### VRAM Usage at 100K Context

```text
gemma3:4b       ████████░░░░░░░░░░░░░░ 10GB  (42% utilization)
qwen3:8b        ███████████████░░░░░░░ 18GB  (75% utilization)
gpt-oss         ████████████████████░░ 24GB  (100% utilization) ✅
deepseek-r1     ████████████████░░░░░░ 37GB* (154% - SPILLS TO RAM)
qwen3-coder     ████████████████░░░░░░ 38GB* (158% - CPU ONLY!)
phi4-mini       ██████████████████░░░░ 44GB* (183% - SPILLS TO RAM)

* = Total memory (RAM + VRAM)
```

### Memory Growth Rate

**Per 10K tokens added:**

- GPT-OSS: ~1GB (excellent)
- qwen3:8b: ~1.1GB (excellent)
- gemma3:4b: ~0.4GB (best)
- phi4-mini: ~4.2GB (poor)
- deepseek-r1: ~3.2GB (poor)
- qwen3-coder: ~1.7GB (acceptable, but base is too large)

______________________________________________________________________

## Real-World Use Case Recommendations

### ✅ Use GPT-OSS For

- **Complex reasoning with long context** (agentic workflows, tool use)
- Long document analysis requiring deep understanding (50K+ tokens)
- Large codebase comprehension with reasoning
- Extended conversations with full history where quality matters
- RAG with large retrieved contexts + complex queries
- When you need BOTH model capability AND long context

### ✅ Use qwen3:8b For

- Simpler tasks with long context (summaries, basic Q&A)
- Budget-conscious long context work
- Multiple concurrent workflows (lower VRAM)
- When context length matters more than reasoning depth

### ✅ Use phi4-mini:3.8b For

- Quick responses with small context (\<32K)
- High-throughput short tasks
- Multiple simultaneous small models
- Speed-critical applications

### ❌ Avoid For Long Context

- deepseek-r1:8b (RAM spillover at 64K+)
- phi4-mini:3.8b (RAM spillover at 64K+)
- qwen3-coder:30b (too large for consumer GPU)

______________________________________________________________________

## The MXFP4 Advantage

**How GPT-OSS Achieves This:**

1. **MXFP4 Quantization:**

   - 4.25 bits per parameter
   - 7.5× compression vs FP32
   - \<0.3% quality loss

2. **MoE Architecture:**

   - 21B total parameters
   - Only 3.6B active per token
   - Sparse activation = memory efficiency

3. **Optimized KV Cache:**

   - Quantized key-value cache
   - Efficient context window management
   - Native Ollama support

**Result:** 90-100K context windows on 24GB VRAM at full speed

______________________________________________________________________

## Competitive Positioning

### vs Traditional Quantization (Q4/Q5)

**qwen3:8b (Q4):** Good efficiency, handles 100K context technically, but 8B params = limited reasoning/tool capability

**deepseek-r1:8b (Q4):** Great reasoning at small context, but RAM spillover kills performance at 64K+

**phi4-mini (Q4):** Speed champion at small context, crashes hard at 64K

### vs Larger Models

**qwen3-coder:30b:** Too large even with quantization - spills to RAM immediately at 16K+, becomes CPU-only at 100K

### The Unique Combination

**What makes GPT-OSS special on RTX 4090:**

- **Not just** 100K context support (qwen3:8b and gemma3:4b can do that)
- **Not just** large model capability (qwen3-coder is larger but can't fit efficiently)
- **The combo**: 21B parameter large capable model + 100K context + 24GB fit
- Handle 100K context at 150+ t/s while maintaining reasoning/tool capabilities
- Stay 100% on GPU at 100K context WITH model capability

**GPT-OSS is unique in combining capability + context + efficiency together via MXFP4.**

______________________________________________________________________

## Testing Methodology

### Hardware Configuration

- **GPU:** NVIDIA RTX 4090 (24GB VRAM)
- **Driver:** Latest NVIDIA drivers
- **Ollama Version:** Latest stable release
- **System:** Linux with optimal GPU settings

### Test Parameters

- **Context Sizes:** 8K, 16K, 32K, 64K, 100K tokens
- **Test Prompt:** Standardized prompt for consistent comparison
- **Metrics Collected:**
  - Tokens per second (t/s)
  - VRAM usage
  - RAM usage
  - GPU utilization percentage
  - CPU utilization percentage

### Models Tested

- GPT-OSS (21B params, MXFP4 quantization)
- qwen3:8b (Q4 quantization)
- phi4-mini:3.8b (Q4 quantization)
- deepseek-r1:8b (Q4 quantization)
- gemma3:4b (Q4 quantization)
- qwen3-coder:30b (Q4 quantization)

______________________________________________________________________

## Conclusion

**GPT-OSS solves the "large capable model + long context" challenge on consumer hardware.**

Multiple models can handle 100K context technically. What's unique about GPT-OSS:

- 21B parameter model (large & capable) with reasoning/tool-use abilities
- Handles 100K context efficiently via MXFP4 quantization
- Fits in 24GB VRAM with full GPU utilization

For local AI on consumer hardware, GPT-OSS represents a breakthrough: getting model capability AND context efficiency
together. It's not about context length alone - it's about the combination.

**This benchmark demonstrates: capability + context + efficiency in 24GB VRAM.**
