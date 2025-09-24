# Local LLM Model Selection Guide (Q3-Q4 2025)

Comprehensive guide to selecting the most resource-effective LLM models for RTX 4090 24GB and Apple Silicon M4 Pro 24GB
hardware.

## Quick Reference: Top Models by Use Case

### 🥇 **Best Overall Models (September 2025)**

| Use Case      | Model                 | Size | RTX 4090 Perf | M4 Pro Perf  | Memory | Quality |
| ------------- | --------------------- | ---- | ------------- | ------------ | ------ | ------- |
| **Reasoning** | DeepSeek R1-7B        | 7B   | 50-60 tok/s   | 42-52 tok/s  | 8GB    | 95/100  |
| **Coding**    | Qwen2.5-Coder-7B      | 7B   | 45-55 tok/s   | 45-58 tok/s  | 6.3GB  | 88/100  |
| **General**   | Llama 3.2-8B          | 8B   | 42-52 tok/s   | 42-52 tok/s  | 4.5GB  | 90/100  |
| **Speed**     | Phi-3.5-3.8B          | 3.8B | 65-80 tok/s   | 60-75 tok/s  | 3GB    | 85/100  |
| **Vision**    | Llama 3.2-Vision-11B  | 11B  | 25-35 tok/s   | 20-30 tok/s  | 12GB   | 92/100  |
| **Embedding** | nomic-embed-text-v1.5 | 137M | 2000+ docs/s  | 1500+ docs/s | 0.8GB  | 62/100  |
| **Maximum**   | DeepSeek R1-32B       | 32B  | 10-15 tok/s   | 15-25 tok/s  | 20GB   | 98/100  |

## September 2025 Model Breakthroughs

### 🚀 **DeepSeek R1 Distilled Series**

**Release Date**: September 2025 **Key Innovation**: First open-source model matching OpenAI-o1 performance

#### Available Sizes

- **R1-Distill-1.5B**: Browser-compatible, 1.28GB memory
- **R1-Distill-7B**: Sweet spot for most users, 8GB memory
- **R1-Distill-8B**: Balanced performance, 8.5GB memory
- **R1-Distill-14B**: High capability, 12GB memory
- **R1-Distill-32B**: Maximum reasoning, 20GB memory
- **R1-Distill-70B**: Enterprise-grade, requires RAM offload

#### Performance Highlights

- **Reasoning**: Comparable to GPT-4 in mathematical problem-solving
- **Code Generation**: Superior debugging and complex algorithm implementation
- **Temperature Settings**: 0.5-0.7 optimal (no system prompts needed)
- **Quantization**: Handles Q4_K_M with minimal quality loss

### 📚 **Qwen2.5/Qwen3 Series Evolution**

**Latest Release**: Qwen3 Preview (October 2025 expected)

#### Qwen2.5 Current Champions

- **Qwen2.5-Coder-7B**: 88.4% HumanEval (beats GPT-4's 87.1%)
- **Qwen2.5-14B**: Excellent general-purpose reasoning
- **Qwen2.5-32B**: High-capability model for complex tasks

#### Qwen3 Improvements (Preview)

- **36 trillion tokens** training (2x improvement over Qwen2.5)
- **119 languages** with enhanced multilingual capabilities
- **15-20% performance improvements** across benchmarks

## Model Selection Matrix

### By Hardware Platform

#### RTX 4090 24GB Optimal Configurations

### Configuration A: Multi-Model Development

```bash
DeepSeek R1-7B (8GB) + Qwen2.5-Coder-7B (6.3GB) + Phi-3.5 (3GB) = 17.3GB
```

- Reasoning + Coding + Speed specialized models
- Leaves 6.7GB for context and system overhead

### Configuration B: Balanced Power

```bash
DeepSeek R1-14B (12GB) + Qwen2.5-Coder-7B (6.3GB) = 18.3GB
```

- Enhanced reasoning with efficient coding support
- Leaves 5.7GB for context

### Configuration C: Maximum Single Model

```bash
DeepSeek R1-32B (20GB)
```

- Ultimate reasoning capability
- Best for complex problem-solving tasks

#### Apple Silicon M4 Pro 24GB Optimal Configurations

### Energy Efficient Setup

```bash
Llama 3.2-8B (4.5GB) + Qwen2.5-Coder-7B (4.2GB) + Phi-3.5 (3GB) = 11.7GB
```

- Excellent battery life with high performance
- Leaves 12GB for system operations

### High Performance Setup

```bash
DeepSeek R1-32B (19GB) + Phi-3.5 (3GB) = 22GB
```

- Maximum reasoning with quick response backup
- Optimal for intensive research work

### By Use Case Priority

#### 🔬 **Research & Reasoning**

1. **DeepSeek R1-32B**: Maximum capability, complex problem solving
2. **DeepSeek R1-14B**: Balanced reasoning power
3. **Llama 3.2-8B**: General reasoning with broader knowledge
4. **Mixtral 8x7B**: MoE efficiency for complex tasks

#### 💻 **Code Development**

1. **Qwen2.5-Coder-7B**: Best tokens/sec per GB, 88.4% HumanEval
2. **DeepSeek-Coder-V2-16B**: Broad language support (338 languages)
3. **CodeLlama-13B**: Meta's specialized coding model
4. **Phi-3.5**: Lightweight coding for simple tasks

#### ⚡ **Speed & Efficiency**

1. **Phi-3.5-3.8B**: 60-80 tokens/sec, excellent small model
2. **Qwen2.5-7B**: Fast multilingual performance
3. **Gemma2-9B**: Google's efficient architecture
4. **Mistral-7B**: Proven efficiency champion

#### 🌐 **Multilingual & International**

1. **Qwen2.5 Series**: 119+ languages supported
2. **Llama 3.2**: Strong multilingual base
3. **Gemma2**: Google's international optimization
4. **Yi-34B**: Chinese-English bilingual excellence

#### 👁️ **Vision-Enabled Models**

1. **Llama 3.2-Vision-11B**: Meta's multimodal flagship, excellent image understanding
2. **Qwen2-VL-7B**: Strong vision-language performance, 7B efficiency
3. **Gemma2-VIT-9B**: Google's vision-text integration
4. **MiniCPM-V-2.6**: Efficient vision model, 8B parameters

#### 🔍 **Embedding Models for RAG**

1. **nomic-embed-text-v1.5**: 768 dimensions, excellent retrieval performance
2. **bge-large-en-v1.5**: BAAI's top English embedding model
3. **multilingual-e5-large**: Cross-lingual embedding capabilities
4. **all-MiniLM-L6-v2**: Lightweight, fast embedding generation

## ⚠️ Context Window Memory Usage - CRITICAL CONSIDERATIONS

Context window size dramatically affects VRAM/memory usage through KV cache scaling. Understanding this is essential for
optimal model deployment.

### 📊 **KV Cache Memory Scaling Formula**

```text
Total Memory = Model_Weights + KV_Cache + System_Overhead

KV_Cache = Context_Length × Model_Scaling_Factor × KV_Precision_Factor
System_Overhead = ~10-15% of total usage
```

### 🎯 **Context Window Memory Impact by Model Size**

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

### 🚨 **Practical Context Limits for 24GB Systems**

| Model Size     | Conservative (22GB) | Optimized (Q8 KV) | Aggressive (Q4 KV) |
| -------------- | ------------------- | ----------------- | ------------------ |
| **7B Models**  | 32k tokens          | 64k tokens        | 128k tokens        |
| **13B Models** | 16k tokens          | 32k tokens        | 64k tokens         |
| **32B Models** | 4k tokens           | 8k tokens         | 16k tokens         |

### ⚙️ **Context Window Optimization Configuration**

#### **Essential Ollama Settings:**

```bash
# Enable KV cache quantization (50% memory savings)
export OLLAMA_KV_CACHE_TYPE="q8_0"

# Enable Flash Attention (20-30% additional savings)
export OLLAMA_FLASH_ATTENTION=1

# Monitor memory usage
export OLLAMA_DEBUG=1
```

#### **Memory Monitoring Commands:**

```bash
# Check GPU memory usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# Check Ollama model memory usage
ollama ps

# Monitor in real-time
watch -n 2 'nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader'
```

### 💡 **Context Window vs Performance Trade-offs**

#### **Memory Pressure Indicators:**

- GPU utilization drops below 80%
- Token generation speed decreases >25%
- CUDA out-of-memory errors
- System starts using CPU/swap memory

#### **Real-World Performance Impact:**

| Context Size   | 7B Model Speed | 13B Model Speed | 32B Model Speed |
| -------------- | -------------- | --------------- | --------------- |
| **2k tokens**  | 50-60 tok/s    | 35-45 tok/s     | 15-20 tok/s     |
| **16k tokens** | 45-55 tok/s    | 25-35 tok/s     | 8-12 tok/s      |
| **32k tokens** | 35-45 tok/s    | 15-25 tok/s     | Not feasible    |
| **64k tokens** | 25-35 tok/s    | Memory limit    | Memory limit    |

### 🔧 **Platform-Specific Context Window Handling**

#### **RTX 4090 Characteristics:**

- **Hard VRAM Limit**: 24GB with sharp performance cliff
- **Optimal Strategy**: Aggressive KV cache quantization
- **Best Context Ranges**:
  - 7B models: Up to 64k tokens
  - 13B models: Up to 32k tokens
  - 32B models: Up to 8k tokens

#### **Apple Silicon M4 Pro Characteristics:**

- **Unified Memory**: Graceful overflow to system RAM
- **Higher Context Tolerance**: Better handling of very long contexts
- **Best Context Ranges**:
  - 7B models: Up to 128k tokens
  - 13B models: Up to 64k tokens
  - 32B models: Up to 16k tokens

### 🛠️ **Advanced Context Window Techniques**

#### **1. Dynamic Context Management**

```javascript
// n8n Function node for dynamic context sizing
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

#### **2. Conversation Summarization Pattern**

```bash
# Long conversation management workflow
# 1. Check context length
# 2. Summarize old messages when approaching limit
# 3. Keep last N messages + summary
```

#### **3. Context Window Monitoring**

```bash
# Real-time context tracking script
#!/bin/bash
CONTEXT_THRESHOLD=30000  # Warning at 30k tokens

while true; do
    CURRENT_CONTEXT=$(curl -s http://localhost:11434/api/ps | jq '.models[0].context_length')
    if [ "$CURRENT_CONTEXT" -gt "$CONTEXT_THRESHOLD" ]; then
        echo "WARNING: Context length approaching limit: $CURRENT_CONTEXT tokens"
    fi
    sleep 5
done
```

### 🎯 **Context Window Best Practices**

#### **For Long Document Analysis:**

1. **Use 7B models** with Q8 KV cache quantization
2. **Enable Flash Attention** for memory efficiency
3. **Implement chunking** for documents >32k tokens
4. **Monitor memory usage** continuously

#### **For Conversational AI:**

1. **Implement conversation summarization** at 75% context limit
2. **Use graduated context limits** based on model size
3. **Cache important context** separately from conversation history
4. **Monitor token usage** per conversation turn

#### **For Code Generation:**

1. **Use appropriate context** for codebase size
2. **Implement semantic chunking** for large codebases
3. **Balance context window** vs response quality
4. **Consider RAG** for very large codebases instead of full context

### ⚡ **Flash Attention Memory Savings**

Flash Attention provides exponentially better memory scaling:

| Context Length | Standard Memory | Flash Attention | Savings |
| -------------- | --------------- | --------------- | ------- |
| **8k tokens**  | 100%            | 95%             | 5%      |
| **16k tokens** | 100%            | 85%             | 15%     |
| **32k tokens** | 100%            | 75%             | 25%     |
| **64k tokens** | 100%            | 60%             | 40%     |

**Enable Flash Attention everywhere possible!**

## Quantization Strategy Guide

### Performance vs Quality Trade-offs

| Quantization | Memory Reduction | Quality Loss | RTX 4090 Speed | M4 Pro Speed |
| ------------ | ---------------- | ------------ | -------------- | ------------ |
| **Q8_0**     | 2x               | \<2%         | Baseline       | Baseline     |
| **Q6_K**     | 2.7x             | 3-5%         | +10%           | +8%          |
| **Q5_K_M**   | 3.2x             | 5-8%         | +15%           | +12%         |
| **Q4_K_M**   | 4x               | 8-12%        | +25%           | +20%         |
| **Q4_K_S**   | 4.2x             | 12-18%       | +30%           | +25%         |
| **IQ2**      | 8x               | 25-35%       | +60%           | +50%         |

### Quantization Recommendations by Model

#### DeepSeek R1 Series

- **Q4_K_M**: Recommended for most users (8-12% quality loss)
- **Q5_K_M**: Higher quality for critical applications
- **Q6_K**: Near-original quality for production use

#### Qwen2.5 Coder Series

- **Q4_K_M**: Maintains 85%+ of coding accuracy
- **Q5_K_M**: Optimal for professional development work
- **Q8_0**: Maximum fidelity for complex algorithms

#### Phi-3.5 and Small Models

- **Q4_0**: Often sufficient due to model efficiency
- **Q4_K_M**: Standard recommendation
- **Higher quantizations**: Diminishing returns

## Platform-Specific Recommendations

### RTX 4090 Advantages

- **Raw Performance**: 4-8x faster than M4 Pro for large models
- **VRAM Efficiency**: Dedicated GPU memory reduces system conflicts
- **Thermal Headroom**: Better sustained performance under load
- **CUDA Ecosystem**: Broader framework support

**Best RTX 4090 Models:**

1. DeepSeek R1-32B (Q4_K_M) - Maximum reasoning
2. Mixtral 8x7B (Q4_K_M) - MoE efficiency
3. Qwen2.5-Coder-32B (Q4_K_M) - Advanced coding

### Apple Silicon M4 Pro Advantages

- **Energy Efficiency**: 9-11x better performance per watt
- **Unified Memory**: Up to 128GB configurations available
- **System Integration**: Excellent macOS optimization
- **Portability**: Battery-powered high-performance inference

**Best M4 Pro Models:**

1. Llama 3.2-8B (Q4_K_M) - Best all-around
2. Qwen2.5-Coder-7B (Q4_K_M) - Efficient coding
3. DeepSeek R1-14B (Q4_K_M) - Balanced reasoning

## Model Deployment Patterns

### Sequential Loading (Memory Constrained)

```bash
# Load models on-demand based on task type
case $TASK_TYPE in
  "reasoning") ollama run deepseek-r1:7b-distill-q4_K_M ;;
  "coding") ollama run qwen2.5-coder:7b-instruct-q4_K_M ;;
  "quick") ollama run phi3.5:3.8b-mini-instruct-q4_0 ;;
esac
```

### Concurrent Loading (Performance Focused)

```bash
# Pre-load frequently used models
ollama pull deepseek-r1:7b-distill-q4_K_M &
ollama pull qwen2.5-coder:7b-instruct-q4_K_M &
ollama pull phi3.5:3.8b-mini-instruct-q4_0 &
wait
```

### Hybrid Approach (Balanced)

```bash
# One large model + one fast model
ollama run deepseek-r1:14b-distill-q4_K_M &  # Primary capability
ollama run phi3.5:3.8b-mini-instruct-q4_0 &  # Quick responses
```

## Performance Benchmarking Results

### September 2025 Community Benchmarks

#### RTX 4090 Performance (Tokens/Second)

| Model            | Q4_K_M | Q5_K_M | Q6_K  | Q8_0  |
| ---------------- | ------ | ------ | ----- | ----- |
| DeepSeek R1-7B   | 50-60  | 45-55  | 40-50 | 35-45 |
| Qwen2.5-Coder-7B | 45-55  | 40-50  | 35-45 | 30-40 |
| Llama 3.2-8B     | 42-52  | 38-48  | 33-43 | 28-38 |
| Phi-3.5-3.8B     | 65-80  | 60-75  | 55-70 | 50-65 |
| DeepSeek R1-32B  | 10-15  | 8-12   | 6-10  | 5-8   |

#### M4 Pro Performance (Tokens/Second)

| Model            | Q4_K_M | Q5_K_M | Q6_K  | Q8_0  |
| ---------------- | ------ | ------ | ----- | ----- |
| DeepSeek R1-7B   | 42-52  | 38-48  | 33-43 | 28-38 |
| Qwen2.5-Coder-7B | 45-58  | 40-50  | 35-45 | 30-40 |
| Llama 3.2-8B     | 42-52  | 38-48  | 33-43 | 28-38 |
| Phi-3.5-3.8B     | 60-75  | 55-70  | 50-65 | 45-60 |
| DeepSeek R1-32B  | 15-25  | 12-20  | 10-16 | 8-14  |

## Quality Benchmarks

### Academic Benchmarks (September 2025)

| Model            | MMLU  | HumanEval | GSM8K | TruthfulQA |
| ---------------- | ----- | --------- | ----- | ---------- |
| DeepSeek R1-32B  | 84.2% | 85.7%     | 89.5% | 78.3%      |
| DeepSeek R1-7B   | 76.8% | 78.4%     | 82.1% | 71.2%      |
| Qwen2.5-Coder-7B | 72.5% | 88.4%     | 75.8% | 68.9%      |
| Llama 3.2-8B     | 73.0% | 72.6%     | 78.2% | 69.7%      |
| Phi-3.5-3.8B     | 69.1% | 68.9%     | 74.5% | 65.4%      |

### Practical Performance Metrics

- **Response Latency**: First token generation time
- **Context Handling**: Performance with long conversations
- **Instruction Following**: Adherence to complex prompts
- **Factual Accuracy**: Real-world knowledge correctness

## Future Model Roadmap

### Expected Q4 2025 Releases

- **Qwen3 Stable**: October 2025, 36T token training
- **Llama 3.3**: Enhanced efficiency and capabilities
- **DeepSeek R1.1**: Improved reasoning and reduced hallucinations
- **Phi-4**: Microsoft's next-generation small model

### Emerging Trends

- **MoE Architectures**: More efficient large models
- **Multi-modal Integration**: Vision + text capabilities
- **Code Specialization**: Domain-specific optimization
- **Energy Efficiency**: Focus on performance per watt

## Vision-Enabled Models Detailed Guide

### Multi-Modal Model Performance

| Model                    | Size | RTX 4090 Perf | M4 Pro Perf | Memory | Vision Quality | Text Quality |
| ------------------------ | ---- | ------------- | ----------- | ------ | -------------- | ------------ |
| **Llama 3.2-Vision-11B** | 11B  | 25-35 tok/s   | 20-30 tok/s | 12GB   | 92/100         | 88/100       |
| **Qwen2-VL-7B**          | 7B   | 35-45 tok/s   | 30-40 tok/s | 8.5GB  | 88/100         | 85/100       |
| **Gemma2-VIT-9B**        | 9B   | 30-40 tok/s   | 25-35 tok/s | 10GB   | 85/100         | 87/100       |
| **MiniCPM-V-2.6**        | 8B   | 32-42 tok/s   | 28-38 tok/s | 9GB    | 82/100         | 80/100       |

### Vision Model Use Cases

#### **Image Analysis & Description**

```bash
# Install and use Llama 3.2 Vision
ollama pull llama3.2-vision:11b-instruct-q4_K_M

# Example n8n workflow integration
curl -X POST http://host.docker.internal:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2-vision:11b-instruct-q4_K_M",
    "prompt": "Describe this image in detail:",
    "images": ["base64_encoded_image_data"]
  }'
```

#### **Document Processing & OCR**

- **Qwen2-VL**: Excellent for document understanding and table extraction
- **Gemma2-VIT**: Strong performance on charts and technical diagrams
- **MiniCPM-V**: Efficient for batch document processing

#### **Creative & Design Workflows**

- **Llama 3.2-Vision**: Best for creative image interpretation
- **Qwen2-VL**: Multilingual image descriptions
- **Integration with n8n**: Automated image workflows for content creation

## Embedding Models for RAG Integration

### Embedding Model Performance

| Model                     | Dimensions | RTX 4090 Speed | M4 Pro Speed | MTEB Score | Languages |
| ------------------------- | ---------- | -------------- | ------------ | ---------- | --------- |
| **nomic-embed-text-v1.5** | 768        | 2000+ docs/s   | 1500+ docs/s | 62.4       | English   |
| **bge-large-en-v1.5**     | 1024       | 1800+ docs/s   | 1300+ docs/s | 64.2       | English   |
| **multilingual-e5-large** | 1024       | 1500+ docs/s   | 1100+ docs/s | 61.8       | 94 langs  |
| **all-MiniLM-L6-v2**      | 384        | 3000+ docs/s   | 2200+ docs/s | 58.8       | English   |

### RAG Workflow Integration

#### **PostgreSQL + pgvector Setup**

```sql
-- Create embedding table for RAG
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(768),  -- nomic-embed dimensions
    metadata JSONB
);

-- Create index for fast similarity search
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
```

#### **n8n Embedding Workflow**

```javascript
// Function node for generating embeddings
const embeddingModel = 'nomic-embed-text';
const response = await fetch('http://host.docker.internal:11434/api/embeddings', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: embeddingModel,
    prompt: $json.text_content
  })
});

const { embedding } = await response.json();
return [{ embedding, content: $json.text_content }];
```

#### **Embedding Model Selection by Use Case**

**Document Search & Retrieval:**

- **nomic-embed-text-v1.5**: Best overall performance for English documents
- **bge-large-en-v1.5**: Highest quality embeddings for critical applications
- **multilingual-e5-large**: Essential for multi-language document collections

**Real-time Applications:**

- **all-MiniLM-L6-v2**: Fastest processing for high-throughput scenarios
- **nomic-embed-text-v1.5**: Good balance of speed and quality

**Specialized Domains:**

- **bge-large-en-v1.5**: Technical and scientific documents
- **multilingual-e5-large**: International business documents
- **nomic-embed-text-v1.5**: General purpose with excellent retrieval

### Multi-Modal RAG Architecture

#### **Vision + Text RAG Pipeline**

```bash
# Multi-modal workflow components
ollama pull llama3.2-vision:11b-instruct-q4_K_M  # Vision understanding
ollama pull nomic-embed-text                       # Text embeddings
ollama pull qwen2.5-coder:7b-instruct-q4_K_M     # Response generation
```

#### **Integration with Langfuse**

Track multi-modal and embedding performance:

- **Vision model latency** and accuracy metrics
- **Embedding generation speed** and similarity scores
- **RAG pipeline performance** end-to-end
- **Multi-modal conversation traces**

### Resource Requirements

#### **Vision Models Memory Usage**

- **Concurrent text + vision**: Add 20-30% memory overhead
- **Image processing**: 2-4GB additional VRAM per concurrent request
- **Batch processing**: Scale memory linearly with batch size

#### **Embedding Models Optimization**

```bash
# Optimize embedding performance
export OLLAMA_NUM_PARALLEL=8          # Higher parallelism for embeddings
export OLLAMA_EMBEDDING_BATCH_SIZE=32  # Batch processing
export OLLAMA_KEEP_ALIVE="60m"        # Keep embedding models loaded
```

## See Also

- [RTX_4090_OPTIMIZATION.md](./RTX_4090_OPTIMIZATION.md) - NVIDIA-specific optimization
- [M4_PRO_OPTIMIZATION.md](./M4_PRO_OPTIMIZATION.md) - Apple Silicon optimization
- [OLLAMA_INTEGRATION.md](./OLLAMA_INTEGRATION.md) - General Ollama setup
- [CLAUDE.md](./CLAUDE.md) - Stack architecture overview
