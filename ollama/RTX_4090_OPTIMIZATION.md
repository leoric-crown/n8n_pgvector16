# RTX 4090 Optimization Guide for Local LLM Inference

Complete optimization guide for NVIDIA RTX 4090 with 24GB VRAM for local LLM inference using Ollama and n8n workflows.

## Hardware Specifications

- **Architecture**: Ada Lovelace (8.9 compute capability)
- **VRAM**: 24GB GDDR6X with 1008.4 GB/s memory bandwidth
- **CUDA Cores**: 16,384
- **Tensor Cores**: 512 (4th generation)
- **FP16 Performance**: 82.58 TFLOPS

## Memory Management Strategies

### VRAM Allocation Guidelines

- **Model Size Estimation**: FP16 models require ~2 bytes per parameter
  - 7B model: ~14GB VRAM
  - 13B model: ~26GB VRAM (requires quantization)
  - 33B model: ~66GB VRAM (requires heavy quantization)

### Optimal Configuration

```bash
# Reserve 2GB for GPU overhead
export OLLAMA_GPU_OVERHEAD=2147483648

# Optimize parallel processing
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=2

# Enable optimizations
export OLLAMA_FLASH_ATTENTION=1
export CUDA_VISIBLE_DEVICES=0

# Context optimization
export OLLAMA_CONTEXT_LENGTH=4096
```

## Recommended Models by Performance Tier

### Tier 1: High Performance (7-13B Models)

- **DeepSeek R1-7B**: 50-60 tokens/sec, ~8GB VRAM
- **Qwen2.5-Coder-7B**: 45-55 tokens/sec, ~6.3GB VRAM
- **Llama 3.2-8B**: 42-52 tokens/sec, ~8.5GB VRAM

### Tier 2: Balanced (20-34B Models)

- **DeepSeek R1-32B**: 10-15 tokens/sec, ~20GB VRAM
- **Mixtral 8x7B**: 22-35 tokens/sec, ~13GB VRAM
- **Yi 34B (Q4_K_M)**: 15-25 tokens/sec, ~19GB VRAM

## Multi-Model Hosting Configurations

### Configuration A: Development Stack

```bash
# Load coding + reasoning models simultaneously
ollama pull deepseek-r1:7b-distill-q4_K_M      # 8GB
ollama pull qwen2.5-coder:7b-instruct-q4_K_M   # 6.3GB
ollama pull phi3.5:3.8b-mini-instruct-q4_0     # 3GB
# Total: 17.3GB (leaves 6.7GB for context/overhead)
```

### Configuration B: Power User

```bash
# Balance capability and efficiency
ollama pull deepseek-r1:14b-distill-q4_K_M     # 12GB
ollama pull qwen2.5-coder:7b-instruct-q4_K_M   # 6.3GB
# Total: 18.3GB (leaves 5.7GB for context/overhead)
```

### Configuration C: Maximum Single Model

```bash
# Ultimate capability
ollama pull deepseek-r1:32b-distill-q4_K_M     # 20GB
# Leaves 4GB for context and system operations
```

## Performance Optimization

### CUDA Environment

```bash
# Install CUDA 12.1+ and latest drivers
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# Driver recommendations: 531+ (550+ series preferred)
nvidia-smi --query-gpu=driver_version --format=csv
```

### Power and Thermal Management

```bash
# Optimal efficiency at 50-60% power limit
sudo nvidia-smi -pl 250  # Set 250W power limit (from 450W default)

# Monitor temperatures (keep under 80°C for sustained workloads)
watch -n 1 nvidia-smi
```

### Quantization Selection

- **Q4_K_M**: Best balance of quality vs size (recommended)
- **Q5_K_M**: Higher quality, slightly larger
- **Q6_K**: Near-original quality, ~2.7x memory reduction
- **IQ2**: Extreme compression for 70B+ models

## Integration with n8n

### HTTP Request Node Configuration

```json
{
  "method": "POST",
  "url": "http://host.docker.internal:11434/api/generate",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "model": "deepseek-r1:7b-distill-q4_K_M",
    "prompt": "{{$json.prompt}}",
    "stream": false,
    "options": {
      "temperature": 0.7,
      "num_predict": 256,
      "num_ctx": 4096
    }
  }
}
```

### Workflow Template for Model Selection

```javascript
// Function node for dynamic model selection
const modelMap = {
  'reasoning': 'deepseek-r1:7b-distill-q4_K_M',
  'coding': 'qwen2.5-coder:7b-instruct-q4_K_M',
  'quick': 'phi3.5:3.8b-mini-instruct-q4_0'
};

const taskType = $json.task_type || 'reasoning';
return [{
  model: modelMap[taskType] || modelMap['reasoning'],
  prompt: $json.prompt,
  max_tokens: $json.max_tokens || 256
}];
```

## Monitoring and Troubleshooting

### Performance Monitoring Script

```bash
#!/bin/bash
# monitor_rtx4090.sh
while true; do
    clear
    echo "=== RTX 4090 LLM Performance Monitor ==="
    nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw --format=csv,noheader
    echo ""
    echo "Ollama Status:"
    curl -s http://localhost:11434/api/ps | jq '.models[] | {name: .name, size: .size_vram}'
    sleep 2
done
```

### Common Issues and Solutions

**GPU Not Detected:**

```bash
# Verify NVIDIA drivers
nvidia-smi
# Check CUDA installation
nvcc --version
# Restart Ollama service
sudo systemctl restart ollama
```

**Memory Issues:**

```bash
# Check VRAM usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
# Reduce parallel requests if needed
export OLLAMA_NUM_PARALLEL=2
```

**Performance Degradation:**

```bash
# Monitor thermal throttling
nvidia-smi -q -d temperature
# Check power limits
nvidia-smi -q -d power
```

## Benchmarking Results

### Real-World Performance (Community Data)

| Model         | Size | Quantization | Tokens/Sec | VRAM Usage | Use Case  |
| ------------- | ---- | ------------ | ---------- | ---------- | --------- |
| DeepSeek R1   | 7B   | Q4_K_M       | 50-60      | 8GB        | Reasoning |
| Qwen2.5-Coder | 7B   | Q4_K_M       | 45-55      | 6.3GB      | Coding    |
| Llama 3.2     | 8B   | Q4_K_M       | 42-52      | 8.5GB      | General   |
| Mixtral       | 8x7B | Q4_K_M       | 22-35      | 13GB       | Complex   |
| DeepSeek R1   | 32B  | Q4_K_M       | 10-15      | 20GB       | Maximum   |

### GPU Utilization Metrics

- **Small Models (7-13B)**: 85-95% GPU utilization
- **Large Models (30B+)**: 90-99% GPU utilization
- **CPU Usage**: Typically 1-5% during inference

## See Also

- [OLLAMA_INTEGRATION.md](./OLLAMA_INTEGRATION.md) - General Ollama setup
- [M4_PRO_OPTIMIZATION.md](./M4_PRO_OPTIMIZATION.md) - Apple Silicon comparison
- [MODEL_SELECTION_GUIDE.md](./MODEL_SELECTION_GUIDE.md) - Model recommendations
- [CLAUDE.md](../CLAUDE.md) - Stack architecture overview
