# Nexus

Self-hosted homelab for personal services, media streaming, and productivity tools.

## What It Does

- **Dashboard** - Single homepage to access all services
- **Authentication** - Tailscale Access Control (Gatekeeper) + Header Auth
- **Media** - Jellyfin/Plex streaming, Transmission downloads
- **Apps** - FoundryVTT (D&D), Sure (finance), Nextcloud (files), Paperless-ngx (documents), Booklore (books)
- **Security** - Vaultwarden (Bitwarden) password manager
- **Monitoring** - Prometheus + Grafana + Discord alerts
- **Backups** - Automated with Borgmatic

## Tech Stack

| Component | Technology |
|-----------|------------|
| Runtime | Docker Compose |
| Proxy | Traefik (SSL, routing) |
| Auth | Tailscale + tailscale-access |
| DNS | Terraform + Cloudflare |
| Config | Ansible (generates docker-compose.yml) |
| Secrets | Ansible Vault |
| CLI | Python + Invoke |

## Quick Start

```bash
# 1. Clone and bootstrap
git clone <repo-url> ~/dev/nexus && cd ~/dev/nexus
./scripts/bootstrap

# 2. Activate virtual environment
# Option A: Using direnv (recommended) - auto-activates on cd
echo "layout uv" > .envrc && direnv allow
# Option B: Manual activation
source .venv/bin/activate

# 3. Setup and configure secrets
invoke setup
nano ansible/vars/vault.yml   # Add your domain, Cloudflare creds, and Tailscale users

# 4. Deploy everything
invoke deploy
```

The deploy command handles vault encryption, Terraform, cloudflared, and Ansible automatically.

> **Tip:** For a complete shell setup with direnv + uv integration, see [RyanLiu6/setup](https://github.com/RyanLiu6/setup).

## Invoke Commands

```bash
invoke --list                    # Show all tasks

invoke deploy --preset home      # Deploy services
invoke up / down / restart       # Container lifecycle
invoke logs --service traefik    # View logs

invoke lint                      # Run linters
invoke test                      # Run tests

invoke health --domain example.com
invoke ops --daily               # Daily maintenance
```

## Services

**Core:** traefik, tailscale-access, dashboard, monitoring, vaultwarden
**Media:** jellyfin, plex, transmission
**Apps:** foundryvtt, sure, nextcloud, paperless, booklore
**Utils:** backups

## Access Control

| Group | Access | Auth |
|-------|--------|------|
| admin | All services | Tailscale + SSH |
| members | FoundryVTT, Homepage | Tailscale |

## Documentation

| Doc | Contents |
|-----|----------|
| [Deployment](docs/DEPLOYMENT.md) | Step-by-step setup guide, invoke tasks, maintenance |
| [Architecture](docs/ARCHITECTURE.md) | Features, tech stack, deployment flow, monitoring & alerting |
| [Access Control](docs/ACCESS_CONTROL.md) | Tailscale ACLs, Gatekeeper, Header Auth |

Each service also has its own README in `services/<name>/README.md`.

## Project Structure

```
nexus/
├── ansible/            # Playbooks, roles, vault.yml
├── docs/               # Documentation
├── scripts/            # Bootstrap script
├── services/           # Docker Compose per service
├── src/nexus/          # Python library
├── terraform/          # Cloudflare DNS
├── tasks.py            # Invoke tasks
└── pyproject.toml      # Python config
```

## License

MIT
