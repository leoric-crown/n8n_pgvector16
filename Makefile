# n8n Stack Makefile
# Maintainer convenience commands for Docker Compose stack

# Colors for output
RED = \033[31m
GREEN = \033[32m
YELLOW = \033[33m
BLUE = \033[34m
MAGENTA = \033[35m
CYAN = \033[36m
WHITE = \033[37m
RESET = \033[0m

# Default target
.DEFAULT_GOAL := help

.PHONY: help up down restart pull status logs health ports env secrets init validate db-shell pgadmin update prune

# Help target
help: ## Show this help message
	@printf "$(CYAN)n8n Stack Management$(RESET)\n"
	@printf "$(YELLOW)Available targets:$(RESET)\n\n"
	@printf "$(GREEN)Core Operations:$(RESET)\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-12s$(RESET) %s\n", $$1, $$2}'

# Core Operations
up: ## Start all services in detached mode
	@printf "$(GREEN)Starting n8n stack...$(RESET)\n"
	docker compose up -d
	@printf "$(GREEN)Stack started successfully$(RESET)\n"

down: ## Stop all services (preserves volumes)
	@printf "$(YELLOW)Stopping n8n stack...$(RESET)\n"
	docker compose down
	@printf "$(YELLOW)Stack stopped$(RESET)\n"

restart: ## Restart all services
	@printf "$(CYAN)Restarting n8n stack...$(RESET)\n"
	docker compose restart
	@printf "$(GREEN)Stack restarted successfully$(RESET)\n"

pull: ## Pull latest images for all services
	@printf "$(BLUE)Pulling latest images...$(RESET)\n"
	docker compose pull
	@printf "$(GREEN)Images updated$(RESET)\n"

# Monitoring & Status
status: ## Show container status and health
	@printf "$(CYAN)Container Status:$(RESET)\n"
	docker compose ps
	@printf "\n$(CYAN)System Resources:$(RESET)\n"
	docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

logs: ## Follow logs for all services
	@printf "$(CYAN)Following logs for all services (Ctrl+C to exit)...$(RESET)\n"
	docker compose logs -f

health: ## Check service health endpoints
	@printf "$(CYAN)Checking service health...$(RESET)\n"
	@printf "$(BLUE)n8n Health:$(RESET)\n"
	@curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:${N8N_PORT:-5678}/healthz || printf "  $(RED)Service not responding$(RESET)\n"
	@printf "$(BLUE)Langfuse Health:$(RESET)\n"
	@curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:${LANGFUSE_PORT:-9119}/api/public/health || printf "  $(RED)Service not responding$(RESET)\n"
	@printf "$(BLUE)pgAdmin Health:$(RESET)\n"
	@curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:${PGADMIN_PORT:-5050}/misc/ping || printf "  $(RED)Service not responding$(RESET)\n"

ports: ## List all exposed ports
	@printf "$(CYAN)Exposed Ports:$(RESET)\n"
	@printf "$(BLUE)n8n:$(RESET)          http://localhost:${N8N_PORT:-5678}\n"
	@printf "$(BLUE)Langfuse:$(RESET)     http://localhost:${LANGFUSE_PORT:-9119}\n"
	@printf "$(BLUE)pgAdmin:$(RESET)      http://localhost:${PGADMIN_PORT:-5050}\n"
	@printf "$(BLUE)n8n-mcp:$(RESET)      http://localhost:${MCP_PORT:-8042}\n"
	@printf "$(BLUE)postgres-mcp:$(RESET) http://localhost:${POSTGRES_MCP_PORT:-8000}\n"
	@printf "$(BLUE)tableau-mcp:$(RESET)  http://localhost:${TABLEAU_MCP_PORT:-3927}\n"
	@printf "$(BLUE)MinIO:$(RESET)        http://localhost:9000 (API), http://localhost:9001 (Console)\n"
	@printf "$(BLUE)PostgreSQL:$(RESET)   localhost:5432\n"

# Environment Setup
env: ## Copy .env.example to .env if missing
	@if [ ! -f .env ]; then \
		printf "$(YELLOW)Creating .env from .env.example...$(RESET)\n"; \
		cp .env.example .env; \
		printf "$(GREEN).env file created$(RESET)\n"; \
		printf "$(YELLOW)Please edit .env with your specific values$(RESET)\n"; \
	else \
		printf "$(GREEN).env file already exists$(RESET)\n"; \
	fi

secrets: ## Generate required secrets/keys for .env
	@printf "$(CYAN)Generating secrets...$(RESET)\n"
	@printf "$(BLUE)N8N_ENCRYPTION_KEY:$(RESET)        $$(openssl rand -hex 32)\n"
	@printf "$(BLUE)MCP_AUTH_TOKEN:$(RESET)            $$(openssl rand -hex 32)\n"
	@printf "$(BLUE)LANGFUSE_NEXTAUTH_SECRET:$(RESET)  $$(openssl rand -hex 32)\n"
	@printf "$(BLUE)LANGFUSE_ENCRYPTION_KEY:$(RESET)   $$(openssl rand -hex 32)\n"
	@printf "$(BLUE)LANGFUSE_SALT:$(RESET)             $$(openssl rand -hex 32)\n"
	@printf "$(BLUE)LANGFUSE_CLICKHOUSE_PASSWORD:$(RESET) $$(openssl rand -base64 12)\n"
	@printf "$(BLUE)LANGFUSE_REDIS_PASSWORD:$(RESET)   $$(openssl rand -base64 24)\n"
	@printf "$(BLUE)LANGFUSE_S3_ACCESS_KEY:$(RESET)    $$(openssl rand -hex 10 | tr 'a-f' 'A-F')\n"
	@printf "$(BLUE)LANGFUSE_S3_SECRET_KEY:$(RESET)    $$(openssl rand -base64 30)\n"
	@printf "\n$(YELLOW)Copy these values to your .env file$(RESET)\n"

init: env pull up ## Complete initial setup (env + pull + up)
	@printf "$(GREEN)Initial setup complete!$(RESET)\n"
	@printf "$(CYAN)Next steps:$(RESET)\n"
	@printf "  1. Edit .env with your specific values (run 'make secrets' for generated keys)\n"
	@printf "  2. Run 'make restart' after updating .env\n"
	@printf "  3. Access services at the ports listed in 'make ports'\n"

validate: ## Validate docker-compose syntax
	@printf "$(CYAN)Validating docker-compose configuration...$(RESET)\n"
	@docker compose config > /dev/null && printf "$(GREEN)Configuration is valid$(RESET)\n" || printf "$(RED)Configuration has errors$(RESET)\n"

# Database Operations
db-shell: ## Access PostgreSQL shell
	@printf "$(CYAN)Connecting to PostgreSQL shell...$(RESET)\n"
	docker compose exec postgres psql -U "$${POSTGRES_NON_ROOT_USER:-n8n_user}" -d "$${POSTGRES_DB:-n8n}"

pgadmin: ## Open pgAdmin interface
	@printf "$(CYAN)pgAdmin is available at:$(RESET)\n"
	@printf "$(BLUE)URL:$(RESET) http://localhost:${PGADMIN_PORT:-5050}\n"
	@printf "$(BLUE)Login:$(RESET) $${PGADMIN_DEFAULT_EMAIL:-admin@example.com}\n"
	@printf "$(BLUE)Password:$(RESET) Check your .env file\n"

# Maintenance
update: pull restart ## Pull latest images and restart services
	@printf "$(GREEN)Stack updated successfully$(RESET)\n"

prune: ## Clean unused Docker resources (non-destructive)
	@printf "$(YELLOW)Cleaning unused Docker resources...$(RESET)\n"
	docker system prune -f
	@printf "$(GREEN)Cleanup complete$(RESET)\n"
