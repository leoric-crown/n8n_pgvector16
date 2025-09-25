# GEMINI Project Overview: n8n Homelab Stack with PostgreSQL & pgvector

## Project Overview

This project provides a comprehensive Docker Compose stack for running the n8n workflow automation platform with a
PostgreSQL database backend. It is designed for homelab and production use, with a focus on security, scalability, and
AI/ML capabilities.

## Core Stack Technologies

The containerized stack includes:

- **n8n**: A powerful, open-source workflow automation tool.
- **PostgreSQL**: A robust, open-source object-relational database system.
- **pgvector**: A PostgreSQL extension for vector similarity search, enabling AI/ML applications.
- **Langfuse v3**: LLM observability platform with distributed architecture.
- **MinIO**: S3-compatible object storage for Langfuse event buffering.
- **Redis**: Cache and queue for Langfuse background processing.
- **ClickHouse**: OLAP database for traces, observations, and scores.
- **Docker Compose**: A tool for defining and running multi-container Docker applications.
- **Prometheus & Grafana**: Optional services for monitoring and metrics.

## External Homelab Integration

For enhanced homelab functionality, this stack can integrate with:

- **Ollama**: Native LLM server for local AI model inference (installed on host system, not containerized)

The core architecture is based on a set of interconnected Docker containers, orchestrated by Docker Compose. The `n8n`
service is the core of the application, providing the workflow automation capabilities. It is connected to a `postgres`
database service, which is used for data storage. The `pgvector` extension is enabled in the database, allowing for
advanced AI/ML workflows.

## Building and Running

To build and run this project, you will need to have Docker and Docker Compose installed.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/leoric-crown/n8n_pgvector16.git
   cd n8n_pgvector16
   ```

2. **Set up the environment:**

   **Recommended:** Use the automated setup script:

   ```bash
   make setup
   # OR
   python3 setup-env.py --auto
   ```

   **Alternative:** Manual setup:

   ```bash
   cp .env.example .env
   nano .env
   ```

   **IMPORTANT:** The automated script generates secure credentials and avoids common configuration issues.

3. **Start the stack:**

   ```bash
   docker compose up -d
   ```

   This will start all the services in the background. You can check the status of the services with:

   ```bash
   docker compose ps
   ```

4. **Access n8n:**

   - **Local**: `http://n8n.lan:5678` (requires DNS setup)
   - **Production**: `https://n8n.leoric.org` (with Cloudflare Tunnel)

## ⚠️ CRITICAL: Environment Configuration Maintenance

For developers adding/modifying services: **Always update .env.example with directive comments**

### Self-Documenting Environment Variables

This project uses a directive-based system where .env.example serves as both:

- **Template for automated generation** (via setup-env.py)
- **Manual reference** for maintenance

Example format:

```env
# GENERATE: strong_password(32) | Manual: openssl rand -base64 32
SERVICE_PASSWORD=placeholder_value
```

### Available Directive Types

**Password/Key Generation:**

- `strong_password(length)` - Mixed-character secure password
- `hex_key(length)` - Hexadecimal encryption key
- `base64_password(length)` - Base64-encoded password
- `s3_access_key(length)` - Alphanumeric access key

**System Detection:**

- `auto_detect_timezone` - Automatically detects system timezone
- `manual` - Requires manual setup (API keys, etc.)

**Context-Aware Templates:**

- `template("protocol")` - "http" for localhost, "https" for custom domains
- `template("n8n_host")` - Uses actual hostname (localhost or custom domain)
- `template("n8n_webhook_url")` - Full n8n webhook URL with proper protocol and port
- `template("langfuse_url")` - Full Langfuse URL with proper protocol and port

### Maintenance Rules

1. **Every environment variable MUST have a directive comment**
2. **Test changes**: Run `python3 setup-env.py --dry-run --auto`
3. **Use clear placeholders** that indicate required changes
4. **Provide copy-paste commands** in manual instructions
5. **Never commit real credentials**

This ensures the automated setup stays synchronized with stack evolution.

## Development Conventions

This project follows a set of development conventions to ensure code quality, security, and consistency.

- **Pre-commit Hooks**: The repository uses pre-commit hooks to automatically check for secrets, format code, and run
  other quality checks before committing code. To install the hooks, run:

  ```bash
  uv tool install detect-secrets
  pre-commit install
  ```

- **Coding Style**: The project uses `prettier` to automatically format YAML and Markdown files. This ensures a
  consistent coding style across the project.

- **Contribution Guidelines**:

  - **Security First**: All commits are automatically scanned for secrets.
  - **Format Consistency**: Auto-formatters handle Markdown and YAML styling.
  - **Documentation**: Update relevant `.md` files for any configuration changes.
  - **Testing**: Validate `docker-compose` syntax and test local deployment.
