<!-- @format -->

# n8n Homelab Stack with PostgreSQL & pgvector

A comprehensive Docker Compose stack for running n8n workflow automation with PostgreSQL database backend, featuring
pgvector extension for AI/ML workflows and optional n8n-mcp integration for AI-assisted development.

## Features

- **n8n**: AI-native workflow automation platform
- **PostgreSQL with pgvector**: Vector extension for AI/ML embeddings and similarity search
- **n8n-mcp**: AI assistant for workflow development (optional)
- **Production-ready**: HTTPS support, metrics enabled, Cloudflare Tunnel integration
- **Monitoring**: Optional Prometheus & Grafana setup (commented out)
- **Secure**: Non-root database user, configurable encryption

## Performance & Benchmarks

This repository includes comprehensive benchmark results from testing various LLM models on consumer hardware (RTX 4090
24GB VRAM).

**Key Findings:**

- **GPT-OSS**: 21B parameter model handling 100K context at 150+ tokens/sec on 24GB VRAM
- **Context Window Scaling**: Detailed analysis of performance from 8K to 100K tokens across 6 models
- **Memory Efficiency**: Comparison of VRAM usage and RAM spillover thresholds
- **Real-World Recommendations**: Model selection guidance for different use cases

📊 **[View detailed benchmark results →](docs/BENCHMARKS.md)**

🔗 **[External resources & references →](docs/RESOURCES.md)**

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/leoric-crown/n8n_pgvector16.git
cd n8n_pgvector16

# OPTIONAL: Initialize git submodules (only if using tableau-mcp)
git submodule init
git submodule update
```

**Note:** The `tableau-mcp` service is optional. If you don't need Tableau integration:

- Skip the submodule initialization above
- Comment out the `tableau-mcp` service in `docker-compose.yml`
- Otherwise, Docker Compose will fail with "Dockerfile not found" errors

### 2. Install Development Tools (Optional but Recommended)

```bash
# Install uv for Python package management
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install pre-commit hooks for security and code quality
uv tool install detect-secrets
pre-commit install
```

**Security Features Enabled:**

- Secret detection (API keys, passwords, tokens)
- Environment file protection
- Auto-formatting for Markdown and YAML
- Docker security checks

### 3. Environment Setup

#### Quick Setup (Recommended)

```bash
make setup                              # Generate .env with secure credentials
```

#### Alternative Methods

```bash
# Direct script usage
python3 setup-env.py --auto

# Manual setup (not recommended)
cp .env.example .env && nano .env
```

**Safety Note:** The setup will not overwrite existing `.env` files. If you have an existing `.env`, back it up first:
`cp .env .env.backup && rm .env`

### 4. Start the Stack

#### One-Command Setup

```bash
make init                               # Complete setup: env + pull + start
```

#### Step-by-Step

```bash
make pull                               # Pull latest images
make up                                 # Start all services
make status                             # Check status
make logs                               # Check logs
```

**Note:** n8n will fail to start initially due to volume permission issues. This is expected - continue to step 5.

### 5. Initialize Community Node Storage (Required After First Start)

```bash
# Stop the stack first
make down

# Set proper permissions for n8n community nodes volume
docker run --rm -v n8n_pgvector16_n8n_nodes:/nodes alpine chown -R 1000:1000 /nodes

# If you have existing community nodes to migrate:
docker run --rm -v "$(pwd)/n8n-nodes":/source -v n8n_pgvector16_n8n_nodes:/target alpine sh -c "cp -r /source/* /target/ && chown -R 1000:1000 /target"

# Restart the stack
make up
```

**Why this step?** Docker creates the volume with root ownership. n8n runs as user 1000 and needs write permissions to
install community nodes. This one-time setup ensures proper permissions.

**Note:** After this setup, community nodes installed through n8n's interface will automatically persist across
restarts.

### 6. Configure S3 Storage for Langfuse (Required for LLM Observability)

If you're using the Langfuse LLM observability stack, you need to create the required S3 bucket:

**For MinIO (default local setup):**

```bash
# Start MinIO service first
docker compose up minio -d

# Access MinIO web console at http://localhost:9001
# Login credentials (from .env file):
# - Access Key: LANGFUSE_S3_ACCESS_KEY value
# - Secret Key: LANGFUSE_S3_SECRET_KEY value

# Create a bucket named 'langfuse' through the web interface
```

**For AWS S3 (production):**

- Create an S3 bucket named `langfuse` (or your preferred name)
- Update environment variables in `.env` to point to AWS S3 instead of MinIO
- Ensure IAM permissions include `s3:PutObject`, `s3:ListBucket`, and `s3:GetObject`

**Why this step?** Langfuse requires an S3-compatible bucket to store event data, traces, and observability information.
Without this bucket, Langfuse will fail with S3 credential errors.

### 7. Access n8n

- **Local**: <http://localhost:5678>
- **Production**: <https://your.domain.com> (with Cloudflare Tunnel + your own domain)

## Local Network Access with Caddy (Optional)

For a more convenient local development experience, you can use [Caddy](https://caddyserver.com/) as a reverse proxy to
provide HTTPS for your local services (e.g., `https://n8n.lan`). This is optional and not required for production
deployments using Cloudflare Tunnels.

### Caddyfile Configuration for Long-Running Workflows

Add the following to your Caddyfile, then run `caddy run`. This includes increased timeouts to prevent errors with slow
LLM workflows.

```caddy
n8n.lan {
    reverse_proxy localhost:5678 {
        transport http {
            dial_timeout 600s
            response_header_timeout 600s
        }
    }
}
```

This configuration automatically provides a trusted HTTPS certificate (provided by LetsEncrypt) for `n8n.lan` on your
local network. For more advanced configurations, please refer to the
[official Caddy documentation](https://caddyserver.com/docs/).

Point your local DNS records (or update your host files) to route n8n.lan to your host's local IP address to get a fully
functional https served n8n instance on your local network

## Quick Reference

### Service URLs

- **n8n**: <http://localhost:5678>
- **Langfuse**: <http://localhost:9119>
- **pgAdmin**: <http://localhost:5050> (<admin@example.com> / password in .env)
- **MinIO Console**: <http://localhost:9001>

## Production Deployment

For secure internet-accessible deployment with Cloudflare Tunnel, see the comprehensive [DEPLOYMENT.md](DEPLOYMENT.md)
guide.

Key features for production:

- HTTPS protocol with SSL termination via Cloudflare
- Secure tunnel without exposing ports
- Comprehensive metrics and monitoring
- Production-grade database configuration

## Configuration

### Environment Variables

Key variables in `.env`:

```env
# Database
POSTGRES_PASSWORD=your_secret_postgres_password
POSTGRES_NON_ROOT_PASSWORD=your_super_secret_postgres_password

# n8n
N8N_HOST=0.0.0.0
TIMEZONE=America/Mexico_City    # Set your timezone (https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

# n8n-mcp (AI assistant https://github.com/czlonkowski/n8n-mcp)
N8N_API_KEY=your_n8n_api_key_here
MCP_AUTH_TOKEN=your_secure_auth_token_here
```

### Services

- **postgres**: PostgreSQL 16 with pgvector extension
- **n8n**: Main workflow automation service
- **langfuse**: LLM observability and analytics platform (v3)
- **langfuse-worker**: Async event processor for Langfuse
- **minio**: S3-compatible object storage for event buffering
- **redis**: Cache and queue management
- **clickhouse**: OLAP database for traces/observations/scores
- **n8n-mcp**: AI assistant for workflow development (optional)
- **prometheus/grafana**: Monitoring stack (commented out)

### Langfuse v3 Architecture (Important!)

Langfuse v3 uses a distributed database architecture for optimal performance:

- **PostgreSQL**: Stores authentication, projects, API keys, and configuration only
- **ClickHouse**: Stores all traces, observations, and scores (the actual LLM data)
- **MinIO/S3**: Buffers raw events before processing
- **Redis**: Manages queues and caching

**Note**: The `traces`, `observations`, and `scores` tables in PostgreSQL remain empty by design in v3. All
observability data is stored in ClickHouse for better performance at scale.

## Management

## AI/ML Capabilities

This stack includes pgvector extension for:

- Vector similarity search
- Embedding storage and retrieval
- AI/ML workflow support
- Semantic search capabilities

The n8n-mcp service provides AI-assisted workflow development when configured with API keys.

## Security & Development Features

### Pre-commit Security Hooks

This repository includes comprehensive security and code quality automation:

```bash
# Run all checks manually
pre-commit run --all-files

# Security features
- detect-secrets: Prevents API keys, passwords, tokens from being committed
- Environment protection: Blocks .env commits, validates .env.example
- Private key detection: SSH keys, certificates, crypto material
- Docker security: Basic Dockerfile security pattern scanning
```

### Auto-formatting & Code Quality

- **Markdown**: Auto-wraps lines to 120 characters, fixes formatting
- **YAML**: Prettier formatting with consistent styling
- **File hygiene**: Removes trailing whitespace, fixes line endings
- **Format validation**: YAML, JSON, TOML, XML syntax checking
- **Shellcheck**: Shell script linting (when available)

### Production Security

- Database uses non-root user for n8n connections
- Configurable encryption key (not hardcoded)
- Environment variable isolation
- HTTPS protocol with proxy hop configuration
- Blocked environment access in nodes (`N8N_BLOCK_ENV_ACCESS_IN_NODE=true`)

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in docker-compose.yml if 5678 is in use
2. **Database connection**: Verify credentials in .env match database settings
3. **DNS resolution**: Configure n8n.lan in your DNS or hosts file for local access

### Logs and Debugging

```bash
# Check service status
docker compose ps

# View detailed logs
docker compose logs --tail=50 n8n
docker compose logs --tail=50 postgres

# Test database connectivity
docker compose exec postgres pg_isready -U n8n_user -d n8n
```

## Development & Contributing

### Development Setup

```bash
# Install development tools
uv tool install detect-secrets
pre-commit install

# Test your changes
pre-commit run --all-files
docker compose config  # Validate docker-compose.yml
```

### Contributing Guidelines

1. **Security First**: All commits are automatically scanned for secrets
2. **Format Consistency**: Auto-formatters handle Markdown and YAML styling
3. **Documentation**: Update relevant .md files for any configuration changes
4. **Testing**: Validate docker-compose syntax and test local deployment

### Architecture & Deployment

- See [CLAUDE.md](CLAUDE.md) for detailed development guidance and architecture overview
- For production deployment with Cloudflare Tunnel, follow the [DEPLOYMENT.md](DEPLOYMENT.md) guide
- Check [MAINTENANCE.md](MAINTENANCE.md) for operational procedures and security best practices
