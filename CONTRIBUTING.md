# Contributing to n8n Homelab Stack

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Code of Conduct

Be respectful, constructive, and professional in all interactions. We're building tools to help each other.

## How to Contribute

### Reporting Issues

When reporting issues, please include:

- **Environment details**: OS, Docker version, hardware specs
- **Steps to reproduce**: Clear, numbered steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Logs**: Relevant error messages (sanitize any sensitive data)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:

- Check existing issues to avoid duplicates
- Clearly describe the use case and benefits
- Provide examples of how it would work
- Consider backward compatibility

### Pull Requests

1. **Fork the repository** and create a feature branch
2. **Make your changes** following the project structure
3. **Test your changes** thoroughly
4. **Update documentation** if needed
5. **Submit a pull request** with a clear description

## Development Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for setup scripts)
- `uv` for Python package management (optional but recommended)

### Initial Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/n8n_pgvector16.git
cd n8n_pgvector16

# Install development tools
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install detect-secrets
pre-commit install

# Generate environment
make setup

# Start the stack
make up
```

### Running Tests

```bash
# Validate docker-compose configuration
docker compose config

# Check pre-commit hooks
pre-commit run --all-files

# Test environment generation
python3 setup-env.py --dry-run --auto
```

## Development Guidelines

### Code Style

- **YAML**: Use 2-space indentation, consistent formatting
- **Markdown**: 120-character line wrap, clear headings
- **Shell scripts**: Include error handling, use shellcheck
- **Python**: Follow PEP 8, use type hints where helpful

### Pre-commit Hooks

This project uses automated pre-commit hooks for:

- **Security**: Secret detection (detect-secrets)
- **Formatting**: Prettier (YAML), mdformat (Markdown)
- **Validation**: YAML/JSON syntax checking
- **File hygiene**: Trailing whitespace, line endings

All commits are automatically checked. To run manually:

```bash
pre-commit run --all-files
```

### Commit Messages

Use clear, descriptive commit messages:

```text
feat: add support for custom Ollama models
fix: resolve PostgreSQL connection timeout
docs: update benchmark methodology
chore: update dependencies
```

## Documentation

### When to Update Docs

Update documentation when you:

- Add new features or configuration options
- Change existing behavior
- Add new services to docker-compose.yml
- Modify environment variables

### Documentation Files

- `README.md` - Main documentation and quick start
- `DEPLOYMENT.md` - Production deployment guide
- `MAINTENANCE.md` - Operational procedures
- `CLAUDE.md` - Development guidance and architecture
- `docs/BENCHMARKS.md` - Performance analysis
- `docs/RESOURCES.md` - External references

### Benchmark Results

When contributing benchmark results:

1. Use the provided benchmark scripts (`ollama/benchmark/`)
2. Include full hardware specifications
3. Document test methodology clearly
4. Provide reproducible configurations
5. Export results in multiple formats (CSV, JSON)

## Project Structure

```text
.
├── docker-compose.yml      # Service definitions
├── init-data.sh            # PostgreSQL initialization
├── setup-env.py            # Environment generation script
├── .env.example            # Environment template
├── docs/                   # Documentation
│   ├── BENCHMARKS.md       # Performance analysis
│   └── RESOURCES.md        # External references
├── ollama/                 # Ollama configuration and docs
│   └── benchmark/          # Benchmark tools
└── .pre-commit-config.yaml # Pre-commit hooks config
```

## Testing Changes

### Docker Compose Changes

```bash
# Validate syntax
docker compose config

# Test with fresh containers
docker compose down -v
docker compose up -d

# Check logs
docker compose logs -f
```

### Environment Variable Changes

When modifying `.env.example`:

1. Add directive comments for auto-generation
2. Test the setup script: `python3 setup-env.py --dry-run --auto`
3. Verify manual instructions are clear
4. Document the purpose in comments

Example:

```text
# GENERATE: strong_password(32) | Manual: openssl rand -base64 32
NEW_SERVICE_PASSWORD=placeholder_value
```

### Benchmark Script Changes

```bash
cd ollama/benchmark

# Install dependencies
uv pip install -r requirements.txt

# Test with dry-run
uv run --with-requirements requirements.txt run_matrix.py --dry-run

# Test with single model
uv run --with-requirements requirements.txt benchmark_models.py phi4-mini:3.8b
```

## Security Guidelines

### Never Commit

- Real `.env` files
- API keys or passwords
- Personal credentials
- Cloudflare Tunnel tokens
- Private keys or certificates

The pre-commit hooks will catch most of these, but be vigilant.

### Environment Variables

- Use placeholder values in `.env.example`
- Document generation methods
- Never hardcode secrets in code

### Docker Security

- Use non-root users where possible
- Minimize exposed ports
- Keep images updated
- Review security scan results

## Review Process

Pull requests will be reviewed for:

1. **Functionality**: Does it work as intended?
2. **Documentation**: Are changes documented?
3. **Security**: Are there any security concerns?
4. **Testing**: Has it been tested adequately?
5. **Code quality**: Is it clean and maintainable?
6. **Backward compatibility**: Does it break existing setups?

## Getting Help

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub discussions for questions
- **Documentation**: Check docs/ directory first

## Recognition

Contributors are recognized in:

- Git commit history
- Release notes
- Project documentation

Thank you for contributing to make this project better!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
