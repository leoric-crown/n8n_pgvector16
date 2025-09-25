# Ollama Integration Guide

This guide provides a complete workflow for setting up, tuning, and integrating a native Ollama instance with the n8n
stack.

## Why Native Ollama?

Running Ollama natively on the host machine (not containerized) is the recommended approach for this project. It offers:

- **Direct GPU Access**: No Docker virtualization overhead, ensuring maximum performance.
- **Simplified Drivers**: Avoids complexities with container-to-GPU driver mapping.
- **Easier Management**: Pulling, updating, and managing models is more straightforward.
- **Simpler Troubleshooting**: Direct access to logs and system resources.

## Step 1: Installation

First, install Ollama on your host machine. The installation scripts also perform a basic API health check.

- **For Linux with NVIDIA GPU**:

  ```bash
  sudo bash ollama/scripts/install_ollama_linux_nvidia.sh
  ```

- **For macOS with Apple Silicon**:

  ```bash
  bash ollama/scripts/install_ollama_macos_apple_silicon.sh
  ```

## Step 2: Environment Tuning

Next, apply platform-specific tuning. These scripts set environment variables for performance, such as enabling Flash
Attention and setting a sensible KV cache quantization policy.

- **For Linux with NVIDIA GPU**:

  ```bash
  sudo bash ollama/scripts/tune_env_nvidia.sh
  ```

- **For macOS with Apple Silicon**:

  ```bash
  bash ollama/scripts/tune_env_macos.sh
  ```

**Note**: The macOS tuning script only sets the environment for the current user session. For persistence across
reboots, you must edit the `homebrew.mxcl.ollama.plist` file as instructed by the script's output.

## Step 3: Model Selection and Management

1. **Choose Your Models**: Refer to the [Local LLM Model Selection Guide](./MODEL_SELECTION_GUIDE.md) to choose the best
   models for your hardware and use cases.

2. **Pull the Models**: Use `ollama pull` to download them. For a good starting point, grab the baseline models:

   ```bash
   # See ollama/BASELINE_MODELS.md for the latest recommendations
   ollama pull llama3.2:8b
   ollama pull qwen3-coder
   ollama pull phi4-mini:3.8b
   ```

3. **Verify Performance**: Use the benchmark script to test token-per-second performance.

   ```bash
   bash ollama/scripts/benchmark_models.sh llama3.2:8b qwen3-coder
   ```

## Step 4: Integration with n8n

Within n8n, you can now connect to Ollama using the HTTP Request node. The n8n container can reach the Ollama service
running on the host via `host.docker.internal`.

When using the 'AI Agent' node you can connect it directly to Ollama by using the 'Ollama Chat Model' node.

### HTTP Request Node: Basic Generation

- **URL**: `http://host.docker.internal:11434/api/generate`
- **Method**: `POST`

```json
{
  "method": "POST",
  "url": "http://host.docker.internal:11434/api/generate",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "model": "llama3.2:8b",
    "prompt": "{{$json.prompt}}",
    "stream": false,
    "options": {
      "temperature": 0.7,
      "num_predict": 256
    }
  }
}
```

### Function Node: Dynamic Model Selection

You can use a Function node to dynamically select the best model for a given task, based on tags or other input.

```javascript
// Function node for dynamic model selection
const modelMap = {
  'reasoning': 'deepseek-r1:8b',
  'coding': 'qwen3-coder',
  'quick': 'phi4-mini:3.8b'
};

const taskType = $json.task_type || 'reasoning';

return [{
  model: modelMap[taskType] || modelMap['reasoning'],
  prompt: $json.prompt,
  max_tokens: $json.max_tokens || 256
}];
```

## Troubleshooting

- **Network Connectivity**: Ensure the Docker container can reach the host. `host.docker.internal` is the standard way.
  If that fails, you may need to use your host machine's specific LAN IP address (e.g., `http://192.168.1.100:11434`).
- **Performance Issues**: Use `btop`, `nvtop`, or other system monitoring utilities to check for CPU/GPU bottlenecks or
  thermal throttling.
