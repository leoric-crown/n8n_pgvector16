<!-- @format -->

# n8n Homelab Stack with PostgreSQL & pgvector

A comprehensive Docker Compose stack for running n8n workflow automation with PostgreSQL database backend, featuring pgvector extension for AI/ML workflows and optional n8n-mcp integration for AI-assisted development.

## Features

- **n8n**: Latest workflow automation platform
- **PostgreSQL with pgvector**: Vector extension for AI/ML embeddings and similarity search
- **n8n-mcp**: AI assistant for workflow development (optional)
- **Production-ready**: HTTPS support, metrics enabled, Cloudflare Tunnel integration
- **Monitoring**: Optional Prometheus & Grafana setup (commented out)
- **Secure**: Non-root database user, configurable encryption

## Quick Start

### 1. Environment Setup

```bash
cp .env.example .env                     # Copy example environment file
nano .env                               # Edit with your credentials
```

**IMPORTANT:** Change the default passwords and configure your domain in the `.env` file!

### 2. Start the Stack

```bash
docker compose up -d                    # Start all services
docker compose ps                       # Check status
docker compose logs -f n8n              # View logs
```

### 3. Access n8n

- **Local**: http://n8n.lan:5678 (requires DNS setup)
- **Production**: https://n8n.leoric.org (with Cloudflare Tunnel)

## Production Deployment

For secure internet-accessible deployment with Cloudflare Tunnel, see the comprehensive [DEPLOYMENT.md](DEPLOYMENT.md) guide.

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
POSTGRES_PASSWORD=your_super_secret_postgres_password
POSTGRES_NON_ROOT_PASSWORD=your_super_secret_postgres_password

# n8n
N8N_HOST=n8n.lan                    # Change for production
TIMEZONE=America/Mexico_City

# n8n-mcp (AI assistant)
N8N_API_KEY=your_n8n_api_key_here
MCP_AUTH_TOKEN=your_secure_auth_token_here
```

### Services

- **postgres**: PostgreSQL 16 with pgvector extension
- **n8n**: Main workflow automation service
- **n8n-mcp**: AI assistant for workflow development (optional)
- **prometheus/grafana**: Monitoring stack (commented out)

## Management

### Common Commands

```bash
docker compose up -d                    # Start stack
docker compose stop                     # Stop stack
docker compose logs -f n8n              # View n8n logs
docker compose logs -f postgres         # View postgres logs
docker compose restart n8n              # Restart specific service
docker compose down -v                  # Complete teardown (removes volumes)

# Database management
docker compose exec postgres pg_dump -U n8n_user -d n8n > backup.sql           # Backup
docker compose exec -T postgres psql -U n8n_user -d n8n < backup.sql           # Restore
docker compose exec postgres psql -U n8n_user -d n8n                           # Access database
```

## AI/ML Capabilities

This stack includes pgvector extension for:
- Vector similarity search
- Embedding storage and retrieval
- AI/ML workflow support
- Semantic search capabilities

The n8n-mcp service provides AI-assisted workflow development when configured with API keys.

## Security Notes

- Database uses non-root user for n8n connections
- Fixed encryption key for data consistency
- Environment variable isolation
- Optional SSL certificate support for internal use

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

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development guidance and architecture overview.

For production deployment with Cloudflare Tunnel, follow the [DEPLOYMENT.md](DEPLOYMENT.md) guide.
