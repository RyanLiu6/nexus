# Nexus

Collection of self-hosted services for my personal multi-media home server.

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md) - System architecture and components
- [Deployment Guide](docs/DEPLOYMENT.md) - Complete deployment instructions
- [Access Control](docs/ACCESS_CONTROL.md) - User groups and permissions
- [Secrets Management](docs/SECRETS.md) - Ansible-vault setup guide
- [Alerting Setup](docs/ALERTING.md) - Discord bot and Grafana alerts
- [Security & Access Control](docs/SECURITY.md) - Authentication and authorization
- [Tailscale Integration](docs/TAILSCALE.md) - VPN-based secure access
- [SSH Access Guide](docs/SSH_ACCESS.md) - Traditional and Tailscale SSH setup
- [Runbooks](docs/runbooks/) - Service-specific troubleshooting

## Quick Start

```bash
# 1. Install dependencies
uv pip install -e .

# 2. Generate secrets and encrypt them
./scripts/generate-secrets.sh

# 3. Encrypt vault file
ansible-vault encrypt ansible/vars/vault.yml

# 4. Deploy services (Terraform + Ansible)
./scripts/deploy.py -p home

# 5. Or deploy everything manually
./scripts/deploy.py -p home --skip-dns --skip-ansible
docker compose up -d
```

For detailed deployment instructions, see:
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Secrets Management](docs/SECRETS.md)
- [Access Control](docs/ACCESS_CONTROL.md)

## Services

### Core
- [traefik](services/traefik/) - Reverse proxy and SSL management
- [auth](services/auth/) - Authelia SSO and 2FA
- [dashboard](services/dashboard/) - Homepage dashboard

### Content
- [plex](services/plex/) - Media streaming
- [jellyfin](services/jellyfin/) - Media server
- [nextcloud](services/nextcloud/) - File storage
- [transmission](services/transmission/) - Torrent client

### Games
- [foundryvtt](services/foundryvtt/) - [FoundryVTT](https://foundryvtt.com/), Virtual Tabletop

### Finance
- [sure](services/sure/) - Self-hosted finance and budgeting tool

### Utilities
- [backups](services/backups/) - Automated backups with Borgmatic

## Scripts

All scripts use Python and are managed with `uv`.

### Setup

```bash
# Install all dependencies
./scripts/bootstrap.sh

# Generate secure passwords and create vault
./scripts/generate-secrets.sh

# Encrypt vault
ansible-vault encrypt ansible/vars/vault.yml
```

### Monitoring

```bash
# Run health check
./scripts/health_check.py --domain ryanliu6.xyz

# Run maintenance tasks
./scripts/operations.py --all
```

### Deployment
```bash
./scripts/deploy.py [options] [services]

Options:
  -p, --preset PRESET    Use service preset (default, home)
  -a, --all              Deploy all services
  -d, --domain DOMAIN      Set base domain
  --skip-dns              Skip Terraform DNS management
  --skip-ansible           Skip Ansible deployment
  -v, --verbose           Verbose output

Examples:
  ./scripts/deploy.py -p home                    # Deploy home preset
  ./scripts/deploy.py plex jellyfin              # Deploy specific services
  ./scripts/deploy.py --all --skip-dns          # Deploy all, skip DNS
```

### Configuration Generation
```bash
./scripts/generate_dashboard.py [options] [services]

Options:
  -p, --preset PRESET    Use service preset
  -a, --all              Generate for all services
  -d, --domain DOMAIN      Set base domain
  -v, --verbose           Verbose output

Examples:
  ./scripts/generate_dashboard.py -p home                   # Generate home preset
  ./scripts/generate_dashboard.py plex jellyfin               # Generate specific services
```

### Health Checks
```bash
./scripts/health_check.py [options]

Options:
  -d, --domain DOMAIN      Base domain for SSL checks
  --critical-only          Only check critical services
  --alert-webhook URL     Send alerts to webhook
  -v, --verbose           Verbose output

Examples:
  ./scripts/health_check.py --domain ryanliu6.xyz
  ./scripts/health_check.py --critical-only
```

### Backup & Restore
```bash
# Restore from backup
./scripts/restore.py [options]

Options:
  --list                  List available backups
  --backup BACKUP        Backup file to restore
  --service SERVICE       Specific service to restore
  --db DB_FILE            Restore database from SQL file
  --verify                Verify backup integrity

Examples:
  ./scripts/restore.py --list
  ./scripts/restore.py --backup nexus-backup-20250111.tar.gz
  ./scripts/restore.py --verify --backup nexus-backup.tar.gz
```

### Alert Bot
```bash
./scripts/alert_bot.py [options]

Options:
  --config PATH           Path to config file
  --port PORT             Webhook server port (default: 8080)

Examples:
  ./scripts/alert_bot.py --config alert_bot_config.yml
  ./scripts/alert_bot.py --port 8080
```

## Environment Variables

Set these in `.env` or as environment variables:

```bash
# Nexus Configuration
NEXUS_ROOT_DIRECTORY=/path/to/nexus          # Default: $HOME/dev/focus
NEXUS_BACKUP_DIRECTORY=/path/to/backups     # Default: $HOME/nexus-backups
NEXUS_DOMAIN=yourdomain.xyz                   # Base domain

# Cloudflare (for Terraform DNS)
CLOUDFLARE_API_TOKEN=your_token
CLOUDFLARE_ZONE_ID=your_zone_id

# Alerting (Discord)
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_CHANNEL_ID=your_channel_id
DISCORD_WEBHOOK_URL=your_webhook_url

# Monitoring
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_password
```

## Development

### Setup

```bash
# Install dependencies with uv
uv pip install -e ".[dev]"

# Run linter
uv run ruff check src/ scripts/

# Format code
uv run ruff format src/ scripts/

# Run tests
uv run pytest
```

## Architecture

Nexus uses a hybrid approach:

- **Terraform**: Cloud infrastructure (DNS, future R2)
- **Ansible**: Configuration management (Docker, system setup)
- **Python Scripts**: Orchestration and utilities

See [Architecture Overview](docs/ARCHITECTURE.md) for details.

## Access Control

### User Groups

- **admin**: Full access to all services (you)
- **gaming**: FoundryVTT access only (friends)
- **wife**: Plex + Sure access only

### Access Methods

1. **Public Internet**: Authelia SSO required
2. **Tailscale VPN**: Full bypass, access to everything
3. **SSH**: Key-based or Tailscale SSH

See [Security Documentation](docs/SECURITY.md) for details.

## Troubleshooting

Service-specific troubleshooting guides in [docs/runbooks/](docs/runbooks/):

- [Plex](docs/runbooks/plex.md)
- [Jellyfin](docs/runbooks/jellyfin.md)
- [Authelia](docs/runbooks/authelia.md)
- [Transmission](docs/runbooks/transmission.md)

## License

MIT
