# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a Docker Compose stack for running n8n (workflow automation tool) with PostgreSQL as the database backend. The setup includes:

- **PostgreSQL with pgvector**: Uses `pgvector/pgvector:pg16` image with vector extension for AI/ML workflows
- **n8n**: Latest n8n workflow automation tool connected to PostgreSQL
- **Optional monitoring**: Prometheus and Grafana (currently commented out)

## Key Components

- `docker-compose.yml`: Main service definitions for postgres and n8n services
- `DEPLOYMENT.md`: Comprehensive deployment guide for production setup with Cloudflare Tunnel
- `init-data.sh`: PostgreSQL initialization script that creates non-root user and enables vector extension
- `.env`: Environment variables for database credentials (copy from `.env.example`)
- `prometheus.yml`: Prometheus configuration for optional monitoring setup
- `myLANrootCA.crt`: Custom certificate for internal LAN usage

## Common Commands

### Start the stack
```bash
docker-compose up -d
```

### Stop the stack
```bash
docker-compose stop
```

### Tear down with volume removal
```bash
docker-compose down -v
```

### View logs
```bash
docker-compose logs -f n8n
docker-compose logs -f postgres
```

### Management script (from parent directory)
```bash
../manage.bash up    # Start all compose stacks in parent directory
../manage.bash down  # Stop all compose stacks
```

## Configuration

- Database credentials are configured in `.env` file (copy from `.env.example`)
- DNS server for n8n container configured via `DNS_SERVER` environment variable
- n8n is accessible on port 5678 at `n8n.lan` (requires DNS setup)
- PostgreSQL uses custom non-root user for n8n connection
- Vector extension is automatically enabled during database initialization

## Environment Setup

1. Copy `.env.example` to `.env` and update passwords
2. Ensure `myLANrootCA.crt` is present for SSL certificate trust
3. Configure DNS or hosts file for `n8n.lan` resolution

## Monitoring (Optional)

Uncomment Prometheus and Grafana services in `docker-compose.yml` to enable:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/overBurden9)
- n8n metrics available at `/metrics` endpoint when enabled