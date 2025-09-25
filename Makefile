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

.PHONY: help up down restart pull status logs setup init validate db-shell prune

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

# Environment Setup
setup: ## Generate .env with secure credentials automatically
	@printf "$(CYAN)Generating .env with secure credentials...$(RESET)\n"
	@if python3 setup-env.py --auto; then \
		printf "$(GREEN).env file created with secure credentials$(RESET)\n"; \
	else \
		printf "$(RED)Setup failed - see message above$(RESET)\n"; \
		exit 1; \
	fi

init: setup pull up ## Complete initial setup (automated env + pull + up)
	@printf "$(GREEN)Automated setup complete!$(RESET)\n"
	@printf "\n$(YELLOW)⚠️  REQUIRED MANUAL STEPS:$(RESET)\n"
	@printf "\n$(CYAN)1. Fix n8n volume permissions (required for community nodes):$(RESET)\n"
	@printf "   make down\n"
	@printf "   docker run --rm -v n8n_pgvector16_n8n_nodes:/nodes alpine chown -R 1000:1000 /nodes\n"
	@printf "   make up\n"
	@printf "\n$(CYAN)2. Create Langfuse S3 bucket (required for LLM observability):$(RESET)\n"
	@printf "   • Open: http://localhost:9001\n"
	@printf "   • Login with S3 credentials from your .env file\n"
	@printf "   • Create bucket named: langfuse\n"
	@printf "\n$(CYAN)3. Access your services:$(RESET)\n"
	@printf "   • n8n: http://localhost:5678\n"
	@printf "   • Langfuse: http://localhost:9119\n"
	@printf "   • pgAdmin: http://localhost:5050 (admin@example.com / password in .env)\n"
	@printf "\n$(GREEN)💡 Run 'make help' for more commands$(RESET)\n"

validate: ## Validate docker-compose syntax
	@printf "$(CYAN)Validating docker-compose configuration...$(RESET)\n"
	@docker compose config > /dev/null && printf "$(GREEN)Configuration is valid$(RESET)\n" || printf "$(RED)Configuration has errors$(RESET)\n"

# Database Operations
db-shell: ## Access PostgreSQL shell as n8n user
	@printf "$(CYAN)Connecting to PostgreSQL shell...$(RESET)\n"
	docker compose exec postgres psql -U n8n_user -d n8n

# Maintenance

prune: ## Clean unused Docker resources (non-destructive)
	@printf "$(YELLOW)Cleaning unused Docker resources...$(RESET)\n"
	docker system prune -f
	@printf "$(GREEN)Cleanup complete$(RESET)\n"
