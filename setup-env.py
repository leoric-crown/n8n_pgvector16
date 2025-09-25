#!/usr/bin/env python3
"""
Cross-platform environment setup script for n8n pgvector stack.
Generates secure credentials and creates .env file from .env.example template.
"""

import argparse
import os
import platform
import re
import secrets
import socket
import string
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple


class EnvSetup:
    """Environment setup handler for n8n pgvector stack."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.env_example = base_dir / '.env.example'
        self.env_file = base_dir / '.env'
        self.os_type = platform.system()

    def generate_hex_key(self, length: int = 32) -> str:
        """Generate a secure hex key."""
        return secrets.token_hex(length)

    def generate_base64_password(self, length: int = 12) -> str:
        """Generate a secure base64-like password."""
        # Using URL-safe base64 encoding for better compatibility
        return secrets.token_urlsafe(length)

    def generate_alphanumeric_key(self, length: int = 20, uppercase: bool = True) -> str:
        """Generate an alphanumeric key with optional uppercase."""
        chars = string.ascii_letters + string.digits
        if uppercase:
            # Mix of upper and lower case
            return ''.join(secrets.choice(chars) for _ in range(length))
        else:
            # Lowercase only with digits
            chars = string.ascii_lowercase + string.digits
            return ''.join(secrets.choice(chars) for _ in range(length))

    def generate_strong_password(self, length: int = 24) -> str:
        """Generate a strong password with mixed characters.
        Avoids $ to prevent Docker Compose variable interpolation issues.
        """
        # Safe special characters (no $ to avoid docker-compose interpolation)
        safe_special = '!@#%^&*()_+-=[]{}|;:,.<>?'

        # Ensure at least one of each type
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice(safe_special)
        ]

        # Fill the rest
        all_chars = string.ascii_letters + string.digits + safe_special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))

        # Shuffle to avoid predictable pattern
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)

    def detect_dns_server(self) -> str:
        """Detect local DNS server based on OS."""
        default_dns = "1.1.1.1"  # Cloudflare DNS as fallback

        try:
            if self.os_type == "Darwin":  # macOS
                # Try to get DNS from system configuration
                import subprocess
                result = subprocess.run(
                    ["scutil", "--dns"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Parse first nameserver
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'nameserver' in line and ':' in line:
                            dns_ip = line.split(':')[1].strip()
                            if self._is_valid_ip(dns_ip):
                                return dns_ip

            elif self.os_type == "Linux":
                # Check resolv.conf
                resolv_conf = Path('/etc/resolv.conf')
                if resolv_conf.exists():
                    with open(resolv_conf, 'r') as f:
                        for line in f:
                            if line.startswith('nameserver'):
                                dns_ip = line.split()[1]
                                if self._is_valid_ip(dns_ip):
                                    return dns_ip

            elif self.os_type == "Windows":
                import subprocess
                result = subprocess.run(
                    ["nslookup", "google.com"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Parse server address from nslookup output
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Server:' in line or 'Address:' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                dns_ip = parts[1].strip().split('#')[0]
                                if self._is_valid_ip(dns_ip):
                                    return dns_ip
        except Exception:
            pass

        return default_dns

    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def get_timezone(self) -> str:
        """Get system timezone or default."""
        default_tz = "America/New_York"

        try:
            if self.os_type in ["Darwin", "Linux"]:
                # Try to read from /etc/localtime symlink
                tz_path = Path('/etc/localtime')
                if tz_path.exists() and tz_path.is_symlink():
                    tz_link = str(tz_path.readlink())
                    if 'zoneinfo/' in tz_link:
                        return tz_link.split('zoneinfo/')[-1]

                # Try TZ environment variable
                if 'TZ' in os.environ:
                    return os.environ['TZ']

            elif self.os_type == "Windows":
                import subprocess
                result = subprocess.run(
                    ["tzutil", "/g"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Map Windows timezone to IANA format (simplified)
                    win_tz = result.stdout.strip()
                    # Common mappings (extend as needed)
                    tz_map = {
                        'Eastern Standard Time': 'America/New_York',
                        'Central Standard Time': 'America/Chicago',
                        'Mountain Standard Time': 'America/Denver',
                        'Pacific Standard Time': 'America/Los_Angeles',
                        'GMT Standard Time': 'Europe/London',
                        'Central European Standard Time': 'Europe/Berlin',
                    }
                    return tz_map.get(win_tz, default_tz)
        except Exception:
            pass

        return default_tz

    def generate_credentials(self) -> Dict[str, str]:
        """Generate all required credentials."""
        return {
            # PostgreSQL passwords
            'POSTGRES_PASSWORD': self.generate_strong_password(32),
            'POSTGRES_NON_ROOT_PASSWORD': self.generate_strong_password(28),
            'LANGFUSE_DB_PASSWORD': self.generate_strong_password(30),

            # pgAdmin password
            'PGADMIN_DEFAULT_PASSWORD': self.generate_strong_password(16),

            # Encryption keys (32-byte hex = 256-bit)
            'N8N_ENCRYPTION_KEY': self.generate_hex_key(32),
            'LANGFUSE_NEXTAUTH_SECRET': self.generate_hex_key(32),
            'LANGFUSE_ENCRYPTION_KEY': self.generate_hex_key(32),
            'LANGFUSE_SALT': self.generate_hex_key(32),
            'MCP_AUTH_TOKEN': self.generate_hex_key(32),

            # Langfuse v3 stack passwords
            'LANGFUSE_CLICKHOUSE_PASSWORD': self.generate_base64_password(12),
            'LANGFUSE_REDIS_PASSWORD': self.generate_base64_password(24),

            # S3/MinIO credentials
            'LANGFUSE_S3_ACCESS_KEY': self.generate_alphanumeric_key(20, uppercase=True),
            'LANGFUSE_S3_SECRET_KEY': self.generate_base64_password(30),
        }

    def load_template(self) -> str:
        """Load the .env.example template."""
        if not self.env_example.exists():
            raise FileNotFoundError(f".env.example not found at {self.env_example}")

        with open(self.env_example, 'r') as f:
            return f.read()

    def parse_generate_directive(self, comment_line: str) -> Optional[Dict[str, str]]:
        """Parse a GENERATE directive from a comment line.

        Expected format: # GENERATE: directive_type(args) | Manual: manual_instruction

        Returns dict with 'type', 'args', 'manual' or None if not a generate directive.
        """
        if '# GENERATE:' not in comment_line:
            return None

        try:
            parts = comment_line.split('|')
            generate_part = parts[0].split('GENERATE:')[1].strip()
            manual_part = parts[1].split('Manual:')[1].strip() if len(parts) > 1 else None

            # Parse directive type and arguments
            if '(' in generate_part and ')' in generate_part:
                directive_type = generate_part.split('(')[0].strip()
                args_str = generate_part.split('(')[1].split(')')[0].strip()
                # Remove quotes from args if present
                args = args_str.strip('"\'') if args_str else None
            else:
                directive_type = generate_part.strip()
                args = None

            return {
                'type': directive_type,
                'args': args,
                'manual': manual_part
            }
        except Exception:
            # Ignore malformed directives
            return None

    def parse_env_file_with_directives(self, content: str) -> Dict[str, Dict]:
        """Parse .env.example content and extract generation directives."""
        lines = content.split('\n')
        directives = {}

        for i, line in enumerate(lines):
            # Check if this line has a GENERATE directive
            directive = self.parse_generate_directive(line)
            if directive and i + 1 < len(lines):
                # Next line should be the actual env var
                next_line = lines[i + 1]
                if '=' in next_line and not next_line.strip().startswith('#'):
                    var_name = next_line.split('=')[0].strip()
                    directives[var_name] = directive

        return directives

    def generate_value_from_directive(self, directive: Dict[str, str], var_name: str,
                                     n8n_host: str, n8n_port: str, langfuse_host: str, langfuse_port: str) -> str:
        """Generate a value based on the directive type."""
        directive_type = directive['type']
        args = directive['args']

        if directive_type == 'strong_password':
            length = int(args) if args else 24
            return self.generate_strong_password(length)

        elif directive_type == 'hex_key':
            length = int(args) if args else 32
            return self.generate_hex_key(length)

        elif directive_type == 'base64_password':
            length = int(args) if args else 12
            return self.generate_base64_password(length)

        elif directive_type == 's3_access_key':
            length = int(args) if args else 20
            return self.generate_alphanumeric_key(length, uppercase=True)

        elif directive_type == 'template':
            if args == "http":
                return 'http' if n8n_host == 'localhost' else 'https'
            elif args == "localhost":
                return n8n_host
            elif args == "http://localhost:5678":
                return f'http://{n8n_host}:{n8n_port}' if n8n_host == 'localhost' else f'https://{n8n_host}'
            elif args == "http://localhost:9119":
                return f'http://{langfuse_host}:{langfuse_port}' if langfuse_host == 'localhost' else f'http://{langfuse_host}'
            else:
                return args

        elif directive_type == 'auto_detect_timezone':
            return self.get_timezone()

        elif directive_type == 'manual':
            # Skip manual values - they need to be set later
            return f"your_{var_name.lower()}_here"

        else:
            # Unknown directive, return placeholder
            return f"your_{var_name.lower()}_here"

    def replace_placeholders(self, template: str, values: Dict[str, str]) -> str:
        """Replace placeholder values in template with generated credentials."""
        content = template

        # Direct replacements for generated credentials
        replacements = {
            'your_super_secret_postgres_password': values['POSTGRES_PASSWORD'],
            'your_secret_postgres_password': values['POSTGRES_NON_ROOT_PASSWORD'],
            'your_super_secret_langfuse_password': values['LANGFUSE_DB_PASSWORD'],
            'your_encryption_key': values['N8N_ENCRYPTION_KEY'],
            'your_langfuse_nextauth_secret_here': values['LANGFUSE_NEXTAUTH_SECRET'],
            'your_langfuse_encryption_key_here': values['LANGFUSE_ENCRYPTION_KEY'],
            'your_langfuse_salt_here': values['LANGFUSE_SALT'],
            'your_secure_auth_token_here': values['MCP_AUTH_TOKEN'],
            'your_clickhouse_password': values['LANGFUSE_CLICKHOUSE_PASSWORD'],
            'your_redis_password': values['LANGFUSE_REDIS_PASSWORD'],
            'langfuse_access_key': values['LANGFUSE_S3_ACCESS_KEY'],
            'your_s3_secret_key': values['LANGFUSE_S3_SECRET_KEY'],
        }

        for old, new in replacements.items():
            content = content.replace(old, new)

        # Replace pgAdmin password specifically (to avoid replacing "admin" in email)
        content = re.sub(
            r'PGADMIN_DEFAULT_PASSWORD=admin',
            f'PGADMIN_DEFAULT_PASSWORD={values["PGADMIN_DEFAULT_PASSWORD"]}',
            content
        )

        return content

    def process_env_with_directives(self, template: str, dns: str, timezone: str,
                                   n8n_host: str, n8n_port: str, langfuse_host: str, langfuse_port: str,
                                   mcp_port: str, postgres_mcp_port: str) -> str:
        """Process .env template using GENERATE directives."""
        # Parse directives from template
        directives = self.parse_env_file_with_directives(template)

        # Process each line
        lines = template.split('\n')
        processed_lines = []

        for i, line in enumerate(lines):
            if '=' in line and not line.strip().startswith('#'):
                # This is an environment variable line
                var_name = line.split('=')[0].strip()

                if var_name in directives:
                    # Generate value based on directive
                    directive = directives[var_name]
                    new_value = self.generate_value_from_directive(
                        directive, var_name, n8n_host, n8n_port, langfuse_host, langfuse_port
                    )
                    processed_lines.append(f"{var_name}={new_value}")
                else:
                    # Handle special cases that need manual processing
                    if var_name == 'DNS_SERVER':
                        processed_lines.append(f"DNS_SERVER={dns}")
                    elif var_name == 'TIMEZONE':
                        processed_lines.append(f"TIMEZONE={timezone}")
                    elif var_name == 'N8N_PORT':
                        processed_lines.append(f"N8N_PORT={n8n_port}")
                    elif var_name == 'LANGFUSE_PORT':
                        processed_lines.append(f"LANGFUSE_PORT={langfuse_port}")
                    elif var_name == 'MCP_PORT':
                        processed_lines.append(f"MCP_PORT={mcp_port}")
                    elif var_name == 'POSTGRES_MCP_PORT':
                        processed_lines.append(f"POSTGRES_MCP_PORT={postgres_mcp_port}")
                    elif var_name == 'POSTGRES_MCP_DB':
                        processed_lines.append("POSTGRES_MCP_DB=n8n")
                    else:
                        # Keep original line
                        processed_lines.append(line)
            else:
                # Keep comment and other lines as-is
                processed_lines.append(line)

        return '\n'.join(processed_lines)

    def update_config_values(self, content: str, dns: str, timezone: str, n8n_host: str, n8n_port: str,
                             langfuse_host: str, langfuse_port: str, mcp_port: str, postgres_mcp_port: str) -> str:
        """Update configuration values in the content."""
        # Update DNS server
        content = re.sub(
            r'DNS_SERVER=.*',
            f'DNS_SERVER={dns}',
            content
        )

        # Update timezone
        content = re.sub(
            r'TIMEZONE=.*',
            f'TIMEZONE={timezone}',
            content
        )

        # Update n8n configuration
        # For localhost: use http protocol and include port in webhook URL
        # For custom domains: use https and no port (assumes reverse proxy)
        if n8n_host == 'localhost':
            n8n_protocol = 'http'
            n8n_webhook_url = f'http://localhost:{n8n_port}'
        else:
            n8n_protocol = 'https'
            n8n_webhook_url = f'https://{n8n_host}'

        content = re.sub(
            r'N8N_PROTOCOL=.*',
            f'N8N_PROTOCOL={n8n_protocol}',
            content
        )

        content = re.sub(
            r'N8N_HOST=.*',
            f'N8N_HOST={n8n_host}',
            content
        )

        content = re.sub(
            r'N8N_PORT=.*',
            f'N8N_PORT={n8n_port}',
            content
        )

        content = re.sub(
            r'N8N_WEBHOOK_URL=.*',
            f'N8N_WEBHOOK_URL={n8n_webhook_url}',
            content
        )

        # Update Langfuse URL - needs full URL with port for NextAuth
        langfuse_url = f'http://{langfuse_host}:{langfuse_port}' if langfuse_host == 'localhost' else f'http://{langfuse_host}'
        content = re.sub(
            r'LANGFUSE_URL=.*',
            f'LANGFUSE_URL={langfuse_url}',
            content
        )

        content = re.sub(
            r'LANGFUSE_PORT=.*',
            f'LANGFUSE_PORT={langfuse_port}',
            content
        )

        # Update MCP ports
        content = re.sub(
            r'MCP_PORT=.*',
            f'MCP_PORT={mcp_port}',
            content
        )

        content = re.sub(
            r'POSTGRES_MCP_PORT=.*',
            f'POSTGRES_MCP_PORT={postgres_mcp_port}',
            content
        )

        # Set POSTGRES_MCP_DB to match main database
        content = re.sub(
            r'POSTGRES_MCP_DB=.*',
            'POSTGRES_MCP_DB=n8n',
            content
        )

        return content

    def write_env_file(self, content: str, force: bool = False) -> bool:
        """Write the .env file with proper handling."""
        if self.env_file.exists() and not force:
            print(f"\n⚠️  ERROR: {self.env_file} already exists!")
            print("\n🛡️  For safety, this script will not overwrite existing .env files.")
            print("\n📋 To proceed, you must manually:")
            print("  • Backup your existing .env: cp .env .env.backup")
            print("  • Delete the existing .env: rm .env")
            print("  • Or use --force flag if you're certain: --force")
            print("\n❌ Setup terminated for safety.")
            return False

        # Write with appropriate line endings for the OS
        line_ending = '\r\n' if self.os_type == 'Windows' else '\n'
        content = content.replace('\r\n', '\n').replace('\n', line_ending)

        with open(self.env_file, 'w', newline='') as f:
            f.write(content)

        # Set appropriate permissions (Unix-like systems only)
        if self.os_type in ['Darwin', 'Linux']:
            os.chmod(self.env_file, 0o600)

        return True

    def print_summary(self, dns: str, timezone: str, n8n_host: str, n8n_port: str,
                      langfuse_host: str, langfuse_port: str, mcp_port: str, postgres_mcp_port: str):
        """Print configuration summary."""
        print("\n" + "="*60)
        print("📋 CONFIGURATION SUMMARY")
        print("="*60)
        print(f"🖥️  Operating System: {self.os_type}")
        print(f"🌐 DNS Server: {dns}")
        print(f"🕐 Timezone: {timezone}")
        print(f"📁 Environment File: {self.env_file}")
        print("\n📡 Service Endpoints:")
        print(f"  • n8n: {n8n_host}:{n8n_port}")
        print(f"  • Langfuse: {langfuse_host}:{langfuse_port}")
        print(f"  • n8n MCP: localhost:{mcp_port}")
        print(f"  • PostgreSQL MCP: localhost:{postgres_mcp_port}")
        print("="*60)

        print("\n✅ Credentials Generated via Directives:")
        print("  • Parsed GENERATE comments from .env.example")
        print("  • Auto-generated secure passwords and keys")
        print("  • Applied host-specific templates")
        print("  • Maintained manual instructions for reference")
        print("\n🔐 All credentials are cryptographically secure")
        print("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Setup environment for n8n pgvector stack',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Interactive setup
  %(prog)s --auto             # Use all defaults
  %(prog)s --dns 10.3.14.3    # Specify DNS server
  %(prog)s --force            # Overwrite existing .env without prompting
        """
    )

    parser.add_argument('--dns', help='DNS server IP address')
    parser.add_argument('--timezone', help='Timezone (e.g., America/New_York)')
    parser.add_argument('--n8n-host', default='localhost', help='n8n hostname (default: localhost)')
    parser.add_argument('--n8n-port', default='5678', help='n8n port (default: 5678)')
    parser.add_argument('--langfuse-host', default='localhost', help='Langfuse hostname (default: localhost)')
    parser.add_argument('--langfuse-port', default='9119', help='Langfuse port (default: 9119)')
    parser.add_argument('--mcp-port', default='8042', help='n8n MCP port (default: 8042)')
    parser.add_argument('--postgres-mcp-port', default='8700', help='PostgreSQL MCP port (default: 8700)')
    parser.add_argument('--auto', action='store_true', help='Use all defaults without prompting')
    parser.add_argument('--force', action='store_true', help='Overwrite existing .env without prompting')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without writing files')

    args = parser.parse_args()

    # Initialize setup
    base_dir = Path(__file__).parent
    setup = EnvSetup(base_dir)

    print("\n🚀 n8n PgVector Stack - Environment Setup")
    print("="*60)

    # Check for template
    if not setup.env_example.exists():
        print(f"❌ Error: .env.example not found at {setup.env_example}")
        print("Please ensure you're running this script from the project root.")
        sys.exit(1)

    # Determine configuration values
    if args.auto:
        dns = args.dns or setup.detect_dns_server()
        timezone = args.timezone or setup.get_timezone()
        n8n_host = args.n8n_host
        n8n_port = args.n8n_port
        langfuse_host = args.langfuse_host
        langfuse_port = args.langfuse_port
        mcp_port = args.mcp_port
        postgres_mcp_port = args.postgres_mcp_port
        print("🤖 Running in auto mode with detected/default values")
    else:
        # DNS Server
        detected_dns = setup.detect_dns_server()
        if args.dns:
            dns = args.dns
        else:
            dns_input = input(f"DNS Server [{detected_dns}]: ").strip()
            dns = dns_input if dns_input else detected_dns

        # Timezone
        detected_tz = setup.get_timezone()
        if args.timezone:
            timezone = args.timezone
        else:
            tz_input = input(f"Timezone [{detected_tz}]: ").strip()
            timezone = tz_input if tz_input else detected_tz

        # Use defaults for hosts and ports
        n8n_host = args.n8n_host
        n8n_port = args.n8n_port
        langfuse_host = args.langfuse_host
        langfuse_port = args.langfuse_port
        mcp_port = args.mcp_port
        postgres_mcp_port = args.postgres_mcp_port

    # Load and process template using directives
    print("📄 Processing template with directives...")
    template = setup.load_template()
    content = setup.process_env_with_directives(template, dns, timezone, n8n_host, n8n_port,
                                               langfuse_host, langfuse_port, mcp_port, postgres_mcp_port)

    # Print summary
    setup.print_summary(dns, timezone, n8n_host, n8n_port, langfuse_host, langfuse_port,
                       mcp_port, postgres_mcp_port)

    # Handle dry run
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No files written")
        print("\nGenerated .env would contain:")
        print("-"*40)
        # Show first few lines as preview
        lines = content.split('\n')[:20]
        for line in lines:
            if '=' in line and not line.startswith('#'):
                key = line.split('=')[0]
                print(f"{key}=<generated_value>")
            else:
                print(line)
        print("... (truncated)")
        return

    # Write the file
    if setup.write_env_file(content, args.force):
        print(f"\n✨ SUCCESS! Environment file created at {setup.env_file}")
        print("\n📝 Next steps:")
        print("  1. Review the generated .env file")
        print("  2. Run: docker compose up -d")
        print(f"  3. Access n8n at: http://{n8n_host}:{n8n_port}")
        if 'langfuse' in template.lower():
            print(f"  4. Access Langfuse at: http://{langfuse_host}:{langfuse_port}")
            print("  5. Create Langfuse S3 bucket at: http://localhost:9001")
        print("\n🔑 Generated Credentials:")
        print("  • pgAdmin: admin@example.com / <check .env for password>")
        print("  • All passwords are stored in the .env file")

        print("\n⚙️  Optional Configuration:")
        print("  • Ollama Integration:")
        print("    - Install Ollama on host: curl -fsSL https://ollama.com/install.sh | sh")
        print("    - Default settings use host.docker.internal:11434")
        print("    - See ollama/OLLAMA_INTEGRATION.md for setup guide")
        print("\n  • Remove unused services from .env:")
        print("    - Tableau MCP: Remove TABLEAU_* variables if not using Tableau")
        print("    - PostgreSQL MCP: Remove POSTGRES_MCP_PORT if not needed")
        print("    - pgAdmin: Remove PGADMIN_* variables if using other DB tools")
        print("\n  • Production/Custom DNS Setup:")
        print("    - Script auto-configures URLs for localhost (with ports)")
        print("    - For custom domains: edit .env to update URLs and protocol")
        print("    - Configure reverse proxy (nginx/traefik/cloudflare)")
        print("\n  • Enable Monitoring (Prometheus/Grafana):")
        print("    - Uncomment monitoring services in docker-compose.yml")
        print("    - Uncomment N8N_METRICS environment variables")
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
