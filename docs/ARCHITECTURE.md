# Nexus Architecture

## What is Nexus?

Nexus is a self-hosted homelab solution that provides:

- **Centralized access** to all services via a single dashboard
- **Secure authentication** with Tailscale (Network & Service level)
- **Automated DNS** via OpenTofu + Cloudflare
- **Containerized services** managed by PyInfra + Docker Compose

## Features Checklist

| Feature | Status | Description |
|---------|--------|-------------|
| Dashboard | ✅ | Authentik Dashboard with SSO to all services |
| Tailscale Auth | ✅ | Network and service-level access control |
| User Groups | ✅ | Access control via Tailscale ACLs |
| Auto SSL | ✅ | Let's Encrypt via Traefik |
| DNS Management | ✅ | OpenTofu + Cloudflare |
| Health Checks | ✅ | Docker healthchecks on all services |
| Monitoring | ✅ | Beszel + Uptime Kuma |
| Alerting | ✅ | Discord webhook alerts |
| Backups | ✅ | Backrest automated backups |
| Media Server | ✅ | Jellyfin (primary), Virtue (secondary) |
| Gaming | ✅ | FoundryVTT for D&D |
| Finance | ✅ | Sure for budgeting |
| Documents | ✅ | Paperless-ngx for document management |
| Books | ✅ | BookOrbit for book library |
| Smart Home | ✅ | Home Assistant OS (HAVM) |

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Runtime | Docker Compose + macOS Virtualization (HAVM) | Container & VM orchestration |
| Proxy | Traefik | HTTP→HTTPS redirect, reverse proxy, SSL, routing |
| Auth | Authentik (OIDC) + Headscale | Network security & Identity |
| DNS | OpenTofu + Cloudflare | DNS record management |
| Config | PyInfra | Docker Compose generation |
| VPN | Headscale + Tailscale | Self-hosted control server & secure remote access |
| CLI | Python + Invoke | User interface |

---

## Deployment Flow

```
User runs: invoke deploy --preset home
    │
    ├── 1. Python validates config and services
    │
    ├── 2. OpenTofu updates Cloudflare DNS
    │       └── Creates A/CNAME records for each service
    │
    ├── 3. PyInfra runs playbook
    │       ├── Reads services from preset
    │       ├── Combines individual docker-compose.yml files
    │       ├── Generates root docker-compose.yml from template
    │       └── Runs docker compose up -d
    │
    └── 4. Services start with health checks
```

### docker-compose.yml Generation

PyInfra generates the root `docker-compose.yml` by combining individual service files:

1. Each service has its own `services/<name>/docker-compose.yml`
2. PyInfra reads the preset to determine which services to include
3. The `pyinfra/roles/nexus/templates/docker-compose.yml.j2 (PyInfra Jinja)` template combines them
4. Variables from `secrets.enc.yml` are injected (domains, passwords, etc.)
5. Final `docker-compose.yml` is written to the project root

This allows:
- Individual service files to be version controlled
- Secrets to remain encrypted in secrets.enc.yml
- Different presets (core, home) to generate different compositions

---

## Traffic Flow

```
Internet → Router Port Forwarding (443) → Traefik → FoundryVTT / Headscale (Public)

Tailscale → Device (100.x.x.x) → Traefik → authentik → Docker Services
                                   │              ↓
                                   │      Check Group Access
                                   │
                                   └── File Provider (rules/) → HAVM (Home Assistant OS)
```

---

## Monitoring & Alerting

### Stack

| Component | Purpose |
|-----------|---------|
| **Beszel (Hub + Agent)** | Host CPU, RAM, disk, network, and per-container Docker metrics & alerts |
| **Uptime Kuma** | HTTP/HTTPS service uptime, TLS certificate expiry, HAVM `/health` check, and Docker container health |

### Alert Flow

```
Beszel / Uptime Kuma → Native Discord Webhook (auto-synced from SOPS on deploy)
```

### Setting Up Alerts

See [DEPLOYMENT.md - Discord Alerts](DEPLOYMENT.md#optional-discord-alerts) for setup instructions.

**Alert types:**
- Host/system down, high CPU/memory/disk usage (Beszel)
- HTTPS endpoint down, TLS cert expiring, HAVM health check failed, container down (Uptime Kuma)

---

## Service Presets

```python
PRESETS = {
    "core": ["traefik", "headscale", "ddns", "beszel", "uptime-kuma", "homeassistant", "scrypted", "fregata"],
    "home": ["core", "backups", "paperless", "bookorbit", "foundryvtt", "jellyfin", "gluetun", "transmission", "authentik", "tailscale-proton", "teslamate"],
}
```

## Services

| Service | Purpose | Access |
|---------|---------|--------|
| **traefik** | Reverse proxy, SSL | Admin (Tailscale) |
| **authentik** | Identity Provider | Admin/Members |
| **beszel** | Host & Docker container monitoring | Admin (Tailscale) |
| **uptime-kuma** | HTTP/TLS/container uptime monitoring | Admin (Tailscale) |
| **jellyfin** | Media server | Admin |
| **virtue** | Media server (secondary Jellyfin) | Admin |
| **transmission** | Torrent client | Admin |
| **foundryvtt** | Virtual tabletop | Admin + Gaming |
| **sure** | Finance tracking | Admin + Wife |
| **paperless** | Document management | Admin |
| **bookorbit** | Book library | Admin |
| **homeassistant** | Smart home hub (HAVM) | Admin |
| **backups** | Backrest | Automated |

---

## Directory Structure

```
nexus/
├── pyinfra/                  # Configuration management
│   ├── playbook.yml          # Main PyInfra playbook
│   ├── roles/nexus/          # Service deployment role
│   │   ├── tasks/main.yml
│   │   └── templates/        # docker-compose.yml.j2
│   └── vars/
│       └── secrets.enc.yml.sample  # Template for secrets
│
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md       # This file
│   ├── DEPLOYMENT.md         # Setup instructions
│   ├── ACCESS_CONTROL.md     # Auth, Tailscale, SSH
│   ├── DNS_FILTERING.md      # Cloudflare Gateway setup
│   └── haos-havm-setup.md    # Home Assistant OS with HAVM setup
│
├── scripts/
│   └── bootstrap             # Initial setup script
│
├── services/                 # Service definitions
│   ├── traefik/              # Reverse proxy & dynamic rules
│   ├── authentik/            # SSO and OIDC Identity Provider
│
│   ├── monitoring/
│   ├── homeassistant/        # HAVM config & LaunchAgents
│   ├── paperless/
│   ├── bookorbit/
│   └── ...
│
├── src/nexus/                # Python library
│   ├── cli/                  # CLI entry points
│   ├── config.py             # Presets and configuration
│   ├── deploy/               # PyInfra, OpenTofu, Docker
│   ├── generate/             # Config generation
│   ├── health/               # Health checks
│   ├── operations/           # Maintenance tasks
│   ├── alerts/               # Discord alert bot
│   └── restore/              # Backup restoration
│
├── terraform/                # DNS and Cloudflare management (OpenTofu)
│   ├── main.tf
│   ├── cloudflare_dns.tf
│   └── cloudflare_gateway.tf # Zero Trust Gateway policies
│
├── tasks.py                  # Invoke task definitions
└── pyproject.toml            # Python project config
```

---

## Secrets Management

All secrets stored in `config/secrets.enc.yml` (encrypted with sops).

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
sops create config/secrets.enc.yml

# Edit secrets
sops edit config/secrets.enc.yml

# View secrets
sops view config/secrets.enc.yml
```

**Store your age key (or SOPS decryption key) securely** (password manager). If lost, you must recreate all secrets.

---

## Limitations

- **Single machine** - No high availability
- **Docker Desktop NAT** - Tailscale bypass may not work on macOS
- **Manual initial setup** - Tailscale ACLs, initial certificates
