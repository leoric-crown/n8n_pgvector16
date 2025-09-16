# GEMINI Project Overview: n8n Homelab Stack with PostgreSQL & pgvector

## Project Overview

This project provides a comprehensive Docker Compose stack for running the n8n workflow automation platform with a
PostgreSQL database backend. It is designed for homelab and production use, with a focus on security, scalability, and
AI/ML capabilities.

The key technologies used in this project are:

- **n8n**: A powerful, open-source workflow automation tool.
- **PostgreSQL**: A robust, open-source object-relational database system.
- **pgvector**: A PostgreSQL extension for vector similarity search, enabling AI/ML applications.
- **Docker Compose**: A tool for defining and running multi-container Docker applications.
- **n8n-mcp**: An optional AI assistant for workflow development.
- **Prometheus & Grafana**: Optional services for monitoring and metrics.

The architecture is based on a set of interconnected Docker containers, orchestrated by Docker Compose. The `n8n`
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

1. **Set up the environment:**

   Copy the example environment file and edit it with your credentials:

   ```bash
   cp .env.example .env
   nano .env
   ```

   **IMPORTANT:** Change the default passwords and configure your domain in the `.env` file.

1. **Start the stack:**

   ```bash
   docker compose up -d
   ```

   This will start all the services in the background. You can check the status of the services with:

   ```bash
   docker compose ps
   ```

1. **Access n8n:**

   - **Local**: `http://n8n.lan:5678` (requires DNS setup)
   - **Production**: `https://n8n.leoric.org` (with Cloudflare Tunnel)

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
