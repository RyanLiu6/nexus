# Nexus Architecture

## What is Nexus?

Nexus is a self-hosted homelab solution that provides:

- **Centralized access** to all services via a single dashboard
- **Secure authentication** with Tailscale (Network & Service level)
- **Automated DNS** via Terraform + Cloudflare
- **Containerized services** managed by Ansible + Docker Compose

## Features Checklist

| Feature | Status | Description |
|---------|--------|-------------|
| Dashboard | ✅ | Homepage with links to all services |
| Tailscale Auth | ✅ | Network and service-level access control |
| User Groups | ✅ | Access control via Tailscale ACLs |
| Auto SSL | ✅ | Let's Encrypt via Traefik |
| DNS Management | ✅ | Terraform + Cloudflare |
| Health Checks | ✅ | Docker healthchecks on all services |
| Monitoring | ✅ | Prometheus + Grafana |
| Alerting | ✅ | Discord webhook alerts |
| Backups | ✅ | Backrest automated backups |
| Media Server | ✅ | Jellyfin (primary), Plex (optional) |
| Gaming | ✅ | FoundryVTT for D&D |
| Finance | ✅ | Sure for budgeting |
| Passwords | ✅ | Vaultwarden (Bitwarden) |
| Tasks | ✅ | Donetick for chores/tasks |

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Runtime | Docker + Docker Compose | Container orchestration |
| Proxy | Traefik | Reverse proxy, SSL, routing |
| Auth | Tailscale + Header Auth | Network security & Identity |
| DNS | Terraform + Cloudflare | DNS record management |
| Config | Ansible | Docker Compose generation |
| Secrets | Ansible Vault | Encrypted credentials |
| VPN | Tailscale | Secure remote access |
| CLI | Python + Invoke | User interface |

---

## Deployment Flow

```
User runs: invoke deploy --preset home
    │
    ├── 1. Python validates config and services
    │
    ├── 2. Terraform updates Cloudflare DNS
    │       └── Creates A/CNAME records for each service
    │
    ├── 3. Ansible runs playbook
    │       ├── Reads services from preset
    │       ├── Combines individual docker-compose.yml files
    │       ├── Generates root docker-compose.yml from template
    │       └── Runs docker compose up -d
    │
    └── 4. Services start with health checks
```

### docker-compose.yml Generation

Ansible generates the root `docker-compose.yml` by combining individual service files:

1. Each service has its own `services/<name>/docker-compose.yml`
2. Ansible reads the preset to determine which services to include
3. The `ansible/roles/nexus/templates/docker-compose.yml.j2` template combines them
4. Variables from `vault.yml` are injected (domains, passwords, etc.)
5. Final `docker-compose.yml` is written to the project root

This allows:
- Individual service files to be version controlled
- Secrets to remain encrypted in vault.yml
- Different presets (core, home) to generate different compositions

---

## Traffic Flow

```
Internet → Cloudflare DNS → Cloudflare Tunnel → FoundryVTT (Public)

Tailscale → Device (100.x.x.x) → Traefik → tailscale-access → Service
                                                 ↓
                                         Check Group Access
```

---

## Monitoring & Alerting

### Stack

| Component | Purpose |
|-----------|---------|
| **Prometheus** | Metrics collection and storage |
| **Grafana** | Dashboards and visualization |
| **Alertmanager** | Alert routing and deduplication |
| **Discord Bot** | Receives alerts, posts to Discord |

### Alert Flow

```
Service (down/high CPU) → Prometheus → Alert Rule → Alertmanager → Webhook → Discord
```

### Setting Up Alerts

See [DEPLOYMENT.md - Discord Alerting](DEPLOYMENT.md#advanced-discord-alerting) for setup instructions.

**Alert types:**
- Service down > 5 minutes
- High CPU/memory/disk usage
- Container restart loops

---

## Service Presets

```python
PRESETS = {
    "core": ["traefik", "tailscale-access", "dashboard", "monitoring", "vaultwarden"],
    "home": ["core", "backups", "sure", "foundryvtt", "jellyfin", "transmission", "donetick"],
}
```

## Services

| Service | Purpose | Access |
|---------|---------|--------|
| **traefik** | Reverse proxy, SSL | Admin (Tailscale) |
| **tailscale-access**| Auth Middleware | Internal |
| **dashboard** | Homepage | Admin/Member (Tailscale) |
| **monitoring** | Prometheus + Grafana | Admin (Tailscale) |
| **jellyfin** | Media server | Admin |
| **plex** | Media streaming | Admin + Wife |
| **transmission** | Torrent client | Admin |
| **foundryvtt** | Virtual tabletop | Admin + Gaming |
| **sure** | Finance tracking | Admin + Wife |
| **donetick** | Chore tracker | Admin + Family |
| **vaultwarden** | Password manager | Admin |
| **backups** | Backrest | Automated |

---

## Directory Structure

```
nexus/
├── ansible/                  # Configuration management
│   ├── playbook.yml          # Main Ansible playbook
│   ├── roles/nexus/          # Service deployment role
│   │   ├── tasks/main.yml
│   │   └── templates/        # docker-compose.yml.j2
│   └── vars/
│       └── vault.yml.sample  # Template for secrets
│
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md       # This file
│   ├── DEPLOYMENT.md         # Setup instructions
│   ├── ACCESS_CONTROL.md     # Auth, Tailscale, SSH
│   └── DNS_FILTERING.md      # Cloudflare Gateway setup
│
├── scripts/
│   └── bootstrap             # Initial setup script
│
├── services/                 # Service definitions
│   ├── traefik/
│   ├── tailscale-access/     # Auth middleware
│   ├── dashboard/
│   ├── monitoring/
│   ├── vaultwarden/
│   ├── donetick/
│   └── ...
│
├── src/nexus/                # Python library
│   ├── cli/                  # CLI entry points
│   ├── config.py             # Presets and configuration
│   ├── deploy/               # Ansible, Terraform, Docker
│   ├── generate/             # Config generation
│   ├── health/               # Health checks
│   ├── operations/           # Maintenance tasks
│   ├── alerts/               # Discord alert bot
│   └── restore/              # Backup restoration
│
├── terraform/                # DNS and Cloudflare management
│   ├── main.tf
│   ├── cloudflare_dns.tf
│   └── cloudflare_gateway.tf # Zero Trust Gateway policies
│
├── tasks.py                  # Invoke task definitions
└── pyproject.toml            # Python project config
```

---

## Secrets Management

All secrets stored in `ansible/vars/vault.yml` (encrypted with ansible-vault).

### Required Secrets

```yaml
# Domain and DNS
nexus_domain: "example.com"
cloudflare_api_token: "..."
cloudflare_zone_id: "..."

# Databases
postgres_password: "..."
sure_db_password: "..."

# Alerting
discord_webhook_url: "..."
```

### Generating Secrets

```bash
# Random 64-char secret
openssl rand -hex 32

# Traefik password hash
htpasswd -nb admin password | sed 's/\$/\$\$/g'
```

### Vault Commands

```bash
# Create encrypted vault
ansible-vault create ansible/vars/vault.yml

# Edit secrets
ansible-vault edit ansible/vars/vault.yml

# View secrets
ansible-vault view ansible/vars/vault.yml
```

**Store your vault password securely** (password manager). If lost, you must recreate all secrets.

---

## Limitations

- **Single machine** - No high availability
- **Docker Desktop NAT** - Tailscale bypass may not work on macOS
- **Manual initial setup** - Tailscale ACLs, initial certificates
