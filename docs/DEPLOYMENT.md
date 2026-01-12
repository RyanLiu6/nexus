# Deployment Guide

This guide covers the complete deployment process for Nexus. For other documentation, see:

- **[Architecture](ARCHITECTURE.md)** - System design, tech stack, and how components work together
- **[Access Control](ACCESS_CONTROL.md)** - Authelia, Tailscale, SSH, and user groups
- **[README](../README.md)** - Project overview and quick reference

**New to Nexus?** Follow this guide from top to bottom for initial setup.

**Already deployed?** Jump to [Advanced Features](#advanced-features) for optional enhancements.

---

## Table of Contents

**Basic Setup:**
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Secrets Management](#secrets-management)
4. [Network Access (Cloudflare Tunnel)](#network-access-cloudflare-tunnel)
5. [Deploy Services](#deploy-services)

**Advanced Features:**
6. [Discord Alerting](#advanced-discord-alerting)
7. [Sure AI Integration](#advanced-sure-ai-integration)
8. [Tailscale SSH](#advanced-tailscale-ssh)
9. [Legacy: Port Forwarding](#legacy-port-forwarding)

**Operations:**
10. [Invoke Tasks](#invoke-tasks)
11. [Maintenance](#maintenance)
12. [Troubleshooting](#troubleshooting)

---

# Basic Setup

## Prerequisites

| Category | Requirement |
|----------|-------------|
| Hardware | 4+ cores, 16GB+ RAM, 500GB+ SSD |
| Software | Docker 24.0+, Python 3.12+, uv |
| DNS | Domain with Cloudflare |
| Accounts | Cloudflare account (free tier is fine) |

**No port forwarding required** - Nexus uses Cloudflare Tunnels by default.

## Quick Start

### 1. Install System Dependencies

**macOS:**
```bash
brew install --cask docker
brew install cloudflare/cloudflare/cloudflared
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
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
| `cloudflare_api_token` | Cloudflare API token | [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens) |
| `cloudflare_zone_id` | Cloudflare Zone ID | Domain Overview page on Cloudflare |
| `cloudflare_account_id` | Cloudflare Account ID | Account Settings or dashboard URL |
| `tunnel_secret` | Tunnel encryption secret | `openssl rand -hex 32` |
| `authelia_jwt_secret` | JWT signing key | `openssl rand -hex 32` |
| `authelia_session_secret` | Session encryption | `openssl rand -hex 32` |
| `authelia_storage_encryption_key` | Storage encryption | `openssl rand -hex 32` |
| `mysql_root_password` | Nextcloud database password | `openssl rand -base64 32` |
| `sure_postgres_password` | Sure database password | `openssl rand -base64 32` |
| `grafana_admin_password` | Grafana admin (API access only) | `openssl rand -base64 24` |

**API Token Permissions:**
- Zone:DNS:Edit
- Zone:Zone:Read
- Account:Cloudflare Tunnel:Edit

### Vault Commands

```bash
# View secrets (read-only)
ansible-vault view ansible/vars/vault.yml

# Edit secrets
ansible-vault edit ansible/vars/vault.yml

# Change vault password
ansible-vault rekey ansible/vars/vault.yml
```

---

## Network Access (Cloudflare Tunnel)

Nexus uses **Cloudflare Tunnels** by default - no port forwarding required. The tunnel is created and managed entirely by Terraform.

### Benefits

- ✅ **No port forwarding** - Works behind CGNAT, dynamic IPs
- ✅ **No public IP exposure** - Your home IP stays private
- ✅ **DDoS protection** - Cloudflare handles attacks
- ✅ **Zero config** - Terraform creates everything

### Setup

**1. Configure Cloudflare credentials in vault.yml:**

All Cloudflare credentials are stored in your encrypted vault:

```bash
# Edit vault (will prompt for vault password)
ansible-vault edit ansible/vars/vault.yml
```

Ensure these values are configured:

```yaml
cloudflare_api_token: "your-api-token"
cloudflare_zone_id: "your-zone-id"
cloudflare_account_id: "your-account-id"
tunnel_secret: "generate-with-openssl-rand-hex-32"
```

**Where to find these:**
- **API Token**: [Cloudflare Dashboard > Profile > API Tokens](https://dash.cloudflare.com/profile/api-tokens)
  - Permissions needed: Zone:DNS:Edit, Zone:Zone:Read, Account:Cloudflare Tunnel:Edit
- **Zone ID**: Domain Overview page in Cloudflare
- **Account ID**: URL bar when logged in (`dash.cloudflare.com/<account-id>/...`) or Account Settings
- **Tunnel Secret**: Generate with `openssl rand -hex 32`

**2. Initialize Terraform and create the tunnel:**

```bash
# Initialize Terraform
invoke tf-init

# Create tunnel and DNS records (reads credentials from vault.yml)
invoke tf-apply
```

You'll be prompted for your vault password. Terraform will:
- Create a Cloudflare Tunnel named `nexus-yourdomain.com`
- Create CNAME records pointing `@` and `*` to the tunnel
- Output the tunnel token

**3. Get the tunnel token:**

```bash
cd terraform && terraform output -raw tunnel_token
```

**4. Run cloudflared:**

```bash
# Test run (foreground)
cloudflared tunnel run --token <your-tunnel-token>

# Or run as a service (recommended for Linux)
sudo cloudflared service install <your-tunnel-token>
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

**macOS (run as launchd service):**
```bash
cloudflared service install <your-tunnel-token>
```

### Verification

After starting cloudflared:
- Check Cloudflare dashboard > Zero Trust > Tunnels - should show "Healthy"
- Visit `https://yourdomain.com` - should show Traefik (after deployment)

---

## Deploy Services

After completing the bootstrap and configuring your vault.yml:

```bash
# Run setup (creates proxy network)
invoke setup

# Deploy services using preset
invoke deploy --preset home

# Or deploy specific services
invoke deploy --services traefik,auth,dashboard
```

### How Deployment Works

1. **Terraform** manages Cloudflare Tunnel and DNS records
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
3. **Authelia checks permissions** against access control rules
   - ✅ **If authorized**: Authelia passes the request with user identity headers
   - ❌ **If denied**: User sees "Access Denied" and is redirected to Authelia portal
4. **Service receives request** with authenticated user info and grants access automatically

**Service-specific notes:**

- **Grafana**: Configured with auth proxy mode to trust Authelia headers. Admin credentials are only for API access.
- **Transmission**: Built-in auth is disabled. Access controlled entirely by Authelia.
- **Nextcloud**: Has its own user management (separate from Authelia SSO), but access is gated by Authelia.
- **FoundryVTT**: Has its own user/world management system (separate from Authelia SSO).

---

# Advanced Features

These features are optional and can be configured after basic deployment.

## Advanced: Discord Alerting

**Get notified about service outages, high resource usage, and other critical events.**

Discord notifications keep you informed when things go wrong.

### Quick Setup

1. **Create a Discord webhook** in your server:
   - Server Settings → Integrations → Webhooks → New Webhook
   - Copy the webhook URL

2. **Add to vault.yml:**
   ```bash
   ansible-vault edit ansible/vars/vault.yml
   ```

   ```yaml
   discord_webhook_url: "https://discord.com/api/webhooks/..."
   alert_provider: "discord"
   ```

3. **Set environment variable and run bot:**
   ```bash
   export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
   invoke alert-bot
   ```

### What You'll Get

- 🚨 Alerts when services go down
- ✅ Notifications when issues resolve
- ⚠️ Warnings for high CPU, memory, or disk usage
- 📊 Configurable alert rules

### Full Documentation

For advanced configuration (custom routing, systemd service, troubleshooting):

See the [Monitoring service README](../services/monitoring/README.md) for complete Discord alerting setup.

---

## Advanced: Sure AI Integration

**Enable automatic transaction categorization with local or cloud AI.**

Sure supports multiple AI options for categorizing your financial transactions automatically.

### Option 1: Local AI with Ollama (Recommended for Privacy)

Keep your financial data completely private:

```bash
# Install Ollama (macOS)
brew install ollama

# Pull base model and create custom financial model
ollama pull qwen2.5:7b
cd services/sure
ollama create ena -f Modelfile
```

Add to vault.yml:
```yaml
sure_openai_access_token: "ollama-local"
sure_openai_uri_base: "http://host.docker.internal:11434/v1"
sure_openai_model: "ena"
```

**Full Instructions:** [Sure Ollama Setup Guide](../services/sure/docs/ollama-setup.md)

### Option 2: Cloud AI Providers

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

**Full Instructions:** [Sure AI Integration Guide](../services/sure/docs/ai-integration.md)

### Cost Comparison

| Provider | Monthly Cost | Privacy |
|----------|--------------|---------|
| Ollama (local) | $0 | ✅ Complete |
| Deepseek | $2-5 | ❌ Cloud |
| Claude API | $10-25 | ❌ Cloud |
| OpenAI | $5-20 | ❌ Cloud |

After configuring, redeploy:
```bash
invoke deploy --preset home
```

---

## Advanced: Tailscale SSH

**Access your server via SSH through Tailscale without port forwarding.**

Tailscale SSH provides secure, zero-config SSH access with built-in authentication.

### Why Tailscale SSH?

- ✅ No SSH port exposed to the internet
- ✅ WireGuard encryption
- ✅ Built-in MFA via identity provider
- ✅ No SSH key management required

### Setup on Server

**macOS:**

Tailscale SSH requires enabling it in the Tailscale admin console for macOS:

1. Go to [Tailscale Admin Console](https://login.tailscale.com/admin/machines)
2. Click on your machine
3. Enable "SSH" in machine settings
4. Configure SSH ACLs in Access Controls

**Linux:**
```bash
sudo tailscale up --ssh
```

### Connect from Client

```bash
# Using Tailscale hostname
ssh username@server-name.tailnet-name.ts.net

# Or using Tailscale IP
ssh username@100.x.y.z
```

### macOS-Specific Notes

**Important:** On macOS, Tailscale SSH works differently than Linux:

1. **Admin Console Required**: Enable SSH per-machine in the Tailscale admin console
2. **ACLs Required**: Configure SSH access rules in [Access Controls](https://login.tailscale.com/admin/acls)

Example ACL configuration:
```json
{
  "ssh": [
    {
      "action": "accept",
      "src": ["autogroup:member"],
      "dst": ["autogroup:self"],
      "users": ["autogroup:nonroot"]
    }
  ]
}
```

3. **Check Mode (Recommended)**: For sensitive access, use check mode which requires re-authentication:
```json
{
  "ssh": [
    {
      "action": "check",
      "src": ["autogroup:member"],
      "dst": ["tag:prod"],
      "users": ["root"]
    }
  ]
}
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| "Permission denied (publickey)" | Enable SSH in Tailscale admin console for macOS. Check SSH ACLs. |
| Can't connect | Verify Tailscale is running: `tailscale status` |
| Wrong user | Ensure the user you're SSHing as matches ACL rules |

**Full Documentation:** [Tailscale SSH Documentation](https://tailscale.com/kb/1193/tailscale-ssh)

For complete access control configuration, see [ACCESS_CONTROL.md](ACCESS_CONTROL.md).

---

## Legacy: Port Forwarding

If you cannot use Cloudflare Tunnels (e.g., specific port requirements), you can use traditional port forwarding.

**Note:** This is not recommended as it exposes your home IP and requires router configuration.

### Setup

1. **Update Terraform variables** in `terraform/terraform.tfvars`:
   ```hcl
   use_tunnel = false
   public_ip  = "your.public.ip"
   subdomains = ["traefik", "grafana", "jellyfin"]
   ```

2. **Forward ports** in your router:
   - 80 → server:80
   - 443 → server:443

3. **Apply Terraform:**
   ```bash
   invoke tf-apply
   ```

This creates A records instead of CNAME records pointing to your public IP.

---

# Operations

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
invoke tf-init                   # Initialize Terraform
invoke tf-plan                   # Show Terraform plan
invoke tf-apply                  # Apply Terraform changes
invoke alert-bot                 # Start Discord alert bot
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
| Services won't start | `invoke logs --service <name>`, check service README |
| SSL issues | Delete `services/traefik/letsencrypt/*`, restart traefik |
| Authelia login loop | Check domain in config, verify Redis is running |
| Permission errors (macOS) | `sudo chown -R $USER:staff ~/Data` |
| Permission errors (Linux) | `sudo chown -R $USER:$USER /data` |
| Vault password wrong | Check password manager, or recreate vault |
| Terraform state lost | Re-import resources or start fresh |
| Tunnel not connecting | Check cloudflared logs, verify token |
| Discord alerts not working | See [Monitoring README](../services/monitoring/README.md) |
| Sure AI not working | Check API keys, see [Sure README](../services/sure/README.md) |

### Getting Logs

```bash
# Via invoke
invoke logs --service traefik
invoke logs --service auth --follow

# Via docker
docker compose logs traefik --tail 100
docker compose logs -f auth

# Cloudflared logs
journalctl -u cloudflared -f  # Linux
log show --predicate 'subsystem == "com.cloudflare.cloudflared"' --last 1h  # macOS
```

### Health Check

```bash
invoke health --domain yourdomain.com --verbose
```

### Service-Specific Help

Each service has its own README with detailed setup and troubleshooting:

| Service | Documentation |
|---------|---------------|
| Traefik | [services/traefik/README.md](../services/traefik/README.md) |
| Authelia | [services/auth/README.md](../services/auth/README.md) |
| Monitoring | [services/monitoring/README.md](../services/monitoring/README.md) |
| Sure | [services/sure/README.md](../services/sure/README.md) |
| Jellyfin | [services/jellyfin/README.md](../services/jellyfin/README.md) |
| Plex | [services/plex/README.md](../services/plex/README.md) |
| FoundryVTT | [services/foundryvtt/README.md](../services/foundryvtt/README.md) |
| Nextcloud | [services/nextcloud/README.md](../services/nextcloud/README.md) |
| Transmission | [services/transmission/README.md](../services/transmission/README.md) |
| Backups | [services/backups/README.md](../services/backups/README.md) |
| Dashboard | [services/dashboard/README.md](../services/dashboard/README.md) |

**Running into issues?** Check individual service READMEs (listed above) for troubleshooting, or [docs/runbooks/](runbooks/) for cross-service issues as they're documented.
