# Ollama Integration Guide

## Why Native Ollama?

Running Ollama natively (not containerized) provides several advantages:

- Direct GPU access without Docker complexity
- Better performance with native drivers
- Easier model management
- Simpler troubleshooting

## Installation

### Ubuntu/Debian

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### macOS (Apple Silicon, Homebrew)

Prereqs: macOS (Darwin), Apple Silicon (arm64), Homebrew installed

Install Ollama and verify API:

```bash
bash ollama/scripts/install_ollama_macos_apple_silicon.sh
```

Tune environment for the Homebrew service and restart it:

```bash
bash ollama/scripts/tune_env_macos.sh
```

Quick checks and logs:

```bash
# API health
curl -sSf http://localhost:11434/api/tags >/dev/null && echo "[OK] Ollama up"
curl -s http://localhost:11434/api/ps | jq '.' || curl -s http://localhost:11434/api/ps

# Service status and logs
brew services list | grep '^ollama\b'
brew services log ollama
```

Persisting env across reboots (Homebrew launchd):

```bash
# Edit the LaunchAgent plist to add EnvironmentVariables, then reload
vi ~/Library/LaunchAgents/homebrew.mxcl.ollama.plist
launchctl unload ~/Library/LaunchAgents/homebrew.mxcl.ollama.plist
launchctl load -w ~/Library/LaunchAgents/homebrew.mxcl.ollama.plist
```

## Configuration for Stack Integration

### 1. Configure Ollama Service

- Set up systemd service
- Configure host binding (0.0.0.0:11434)

### 2. Network Configuration

- Containers access via `host.docker.internal:11434`

### 3. Environment Variables

```bash
# Add to .env
OLLAMA_HOST=host.docker.internal
OLLAMA_PORT=11434
```

## Model Management

### Download Popular Models

```bash
ollama pull llama3.2:3b     # Fast, lightweight
ollama pull qwen2.5-coder:7b # Code-focused
```

## Integration with n8n

### HTTP Request Node Configuration

- URL: `http://host.docker.internal:11434/api/generate`
  - or: `http://192.168.0.100:11434/api/generate` if running on another host on your local network (replace with host's
    local IP address)
- Use POST with JSON payload

## Integration with Langfuse

- Track Ollama usage in workflows
- Monitor performance and costs

## Troubleshooting

### Common Issues

- GPU detection
- Network connectivity
- Model performance
