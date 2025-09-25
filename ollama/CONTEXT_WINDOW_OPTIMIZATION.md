# LLM Context Window Optimization Guide

Context window size dramatically affects VRAM and memory usage through KV cache scaling. Understanding this is essential
for optimal model deployment on any hardware. This guide covers the mechanics, platform-specific limits, and best
practices for managing context.

## ⚠️ Critical Consideration: KV Cache

The Key-Value (KV) cache stores the computed state of tokens in the input prompt, so the model doesn't have to
re-calculate them for each new token it generates. This is why initial prompt processing is slow, and subsequent token
generation is faster.

However, this cache grows linearly with the number of input tokens and can consume a massive amount of memory, often
more than the model weights themselves.

### 📊 KV Cache Memory Scaling Formula

```text
Total Memory = Model_Weights + KV_Cache + System_Overhead

KV_Cache = Context_Length × Model_Scaling_Factor × KV_Precision_Factor
System_Overhead = ~10-15% of total usage
```

### 🎯 Context Window Memory Impact by Model Size

#### **7B Models - Memory per 1k Tokens:**

- **F16 KV Cache**: ~0.28GB per 1k tokens
- **Q8 KV Cache**: ~0.14GB per 1k tokens (50% savings)
- **Q4 KV Cache**: ~0.07GB per 1k tokens (75% savings)

#### **13B Models - Memory per 1k Tokens:**

- **F16 KV Cache**: ~0.52GB per 1k tokens
- **Q8 KV Cache**: ~0.26GB per 1k tokens (50% savings)
- **Q4 KV Cache**: ~0.13GB per 1k tokens (75% savings)

#### **32B Models - Memory per 1k Tokens:**

- **F16 KV Cache**: ~1.28GB per 1k tokens
- **Q8 KV Cache**: ~0.64GB per 1k tokens (50% savings)
- **Q4 KV Cache**: ~0.32GB per 1k tokens (75% savings)

### 🚨 Practical Context Limits for 24GB Systems

These are estimates and can vary based on the specific model and quantization.

| Model Size     | Conservative (22GB) | Optimized (Q8 KV) | Aggressive (Q4 KV) |
| -------------- | ------------------- | ----------------- | ------------------ |
| **7B Models**  | 32k tokens          | 64k tokens        | 128k tokens        |
| **13B Models** | 16k tokens          | 32k tokens        | 64k tokens         |
| **32B Models** | 4k tokens           | 8k tokens         | 16k tokens         |

### ⚙️ Context Window Optimization Configuration

#### **Essential Ollama Settings:**

```bash
# Enable KV cache quantization (50% memory savings)
export OLLAMA_KV_CACHE_TYPE="q8_0"

# Enable Flash Attention (up to 40% additional memory savings on long context)
export OLLAMA_FLASH_ATTENTION=1

# Monitor memory usage
export OLLAMA_DEBUG=1
```

#### **Memory Monitoring Commands:**

```bash
# NVIDIA GPU memory usage
nvidia-smi --query-gpu=memory.used,memory.total

# Check Ollama model memory usage
ollama ps

# Monitor in real-time
# Option 1: htop-like monitoring for system resources, includes a GPU section
# Works on both Linux and MacOS (brew install btop)
btop
# Option 2: htop-like monitoring for GPU resources
# Works on both Linux and MacOS (brew install nvtop)
nvtop
```

Or use your OS's native system monitor tools.

### 💡 Context Window vs Performance Trade-offs

#### **Memory Pressure Indicators:**

- GPU utilization drops below 80%
- Token generation speed decreases >25%
- CUDA out-of-memory errors (NVIDIA)
- System starts using swap memory (high memory pressure on Apple Silicon macOS, or overlow from GPU to CPU on
  traiditional systems)

#### **Real-World Performance Impact:**

| Context Size   | 7B Model Speed | 13B Model Speed | 32B Model Speed |
| -------------- | -------------- | --------------- | --------------- |
| **2k tokens**  | 50-60 tok/s    | 35-45 tok/s     | 15-20 tok/s     |
| **16k tokens** | 45-55 tok/s    | 25-35 tok/s     | 8-12 tok/s      |
| **32k tokens** | 35-45 tok/s    | 15-25 tok/s     | Not feasible    |
| **64k tokens** | 25-35 tok/s    | Memory limit    | Memory limit    |

### 🔧 Platform-Specific Context Window Handling

#### **RTX 4090 Characteristics:**

- **Hard VRAM Limit**: 24GB with a sharp performance cliff if exceeded.
- **Optimal Strategy**: Aggressive KV cache quantization (`q8_0` or lower).
- **Best Context Ranges**:
  - 7B models: Up to 64k tokens
  - 13B models: Up to 32k tokens
  - 32B models: Up to 8k tokens

#### **Apple Silicon M4 Pro Characteristics:**

- **Unified Memory**: There is no distinction between system and GPU RAM, so filling memory can cause considerable
  system degradation
- **Higher Context Tolerance**: High memory pressure degrades performance of the model and of the whole system.
- **Best Context Ranges**:
  - 7B models: Up to 128k tokens
  - 13B models: Up to 64k tokens
  - 32B models: Up to 16k tokens

### 🛠️ Advanced Context Window Techniques

#### **1. Dynamic Context Management**

Use application logic to set the context size (`num_ctx`) based on the model being used.

```javascript
// Example n8n Function node for dynamic context sizing
const maxTokens = {
  '7b': 32000,
  '13b': 16000,
  '32b': 4000
};

const modelSize = $json.model.includes('32b') ? '32b' :
                  $json.model.includes('13b') ? '13b' : '7b';

return [{
  model: $json.model,
  prompt: $json.prompt,
  options: {
    num_ctx: maxTokens[modelSize]
  }
}];
```

#### **2. Context Window Monitoring**

Monitor ollama logs for:

```text
Sep 24 17:49:19 hostname ollama[1264933]: time=2025-09-24T17:49:19.543-06:00 level=WARN source=runner.go:159 msg="truncating input prompt" limit=8192 prompt=11861 keep=4 new=8192
```

### ⚡ Flash Attention Memory Savings

Flash Attention provides non-linear memory savings that become more significant as context length increases.

| Context Length | Standard Memory | Flash Attention | Savings |
| -------------- | --------------- | --------------- | ------- |
| **8k tokens**  | 100%            | 95%             | 5%      |
| **16k tokens** | 100%            | 85%             | 15%     |
| **32k tokens** | 100%            | 75%             | 25%     |
| **64k tokens** | 100%            | 60%             | 40%     |

**Enable Flash Attention (`OLLAMA_FLASH_ATTENTION=1`) whenever possible!**
