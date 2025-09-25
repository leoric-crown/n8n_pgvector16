# MAINTENANCE.md

## Common Management Commands

```bash
# Stack management
docker compose up -d                    # Start stack
docker compose stop                     # Stop stack
docker compose restart n8n              # Restart specific service
docker compose down -v                  # Complete teardown (removes volumes)
docker compose ps                       # Check service status

# Logs and monitoring
docker compose logs -f n8n              # Follow n8n logs
docker compose logs -f postgres         # Follow postgres logs
docker compose logs --tail=50 n8n       # View last 50 log lines
curl http://localhost:8042/health       # Check n8n-mcp health

# Database management
docker compose exec postgres pg_dump -U n8n_user -d n8n > backup.sql           # Backup
docker compose exec -T postgres psql -U n8n_user -d n8n < backup.sql           # Restore
docker compose exec postgres psql -U n8n_user -d n8n                           # Access DB
docker compose exec postgres pg_isready -U n8n_user -d n8n                     # Test connectivity
```

## License Management

```bash
# Clear license (fixes license fingerprint mismatch errors)
docker exec n8n-app n8n license:clear
docker compose restart n8n
```

## Encryption Key Migration

```bash
# Export existing credentials (before changing key)
docker exec n8n-app n8n export:credentials --all --decrypted --output=/tmp/credentials.json
docker cp n8n-app:/tmp/credentials.json ./credentials-backup.json

# Generate new key and update .env
openssl rand -hex 32  # Copy output to N8N_ENCRYPTION_KEY in .env

# Restart with new key
docker compose down n8n ; docker compose up -d

# Import credentials back
docker cp ./credentials-backup.json n8n-app:/tmp/credentials.json
docker exec n8n-app n8n import:credentials --input=/tmp/credentials.json

# Clean up
rm ./credentials-backup.json
docker exec n8n-app rm /tmp/credentials.json
```

## Security Best Practices

### Completed Security Measures

- ✅ Strong passwords for database and admin accounts
- ✅ `N8N_PROXY_HOPS=2` configured for reverse proxy setup
- ✅ `N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true`
- ✅ `N8N_BLOCK_ENV_ACCESS_IN_NODE=true`
- ✅ Custom encryption key (not hardcoded)
- ✅ HTTPS enabled with proper host configuration

### Additional Security Recommendations

- [ ] Set `N8N_USER_MANAGEMENT_JWT_SECRET` for session security
- [ ] Consider `N8N_USER_MANAGEMENT_DISABLED=true` after creating admin user
- [ ] Enable `N8N_LOG_LEVEL=warn` to reduce sensitive data in logs
- [ ] Set up API rate limiting
- [ ] Enable audit logging with `N8N_LOG_OUTPUT=file`

### Network Security

- Database port not exposed (internal Docker network only)
- n8n behind Caddy + Cloudflare Tunnel (2 proxy hops)
- Custom Docker network isolation (optional improvement)
