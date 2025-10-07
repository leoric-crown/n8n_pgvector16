# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a Docker Compose stack for running n8n (workflow automation tool) with PostgreSQL as the database backend. The
containerized stack includes:

- **PostgreSQL with pgvector**: Uses `pgvector/pgvector:pg16` image with vector extension for AI/ML workflows
- **n8n**: Latest n8n workflow automation tool connected to PostgreSQL
- **Langfuse v3**: LLM observability platform with distributed architecture
- **MinIO**: S3-compatible object storage for Langfuse event buffering
- **Redis**: Cache and queue for Langfuse background processing
- **ClickHouse**: OLAP database for traces, observations, and scores
- **Optional monitoring**: Prometheus and Grafana (currently commented out)
- **Note**: Tableau MCP server has been extracted to a standalone stack

### External Homelab Dependencies

- **Ollama**: Native LLM server (installed on host system, not containerized) for local AI model inference
  - Runs independently on the host OS
  - Accessible to containers via `host.docker.internal`
  - See [Ollama Integration](./ollama/README.md) for setup and optimization guides

### Langfuse v3 Database Architecture (CRITICAL)

Langfuse v3 uses a distributed storage architecture:

**PostgreSQL stores:**

- User authentication and sessions
- Projects and API keys
- Configuration and metadata
- Dashboards and UI settings
- ⚠️ NOT traces/observations/scores (these tables exist but remain empty)

**ClickHouse stores:**

- All traces, observations, and scores (actual LLM observability data)
- Optimized for high-throughput ingestion and analytical queries
- This is where your LLM metrics actually live

**MinIO/S3 stores:**

- Raw event data (temporary buffer before processing)
- Large objects and multi-modal content
- Events are written here first, then processed to ClickHouse

**Redis provides:**

- Queue management for async processing
- Caching for improved performance
- Session management

**Data Flow:**

1. n8n/SDK → Langfuse API → MinIO (immediate storage)
2. Worker reads from MinIO → Processes events → Writes to ClickHouse
3. UI queries ClickHouse for traces (NOT PostgreSQL)

## Key Components

- `docker-compose.yml`: Main service definitions for postgres and n8n services
- `.env.example`: Environment variable template with directive-based auto-generation
- `setup-env.py`: Automated environment setup script with secure credential generation
- `init-data.sh`: PostgreSQL initialization script that creates non-root user and enables vector extension
- `DEPLOYMENT.md`: Comprehensive deployment guide for production setup with Cloudflare Tunnel
- `MAINTENANCE.md`: Operational commands and security best practices
- `prometheus.yml`: Prometheus configuration for optional monitoring setup

## ⚠️ CRITICAL: .env.example Maintenance

**When adding/removing services or environment variables, you MUST update .env.example with directive comments:**

### Adding New Environment Variables

Use the dual comment system for auto-generation + manual instructions:

```env
# GENERATE: strong_password(32) | Manual: openssl rand -base64 32
NEW_SERVICE_PASSWORD=placeholder_value

# GENERATE: hex_key(32) | Manual: openssl rand -hex 32
NEW_SERVICE_KEY=placeholder_key

# GENERATE: template("n8n_host") | Manual: Set to your domain
NEW_SERVICE_HOST=service.lan
```

### Directive Types Available

- `strong_password(length)` - Secure mixed-character password
- `hex_key(length)` - Hexadecimal key (for encryption)
- `base64_password(length)` - Base64-encoded password
- `s3_access_key(length)` - Alphanumeric access key
- `auto_detect_timezone` - System timezone detection
- `manual` - Requires manual setup (like API keys)

### Template Directives (Context-Aware)

- `template("protocol")` - Sets "http" for localhost, "https" for custom domains
- `template("n8n_host")` - Uses actual hostname (localhost or custom domain)
- `template("n8n_webhook_url")` - Full n8n webhook URL with proper protocol and port
- `template("langfuse_url")` - Full Langfuse URL with proper protocol and port

### Rules for .env.example

1. **Every new env var MUST have a directive comment** above it
2. **Manual instructions MUST be actionable** (copy-paste commands)
3. **Use placeholder values** that clearly indicate what needs to be changed
4. **Test the script** after changes: `python3 setup-env.py --dry-run --auto`
5. **Never commit real credentials** - only placeholders

This system ensures the setup script stays current as the stack evolves.

## Common Commands

### Start the stack

```bash
docker compose up -d
```

### Stop the stack

```bash
docker compose stop
```

### Tear down with volume removal

```bash
docker compose down -v
```

### View logs

```bash
docker compose logs -f n8n
docker compose logs -f postgres
```

## Configuration

- Database credentials are configured in `.env` file (copy from `.env.example`)
- DNS server for n8n container configured via `DNS_SERVER` environment variable
- n8n is accessible on port 5678 at `n8n.lan` (requires DNS setup)
- PostgreSQL uses custom non-root user for n8n connection
- Vector extension is automatically enabled during database initialization
- Langfuse v3 requires Redis to use `REDIS_HOST`, `REDIS_PORT`, `REDIS_AUTH` (not `REDIS_URL`)
- MinIO requires `S3_REGION` and `S3_FORCE_PATH_STYLE` environment variables

## Environment Setup

### Automated Setup (Recommended)

Use the automated setup script for secure, consistent configuration:

```bash
make setup    # Generate .env with secure credentials
# OR
python3 setup-env.py --auto
```

### Core Stack Setup

1. Copy `.env.example` to `.env` and update passwords

2. Configure DNS or hosts file for `n8n.lan` resolution

3. **CRITICAL: Create S3 bucket for Langfuse** (required for LLM observability):

   - **MinIO (local)**: Access <http://localhost:9001>, create bucket named `langfuse`
   - **AWS S3 (production)**: Create S3 bucket with proper IAM permissions
   - **Without this step**: Langfuse will fail with S3 credential errors

4. Install pre-commit hooks for security and code quality:

   ```bash
   uv tool install detect-secrets
   pre-commit install
   ```

### External Homelab Components

For complete homelab functionality, you may also want to set up:

- **Ollama for local LLM inference** (see [Ollama Integration](./ollama/README.md)):
  - Install Ollama natively on host system
  - Configure for container integration via `host.docker.internal`
  - Download recommended models for your hardware

## Pre-commit Hooks

Comprehensive security and code quality hooks with automatic formatting:

- **Secret Detection**: `detect-secrets` prevents committing API keys, passwords, tokens
- **File Hygiene**: Trailing whitespace, end-of-file fixes, line endings
- **Auto-formatting**: Prettier for YAML, mdformat for Markdown (120 char line wrap)
- **Format Validation**: YAML, JSON, TOML, XML syntax checking
- **Docker Security**: Basic Dockerfile security pattern detection
- **Linting**: yamllint and markdownlint for consistent formatting
- **Environment Protection**: Prevents `.env` commits, validates `.env.example`

The formatters automatically fix line length issues in Markdown and YAML files.

Run manually: `pre-commit run --all-files`

## Homelab LLM Integration Documentation

For complete homelab setup with local LLM capabilities (using ollama), see the comprehensive documentation:

- **[Ollama Integration](./ollama/README.md)** - Native Ollama setup and integration guide
- **[MODEL_SELECTION_GUIDE.md](./ollama/MODEL_SELECTION_GUIDE.md)** - Model recommendations and benchmarks
- **[Benchmark Tools](./ollama/benchmark/README.md)** - Configuration, matrix testing, and visualization

## Monitoring (Optional)

Uncomment Prometheus and Grafana services in `docker-compose.yml` to enable:

- Prometheus: <http://localhost:9090>
- Grafana: <http://localhost:3000> (admin/overBurden9)
- n8n metrics available at `/metrics` endpoint when enabled
