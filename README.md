# Nexus

Self-hosted homelab for personal services, media streaming, and productivity tools.

## What It Does

- **Dashboard** - Single homepage to access all services
- **Authentication** - Authelia SSO with 2FA, user groups
- **VPN Access** - Tailscale bypasses auth for admin
- **Media** - Jellyfin/Plex streaming, Transmission downloads
- **Apps** - FoundryVTT (D&D), Sure (finance), Nextcloud (files)
- **Monitoring** - Prometheus + Grafana + Discord alerts
- **Backups** - Automated with Borgmatic

## Tech Stack

| Component | Technology |
|-----------|------------|
| Runtime | Docker Compose |
| Proxy | Traefik (SSL, routing) |
| Auth | Authelia (SSO, 2FA) |
| DNS | Terraform + Cloudflare |
| Config | Ansible (generates docker-compose.yml) |
| Secrets | Ansible Vault |
| CLI | Python + Invoke |

## Quick Start

```bash
# 1. Clone and bootstrap
git clone <repo-url> ~/dev/nexus && cd ~/dev/nexus
./scripts/bootstrap

# 2. Configure secrets
cp ansible/vars/vault.yml.sample ansible/vars/vault.yml
nano ansible/vars/vault.yml
ansible-vault encrypt ansible/vars/vault.yml

# 3. Deploy
docker network create proxy
invoke deploy --preset home
```

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

**Core:** traefik, auth, dashboard, monitoring
**Media:** jellyfin, plex, transmission
**Apps:** foundryvtt, sure, nextcloud
**Utils:** backups

## Access Control

| Group | Access | Auth |
|-------|--------|------|
| admin | All services | 2FA + Tailscale bypass |
| gaming | FoundryVTT | 1FA |
| wife | Plex, Sure | 1FA |

## Documentation

| Doc | Contents |
|-----|----------|
| [Architecture](docs/ARCHITECTURE.md) | Features, tech stack, deployment flow, docker-compose generation, monitoring & alerting, secrets |
| [Deployment](docs/DEPLOYMENT.md) | Setup, secrets management, invoke tasks, maintenance |
| [Access Control](docs/ACCESS_CONTROL.md) | Authelia, Tailscale, SSH, user groups |
| [Runbooks](docs/runbooks/) | Troubleshooting per service |

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
