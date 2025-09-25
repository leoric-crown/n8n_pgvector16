# n8n.<your-domain> Cloudflare Tunnel Deployment Guide

## Prerequisites

### 1. Core Stack Prerequisites

#### Docker Environment

- Docker and Docker Compose installed
- Sufficient system resources (minimum 4GB RAM recommended)

#### Cloudflare Account Setup

- Domain `<your-domain>` added to Cloudflare
- Domain nameservers pointing to Cloudflare

### 2. Optional Homelab Components

For enhanced homelab functionality, you may also want:

- **Ollama** (for local LLM inference)
  - Install natively on a host on your local network
  - See [OLLAMA_INTEGRATION.md](./ollama/OLLAMA_INTEGRATION.md) for setup guides
  - Not required for basic n8n functionality

### 3. Verify Domain in Cloudflare

```bash
# Check nameservers point to Cloudflare
dig NS <your-domain>

# Verify DNS record exists (created automatically by tunnel)
dig n8n.<your-domain>
```

- Ensure `<your-domain>` domain is active in Cloudflare dashboard
- DNS records will be created automatically by the tunnel

## Cloudflare Tunnel Setup

### CLI Approach (Recommended)

Based on the
[n8n community guide](https://community.n8n.io/t/securely-self-hosting-n8n-with-docker-cloudflare-tunnel-the-arguably-less-painful-way/93801),
this is the simplest method:

1. **Install cloudflared**:

   ```bash
   # Download and install cloudflared
   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared-linux-amd64.deb
   ```

2. **Authenticate with Cloudflare**:

   ```bash
   cloudflared tunnel login
   ```

3. **Create tunnel**:

   ```bash
   cloudflared tunnel create n8n-<your-domain>
   ```

4. **Route DNS to tunnel**:

   ```bash
   cloudflared tunnel route dns n8n-<your-domain> n8n.<your-domain>
   ```

5. **Configure cloudflared**: Create `/etc/cloudflared/config.yml`:

   ```yaml
   tunnel: <TUNNEL_UUID>  # Get from: cloudflared tunnel info n8n-<your-domain>
   credentials-file: <PATH_TO_CREDENTIALS>  # Usually ~/.cloudflared/<UUID>.json
   ingress:
     - hostname: n8n.<your-domain>
       service: http://localhost:5678
     - service: http_status:404
   ```

   Find your tunnel UUID and credentials file:

   ```bash
   # Get tunnel UUID
   cloudflared tunnel info n8n-<your-domain>

   # Find credentials file (check both locations)
   ls ~/.cloudflared/
   ls /root/.cloudflared/  # if run with sudo
   ```

6. **Install and start tunnel service**:

   ```bash
   sudo cloudflared service install
   sudo systemctl enable --now cloudflared
   ```

7. **Verify tunnel is running**:

   ```bash
   sudo systemctl status cloudflared
   sudo journalctl -u cloudflared -f
   ```

### 3. Additional Security (Optional)

- Enable **Access policies** for authentication
- Configure **WAF rules** for protection
- Set up **Rate limiting**

## Environment Configuration

### 1. Update .env file

#### Option A: Automated Setup (Recommended)

```bash
# Generate .env with secure passwords (avoids Docker Compose issues)
python3 setup-env.py --auto --n8n-host n8n.<your-domain>
```

#### Option B: Manual Setup

```bash
# Copy example and edit
cp .env.example .env
```

**Warning:** If setting passwords manually, avoid using `$` characters as they cause Docker Compose variable
interpolation errors.

Update the following variables in `.env`:

```env
# Production domain
N8N_HOST=n8n.<your-domain>

# Database credentials (generate strong passwords)
POSTGRES_PASSWORD=your_secret_postgres_password
POSTGRES_NON_ROOT_PASSWORD=your_super_secret_postgres_password

# Timezone
TIMEZONE=America/Mexico_City

# n8n API key (generate after deployment, update .env, and docker compose down+up n8n)
N8N_API_KEY=your_n8n_api_key_here

# MCP auth token (generate with: openssl rand -hex 32)
MCP_AUTH_TOKEN=your_secure_auth_token_here
```

## Production Configuration Changes

The docker-compose.yml file is already configured for production with:

### 1. n8n Configuration

- HTTPS protocol support
- Production-ready environment variables
- n8n-mcp integration for AI-assisted workflow development

### 2. Cloudflare Tunnel

Cloudflare Tunnel runs as a system service (installed via CLI), not as a Docker container.

## Deployment Steps

### 1. Pre-deployment Checks

```bash
# Verify DNS propagation
dig n8n.<your-domain>

# Verify .env configuration
cat .env

# Check docker-compose syntax
docker compose config
```

### 2. Optional Components Setup

```bash
# OPTIONAL: Initialize tableau-mcp submodule (only if using Tableau integration)
# git submodule init
# git submodule update

# If not using tableau-mcp, comment it out in docker-compose.yml to avoid build errors
```

### 3. Deploy Stack

```bash
# Pull latest images
docker compose pull

# Start services
docker compose up -d

# Check service status
docker compose ps
docker compose logs -f n8n
```

### 3. Initial n8n Setup

1. Access \<<https://n8n>.<your-domain>> (Cloudflare handles SSL and routing)
2. Create admin account
3. Configure base URL in settings
4. Generate API key for n8n-mcp integration

### 4. Configure n8n-mcp Integration

```bash
# Generate MCP auth token
openssl rand -hex 32

# Update .env with n8n API key and MCP token
# Restart n8n-mcp service
```

## Post-Deployment Verification

### 1. Service Health Checks

```bash
# Check all services running
docker compose ps

# Test database connectivity
docker compose exec postgres pg_isready -U n8n_user -d n8n

# Check n8n logs for errors
docker compose logs n8n | grep -i error
```

### 2. Functionality Tests

- [ ] n8n web interface accessible at \<<https://n8n>.<your-domain>>
- [ ] Workflow creation and execution
- [ ] Webhook endpoints working
- [ ] Database persistence (docker compose down+up container test)
- [ ] Cloudflare Tunnel connectivity

### 3. Security Verification

- [ ] Default passwords changed
- [ ] API keys generated and secured
- [ ] Firewall rules configured (only necessary ports open)
- [ ] SSL certificate valid (if using reverse proxy)

## Backup Strategy

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U n8n_user -d n8n > n8n_backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T postgres psql -U n8n_user -d n8n < n8n_backup_YYYYMMDD.sql
```

### Volume Backup

```bash
# Backup n8n data
docker run --rm -v n8n_pgvector16_n8n_storage:/data -v $(pwd):/backup alpine tar czf /backup/n8n_data_$(date +%Y%m%d).tar.gz -C /data .

# Backup database
docker run --rm -v n8n_pgvector16_db_storage:/data -v $(pwd):/backup alpine tar czf /backup/db_data_$(date +%Y%m%d).tar.gz -C /data .
```

## Troubleshooting

### Cloudflare Tunnel Issues

- Check tunnel service status: `sudo systemctl status cloudflared`
- View tunnel logs: `sudo journalctl -u cloudflared -f`
- Verify tunnel is running: `cloudflared tunnel info n8n-<your-domain>`

### SSL Issues

- Cloudflare handles all SSL termination
- Verify Cloudflare SSL/TLS mode is set to "Full" or "Full (strict)"
- Check Cloudflare Edge Certificates are active

### Database Connection Issues

```bash
# Check postgres logs
docker compose logs postgres

# Test database connection
docker compose exec postgres psql -U n8n_user -d n8n -c "SELECT version();"
```

### n8n Service Issues

```bash
# Check n8n logs
docker compose logs n8n

# Restart n8n service
docker compose restart n8n

# Check database connectivity from n8n
docker compose exec n8n sh -c 'nc -zv postgres 5432'
```

## Personal Use & Experimentation Setup

### 1. Basic Security for Personal Use

#### Simple Cloudflare Access Protection

1. Go to **Zero Trust > Access > Applications**
2. Select your n8n application
3. Add basic email protection:
   - **Policy name**: `Personal Access`
   - **Action**: `Allow`
   - **Include**: `Emails` → Your personal email
   - **Require**: `One-time PIN` (sends code to email)

This gives you secure access without complex enterprise auth.

### 2. Convenience Configuration for Experimentation

#### Useful n8n Settings for Personal Use

```env
# Keep templates for inspiration
N8N_TEMPLATES_ENABLED=true

# Enable useful features
N8N_DIAGNOSTICS_ENABLED=false  # Disable telemetry if preferred
N8N_PUBLIC_API_DISABLED=false  # Keep API for integrations

# Generate secure encryption key (save this!)
N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)
```

#### Simple Monitoring

```bash
# Basic health check script
#!/bin/bash
curl -f https://n8n.<your-domain>/healthz || \
  echo "n8n down - $(date)" >> ~/n8n-health.log
```

### 3. Personal Automation Ideas

#### Home Lab Automations

- **Server Monitoring**: Check disk space, CPU usage, send alerts to phone
- **Backup Automation**: Scheduled backups to cloud storage (Google Drive, Dropbox)
- **API Playground**: Test webhooks, experiment with REST APIs
- **RSS/News Aggregation**: Collect feeds, filter content, send daily digest
- **Home Assistant Integration**: Connect IoT devices, automate smart home
- **GitHub Repository Monitoring**: Watch for new releases, security alerts

#### Simple Useful Workflows

- **Weather to Calendar**: Daily weather forecast in calendar
- **Bill Reminders**: Parse email bills, add to calendar with reminders
- **Social Media Cross-posting**: Share content across platforms
- **File Organization**: Auto-organize downloads by type/date
- **Meeting Notes**: Auto-create meeting notes from calendar events

### 4. Development Workflow Integration

#### Git Webhooks for Personal Projects

```bash
# Example webhook URL for your n8n
https://n8n.<your-domain>/webhook/github-deploy
```

#### API Testing Environment

- Use n8n as API client for testing personal projects
- Mock external services for development
- Generate test data for applications

### 5. Simple Backup Strategy

#### Quick Backup Commands

```bash
# Manual backup when experimenting
docker compose exec postgres \
  pg_dump -U n8n_user -d n8n > backup-$(date +%Y%m%d).sql

# Export workflows
curl -H "X-N8N-API-KEY: your-api-key" \
  https://n8n.<your-domain>/api/v1/workflows > workflows-backup.json
```

### 6. Quick Recovery

#### If Something Breaks

```bash
# Quick restart
docker compose restart

# Reset if needed (WARNING: loses data)
docker compose down -v
docker compose up -d
```

#### Useful Development Commands

```bash
# View logs
docker compose logs -f n8n

# Access n8n container
docker compose exec n8n sh

# Database access
docker compose exec postgres \
  psql -U n8n_user -d n8n
```

## Maintenance

### Casual Maintenance for Personal Use

- [ ] Monthly updates when convenient (`docker compose pull && docker compose up -d`)
- [ ] Backup workflows before major experiments
- [ ] Check disk space occasionally
- [ ] Clean up old Docker images: `docker system prune`

### If You Want to Scale Later

- Free tier cloudflared tunnel may not be enough for power users once fully set up and running workflows daily
