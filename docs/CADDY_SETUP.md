# Local Network Access with Caddy (Optional)

For a more convenient local development experience, you can use [Caddy](https://caddyserver.com/) as a reverse proxy to
provide HTTPS for your local services (e.g., `https://n8n.lan`).

## Caddyfile Configuration for Long-Running Workflows

Add the following to your Caddyfile, then run `caddy run`. This includes increased timeouts to prevent errors with
long-running LLM workflows.

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

This configuration enables automatic HTTPS via Caddy. For public domains reachable from the internet, Caddy will obtain
certificates from Let's Encrypt. For private/internal hostnames (e.g., `*.lan`), Caddy uses its internal CA — you may
need to trust the local CA certificate on your devices. For more advanced configurations, please refer to the
[official Caddy documentation](https://caddyserver.com/docs/).

Point your local DNS records (or update your host files) to route n8n.lan to your host's local IP address to get a fully
functional https served n8n instance on your local network
