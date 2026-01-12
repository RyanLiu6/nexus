# Deployment Guide

This guide covers the complete deployment process for Nexus. For other documentation, see:

- **[Architecture](ARCHITECTURE.md)** - System design, tech stack, and how components work together
- **[Runbooks](runbooks/)** - Service-specific configuration and troubleshooting
- **[README](../README.md)** - Project overview and quick reference

**New to Nexus?** Follow this guide from top to bottom for initial setup.

**Already deployed?** Jump to [Post-Deployment Configuration](#post-deployment-configuration) for optional features.

## Table of Contents

**Initial Setup:**
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Secrets Management](#secrets-management)
4. [Deploy Services](#deploy-services)
5. [Network Access Setup](#network-access-setup)

**Post-Deployment:**
6. [Post-Deployment Configuration](#post-deployment-configuration)
   - [Monitoring & Discord Alerts](#post-deployment-monitoring)
   - [Sure AI Features (Ollama/Cloud)](#post-deployment-sure-ai-features)
   - [Service-Specific Setup](#post-deployment-service-specific-setup)

**Operations:**
7. [Invoke Tasks](#invoke-tasks)
8. [Maintenance](#maintenance)
9. [Troubleshooting](#troubleshooting)

**Advanced:**
10. [Cloudflare Tunnel Details](#cloudflare-tunnel-details)

---

## Prerequisites

| Category | Requirement |
|----------|-------------|
| Hardware | 4+ cores, 16GB+ RAM, 500GB+ SSD |
| Network | Static local IP, ports 80/443 forwarded |
| Software | Docker 24.0+, Python 3.12+, uv |
| DNS | Domain with Cloudflare |

## Quick Start

### 1. Install System Dependencies

**macOS:**
```bash
brew install --cask docker
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Bootstrap

```bash
git clone <repo-url> ~/dev/nexus && cd ~/dev/nexus
./scripts/bootstrap
```

The bootstrap script installs: Python 3.12+, Ansible, Terraform, pre-commit hooks, and Python dependencies.

### 3. Data Directory

**macOS:**
```bash
mkdir -p ~/Data/{Config,Media}
echo "export DATA_DIRECTORY=$HOME/Data" >> ~/.zshrc && source ~/.zshrc
```

**Ubuntu:**
```bash
sudo mkdir -p /data/{Config,Media}
sudo chown -R $USER:$USER /data
echo "export DATA_DIRECTORY=/data" >> ~/.bashrc && source ~/.bashrc
```

---

## Secrets Management

Nexus uses `ansible-vault` for encrypted secrets. All secrets live in `ansible/vars/vault.yml`.

### Initial Setup

```bash
# Copy sample vault
cp ansible/vars/vault.yml.sample ansible/vars/vault.yml

# Edit with your secrets
nano ansible/vars/vault.yml

# Encrypt the vault (SAVE THIS PASSWORD!)
ansible-vault encrypt ansible/vars/vault.yml
```

### Required Secrets

See `ansible/vars/vault.yml.sample` for the complete list with inline documentation.

**Key secrets to configure:**

| Secret | Description | How to Generate |
|--------|-------------|-----------------|
| `nexus_domain` | Your domain (e.g., example.com) | - |
| `cloudflare_api_token` | Cloudflare API token (Zone:DNS:Edit, Zone:Zone:Read) | [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens) |
| `cloudflare_zone_id` | Cloudflare Zone ID | Domain Overview page on Cloudflare |
| `authelia_jwt_secret` | JWT signing key | `openssl rand -hex 32` |
| `authelia_session_secret` | Session encryption | `openssl rand -hex 32` |
| `authelia_storage_encryption_key` | Storage encryption | `openssl rand -hex 32` |
| `mysql_root_password` | Nextcloud database password | `openssl rand -base64 32` |
| `sure_postgres_password` | Sure database password | `openssl rand -base64 32` |
| `grafana_admin_password` | Grafana admin (initial setup + API access only) | `openssl rand -base64 24` |

**Optional:**
- `discord_webhook_url` - For Discord alerts (see [Monitoring Setup](#post-deployment-monitoring))
- Sure AI configuration - For automatic transaction categorization (see [Sure AI Setup](#post-deployment-sure-ai-features))

### Vault Commands

```bash
# View secrets (read-only)
ansible-vault view ansible/vars/vault.yml

# Edit secrets
ansible-vault edit ansible/vars/vault.yml

# Change vault password
ansible-vault rekey ansible/vars/vault.yml

# Decrypt to file (temporary, delete after!)
ansible-vault decrypt ansible/vars/vault.yml --output /tmp/vault-decrypted.yml
```

### Vault Password File (Optional)

The vault password file stores your **ansible-vault encryption password** (not your service passwords). This is the password that encrypts/decrypts `vault.yml`.

**Without it:** You'll be prompted for the vault password every time (`--ask-vault-pass`)
**With it:** Automation can access the vault without prompting

```bash
# Store your ansible-vault password
echo "your-vault-password" > ~/.vault_pass
chmod 600 ~/.vault_pass

# Use in automated deployments
ansible-playbook playbook.yml --vault-password-file ~/.vault_pass
```

**Security tradeoff:** Convenience (no password prompts) vs. storing decryption key on disk.

**Never commit vault password to git.**

---

## Deploy Services

After completing the bootstrap and configuring your vault.yml:

```bash
# Run setup (creates proxy network and vault.yml from sample)
invoke setup

# Edit and encrypt your vault.yml with secrets
nano ansible/vars/vault.yml
ansible-vault encrypt ansible/vars/vault.yml

# Deploy services using preset
invoke deploy --preset home

# Or deploy specific services
invoke deploy --services traefik,auth,dashboard
```

**Note:** If you already have a configured vault.yml, just run `invoke deploy --preset home`.

### How Deployment Works

1. **Terraform** updates Cloudflare DNS records for each service
2. **Ansible** generates the root `docker-compose.yml` by:
   - Reading the service preset
   - Combining individual `services/<name>/docker-compose.yml` files
   - Injecting secrets from `vault.yml`
   - Running `docker compose up -d`

The generated `docker-compose.yml` is not committed (it contains secrets).

### Authentication Architecture (SSO-First)

Nexus uses **Authelia** as the single sign-on (SSO) authentication layer. All services trust Authelia headers and do not require additional login prompts.

**How it works:**

1. **User accesses a service** (e.g., `grafana.yourdomain.com`)
2. **Traefik forwards to Authelia** for authentication
3. **Authelia checks permissions** against access control rules in `services/auth/configuration.yml`
   - ✅ **If authorized**: Authelia passes the request with user identity headers (`Remote-User`, `Remote-Email`, etc.)
   - ❌ **If denied**: User sees "Access Denied" and is redirected to `auth.yourdomain.com` (Authelia portal)
4. **Service receives request** with authenticated user info and grants access automatically (no additional login)

**Access Control:**

Configure per-service access rules in `services/auth/configuration.yml`. Users attempting to access services they don't have permission for will be denied at the Authelia layer before reaching the application.

For the dashboard to show only accessible services, configure your dashboard application to read Authelia's access control rules or user groups.

**Service-specific notes:**

- **Grafana**: Configured with auth proxy mode to trust Authelia headers. Admin credentials are only for initial setup and API access.
- **Transmission**: Built-in auth is disabled. Access controlled entirely by Authelia.
- **Nextcloud**: Has its own user management (users create accounts within Nextcloud), but access is still gated by Authelia.
- **FoundryVTT**: Has its own user/world management system (separate from Authelia SSO).

**Database credentials** (postgres, mysql) are separate infrastructure-level secrets and not user-facing.

---

## Post-Deployment Configuration

After deploying services, you'll want to configure optional features and service-specific settings.

### Post-Deployment: Monitoring

**Set up Discord alerts for your monitoring stack.**

Discord notifications keep you informed about service outages, high resource usage, and other critical events.

**Quick Setup:**

1. Create a Discord webhook in your server
2. Add `discord_webhook_url` to `vault.yml`
3. Start the alert bot: `invoke alert-bot`

**Full Instructions:** See [Monitoring Runbook - Discord Setup](runbooks/monitoring.md#discord-alerting-setup)

**What you'll get:**
- 🚨 Alerts when services go down
- ✅ Notifications when issues resolve
- ⚠️ Warnings for high CPU, memory, or disk usage
- 📊 Configurable alert rules and routing

### Post-Deployment: Sure AI Features

**Enable automatic transaction categorization with local or cloud AI.**

Sure supports multiple AI options - you can keep your financial data completely private with local Ollama, or use cloud providers for convenience.

**Option 1: Local AI with Ollama (Recommended for Privacy)**

Keep your financial data on your machine:

```bash
# Install Ollama
brew install ollama  # macOS

# Create custom financial model
cd services/sure
ollama pull qwen2.5:7b
ollama create ena -f Modelfile

# Configure in vault.yml
ansible-vault edit ansible/vars/vault.yml
```

Add to vault.yml:
```yaml
sure_openai_access_token: "ollama-local"
sure_openai_uri_base: "http://host.docker.internal:11434/v1"
sure_openai_model: "ena"
```

**Full Instructions:** See [Sure Ollama Setup Guide](../services/sure/docs/ollama-setup.md)

**Option 2: Cloud AI (OpenAI, Claude, Gemini, etc.)**

For convenience at the cost of sharing transaction data with AI providers:

```yaml
# OpenAI
sure_openai_access_token: "sk-proj-your-key"
sure_openai_model: "gpt-4"

# Or use OpenRouter for multiple providers
sure_openai_access_token: "sk-or-v1-your-key"
sure_openai_uri_base: "https://openrouter.ai/api/v1"
sure_openai_model: "deepseek/deepseek-chat"
```

**Full Instructions:** See [Sure AI Integration Guide](../services/sure/docs/ai-integration.md)

**Cost Comparison:**
- Local (Ollama): $0/month (uses your hardware)
- Deepseek: $2-5/month
- Claude API: $10-25/month
- OpenAI: $5-20/month

After configuring, redeploy:
```bash
invoke deploy --preset home
```

### Post-Deployment: Service-Specific Setup

Each service may have additional configuration options. See the individual runbooks:

| Service | Quick Start | Full Documentation |
|---------|-------------|-------------------|
| **Traefik** | Auto-configured | [runbooks/traefik.md](runbooks/traefik.md) |
| **Authelia** | Configure users in `configuration.yml` | [runbooks/authelia.md](runbooks/authelia.md) |
| **Monitoring** | Set up Discord alerts | [runbooks/monitoring.md](runbooks/monitoring.md) |
| **Sure** | Enable AI features | [runbooks/sure.md](runbooks/sure.md), [services/sure/docs/](../services/sure/docs/) |
| **Nextcloud** | Web setup wizard on first access | [runbooks/nextcloud.md](runbooks/nextcloud.md) |
| **Plex** | Claim server, add libraries | [runbooks/plex.md](runbooks/plex.md) |
| **Jellyfin** | Web setup wizard, add libraries | [runbooks/jellyfin.md](runbooks/jellyfin.md) |
| **FoundryVTT** | License key, world setup | [runbooks/foundryvtt.md](runbooks/foundryvtt.md) |
| **Transmission** | Configure download directories | [runbooks/transmission.md](runbooks/transmission.md) |
| **Backups** | Verify backup schedule | [runbooks/backups.md](runbooks/backups.md) |

**Browse all runbooks:** [docs/runbooks/](runbooks/)

---

## Network Access Setup

You have two options for exposing your services to the internet:

### Option 1: Cloudflare Tunnel (Recommended)

**Benefits:**
- No port forwarding needed
- No exposing your home IP address
- Works with CGNAT/dynamic IPs
- Ideal for Tailscale + Authelia setups

**Setup:**

```bash
# Install cloudflared
brew install cloudflare/cloudflare/cloudflared  # macOS
# Or download from GitHub releases for Linux

# Authenticate and create tunnel
cloudflared tunnel login
cloudflared tunnel create nexus

# Configure tunnel (create config.yml)
# Then run the tunnel
cloudflared tunnel run nexus
```

See "Cloudflare Tunnel (Alternative to Port Forwarding)" section below for details.

### Option 2: Traditional Port Forwarding

If you prefer traditional port forwarding:

1. Forward ports 80 and 443 to your server's local IP in your router settings
2. Ensure your public IP is set in `vault.yml` (Terraform will use this)
3. Run `invoke deploy` - Terraform automatically creates all DNS records:
   - A record: `@` → your public IP
   - Wildcard: `*` → your public IP
   - Subdomain records for each service

**No manual Cloudflare configuration needed** - Terraform handles all DNS records.

### Verification

After deployment, verify Traefik is accessible:
- With Cloudflare Tunnel: `https://traefik.yourdomain.com/dashboard`
- With port forwarding: Same URL, but traffic routes through your router

---

## Invoke Tasks

```bash
invoke --list                    # Show all tasks

# Deployment
invoke deploy --preset home      # Deploy home preset
invoke up                        # Start containers
invoke down                      # Stop containers
invoke restart                   # Restart containers
invoke pull                      # Pull latest images

# Development
invoke lint                      # Run linters
invoke format                    # Format code
invoke test                      # Run tests
invoke test --coverage           # With coverage report

# Health & Operations
invoke health --domain example.com
invoke ops --daily               # Container health, disk check
invoke ops --weekly              # Backup verification, cleanup
invoke backup-list               # List available backups

# Infrastructure
invoke ansible-run               # Run Ansible playbook
invoke ansible-check             # Syntax check
invoke tf-init                   # Initialize Terraform
invoke tf-plan                   # Show Terraform plan
invoke tf-apply                  # Apply Terraform changes
```

---

## Maintenance

### Updates

```bash
# Pull latest images and restart
invoke pull && invoke up

# Or manually
docker compose pull
docker compose up -d
```

### Cleanup

```bash
# Remove unused Docker resources
docker system prune -a

# Remove unused volumes (careful - data loss!)
docker volume prune

# Check disk usage
df -h
docker system df
```

### Backups

```bash
# List backups
invoke backup-list

# Manual config backup
tar -czf nexus-configs-$(date +%Y%m%d).tar.gz services/*/configuration.yml

# Database backup (Sure)
docker compose exec sure-db pg_dump -U sure_user sure_production > sure-backup.sql
```

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| Services won't start | `invoke logs --service <name>`, check service-specific runbook |
| SSL issues | Delete `services/traefik/letsencrypt/*`, restart traefik |
| Authelia login loop | Check domain in config, verify Redis is running |
| Permission errors (macOS) | `sudo chown -R $USER:staff /Volumes/Data` |
| Permission errors (Linux) | `sudo chown -R $USER:$USER /data` |
| Vault password wrong | Check password manager, or recreate vault |
| Terraform state lost | Re-import resources or start fresh |
| Discord alerts not working | See [Monitoring Runbook - Troubleshooting](runbooks/monitoring.md#troubleshooting-discord-alerts) |
| Sure AI not working | Check API keys, see [Sure Runbook](runbooks/sure.md) |

### Service-Specific Troubleshooting

For detailed troubleshooting of individual services, see the runbooks:

- **[Traefik](runbooks/traefik.md)** - Proxy and SSL certificate issues
- **[Authelia](runbooks/authelia.md)** - Authentication and SSO issues
- **[Monitoring](runbooks/monitoring.md)** - Prometheus, Grafana, alerts
- **[Sure](runbooks/sure.md)** - Database, AI, transaction issues
- **[Nextcloud](runbooks/nextcloud.md)** - File sync, database issues
- **[Plex](runbooks/plex.md)** - Media library, transcoding issues
- **[Jellyfin](runbooks/jellyfin.md)** - Streaming and library issues
- **[FoundryVTT](runbooks/foundryvtt.md)** - Game world and module issues
- **[Transmission](runbooks/transmission.md)** - Download and permissions issues
- **[Backups](runbooks/backups.md)** - Backup failures and restoration

**View all runbooks:** [docs/runbooks/](runbooks/)

### Getting Logs

```bash
# Via invoke
invoke logs --service traefik
invoke logs --service auth --follow

# Via docker
docker compose logs traefik --tail 100
docker compose logs -f auth
```

### Health Check

```bash
invoke health --domain yourdomain.com --verbose
```

---

## Cloudflare Tunnel Details

Cloudflare Tunnel creates a secure outbound connection from your server to Cloudflare's network, eliminating the need for port forwarding.

### Installation

**macOS:**
```bash
brew install cloudflare/cloudflare/cloudflared
```

**Ubuntu/Debian:**
```bash
# Download latest release
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

### Setup

```bash
# 1. Authenticate with Cloudflare
cloudflared tunnel login

# 2. Create a tunnel
cloudflared tunnel create nexus

# 3. Create tunnel configuration
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

**Example config.yml:**
```yaml
tunnel: nexus
credentials-file: /home/user/.cloudflared/TUNNEL-UUID.json

ingress:
  - hostname: "*.yourdomain.com"
    service: http://localhost:80
  - hostname: yourdomain.com
    service: http://localhost:80
  - service: http_status:404
```

### Running the Tunnel

```bash
# Test the tunnel
cloudflared tunnel run nexus

# Run as a service (recommended)
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

### DNS Setup

After creating the tunnel, point your DNS to it:

```bash
# Route all traffic through the tunnel
cloudflared tunnel route dns nexus yourdomain.com
cloudflared tunnel route dns nexus "*.yourdomain.com"
```

Or manually create CNAME records in Cloudflare:
- `@` → `TUNNEL-UUID.cfargotunnel.com`
- `*` → `TUNNEL-UUID.cfargotunnel.com`

### Benefits

- **No open ports:** All traffic routed through Cloudflare
- **Dynamic IP friendly:** Works behind CGNAT, no static IP needed
- **DDoS protection:** Cloudflare handles malicious traffic
- **Easy management:** Control access through Cloudflare dashboard
