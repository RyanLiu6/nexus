# Deployment Guide

This guide covers the complete deployment process for Nexus. For other documentation, see:

- **[Architecture](ARCHITECTURE.md)** - System design, tech stack, and how components work together
- **[Access Control](ACCESS_CONTROL.md)** - Authelia, Tailscale, SSH, and user groups
- **[README](../README.md)** - Project overview and quick reference

**New to Nexus?** Follow the [Step-by-Step Setup](#step-by-step-setup) from Step 1 to Step 10.

**Already deployed?** Jump to [Advanced Features](#advanced-features) for optional enhancements.

---

## Table of Contents

**Step-by-Step Setup** (follow in order):
1. [Install Dependencies](#step-1-install-dependencies)
2. [Clone & Bootstrap](#step-2-clone--bootstrap)
3. [Activate Virtual Environment](#step-3-activate-virtual-environment)
4. [Create Data Directories](#step-4-create-data-directories)
5. [Initial Setup](#step-5-initial-setup)
6. [Configure Secrets](#step-6-configure-secrets)
7. [Deploy](#step-7-deploy)

**Advanced Features** (optional, after basic setup):
- [Discord Alerting](#advanced-discord-alerting)
- [Sure AI Integration](#advanced-sure-ai-integration)
- [Tailscale SSH](#advanced-tailscale-ssh)
- [Legacy: Port Forwarding](#legacy-port-forwarding)

**Operations:**
- [Invoke Tasks](#invoke-tasks)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

---

# Step-by-Step Setup

Follow these steps in order. Each step depends on the previous ones.

## Prerequisites

| Category | Requirement |
|----------|-------------|
| Hardware | 4+ cores, 16GB+ RAM, 500GB+ SSD |
| Software | Docker 24.0+, Python 3.12+, uv |
| DNS | Domain with Cloudflare |
| Accounts | Cloudflare account (free tier is fine) |

**No port forwarding required** - Nexus uses Cloudflare Tunnels by default.

---

## Step 1: Install Dependencies

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

**Verify installations:**
```bash
docker --version
cloudflared --version
uv --version
```

---

## Step 2: Clone & Bootstrap

```bash
git clone <repo-url> ~/dev/nexus
cd ~/dev/nexus
./scripts/bootstrap
```

The bootstrap script installs: Python 3.12+, Ansible, Terraform, pre-commit hooks, and Python dependencies.

---

## Step 3: Activate Virtual Environment

The virtual environment must be activated to use `invoke` commands.

### Option A: Using direnv (Recommended)

[direnv](https://direnv.net/) automatically activates the venv when you `cd` into the project.

**Setup direnv with uv layout:**

1. Install direnv (see [RyanLiu6/setup](https://github.com/RyanLiu6/setup) for a complete shell setup with direnv + uv integration)

2. Create `.envrc` in the project root:
   ```bash
   echo "layout uv" > .envrc
   direnv allow
   ```

Now the venv activates automatically when you enter the directory.

### Option B: Manual Activation

Activate in every new terminal session:

```bash
cd ~/dev/nexus
source .venv/bin/activate
```

**Verify it's working:**
```bash
invoke --list
```

You should see a list of available tasks. If you get "command not found", the venv isn't activated.

---

## Step 4: Create Data Directories

**macOS:**
```bash
mkdir -p ~/Data/{Config,Media}
```

**Ubuntu:**
```bash
sudo mkdir -p /data/{Config,Media}
sudo chown -R $USER:$USER /data
```

---

## Step 5: Initial Setup

This creates the Docker network, copies the vault sample, and sets up the Ansible inventory:

```bash
invoke setup
```

You should see:
```
✅ Created 'proxy' network
✅ Created vault.yml from sample. Edit it with your secrets.
✅ Created hosts.yml from example.
```

---

## Step 6: Configure Secrets

Open `ansible/vars/vault.yml` and fill in your values:

```bash
nano ansible/vars/vault.yml
# or: code ansible/vars/vault.yml
```

### Required Values

**Paths and domain (all deployments):**
```yaml
nexus_root_directory: "/Users/yourname/dev/nexus"  # Where you cloned nexus
nexus_backup_directory: "/Users/yourname/Data/Backups"
data_directory: "/Users/yourname/Data"
nexus_domain: "yourdomain.com"
tz: "America/Vancouver"  # Your timezone
```

**Cloudflare credentials (for tunnel):**
```yaml
cloudflare_api_token: "<api_token_here>"
cloudflare_zone_id: "your-zone-id"
cloudflare_account_id: "your-account-id"
tunnel_secret: "generate-with-command-below"
```

Generate secrets:
```bash
# For tunnel_secret:
openssl rand -hex 32

# For authelia secrets (need 3 different values):
openssl rand -hex 32
openssl rand -hex 32
openssl rand -hex 32
```

**Where to find Cloudflare values:**
- **API Token**: [Cloudflare Dashboard > Profile > API Tokens](https://dash.cloudflare.com/profile/api-tokens)
  - Create token with permissions: Zone:DNS:Edit, Zone:Zone:Read, Account:Cloudflare Tunnel:Edit
- **Zone ID**: Your domain's Overview page in Cloudflare dashboard
- **Account ID**: In URL bar `dash.cloudflare.com/<account-id>/...` or Account Settings

**Authelia secrets (required for SSO):**
```yaml
authelia_jwt_secret: "<generated_hex_here>"
authelia_session_secret: "<generated_hex_here>"
authelia_storage_encryption_key: "<generated_hex_here>"
```

**Service-specific secrets:** Configure only for services you'll use. See `vault.yml.sample` for the full list.

---

## Step 7: Deploy

The `invoke deploy` command handles everything:
- ✅ Encrypts vault.yml (if not already encrypted)
- ✅ Creates Docker proxy network
- ✅ Runs Terraform to create Cloudflare Tunnel and DNS
- ✅ Starts cloudflared to connect the tunnel
- ✅ Deploys all services with Ansible

```bash
invoke deploy
```

You'll be prompted to:
1. **Confirm prerequisites** - acknowledge you've run bootstrap and configured vault
2. **Create vault password** - if vault isn't encrypted (SAVE THIS PASSWORD!)
3. **Enter vault password** - for Terraform to read Cloudflare credentials

The deployment takes a few minutes. When complete, you'll see:

```
============================================================
  ✅ Deployment Complete!
============================================================

Access your services:
  Dashboard: https://hub.yourdomain.com
  Auth:      https://auth.yourdomain.com
```

### Deploy Options

```bash
# Deploy with a specific preset
invoke deploy --preset core    # Just core services
invoke deploy --preset home    # Full home setup (default)

# Skip certain steps
invoke deploy --skip-dns           # Skip Terraform (if tunnel exists)
invoke deploy --skip-cloudflared   # Don't start cloudflared
invoke deploy --skip-ansible       # Only do DNS, no containers

# Preview without changes
invoke deploy --dry-run

# Non-interactive (for scripts)
invoke deploy --yes
```

### Vault Commands (for later)

```bash
# View secrets (read-only)
ansible-vault view ansible/vars/vault.yml

# Edit secrets
ansible-vault edit ansible/vars/vault.yml

# Change vault password
ansible-vault rekey ansible/vars/vault.yml
```

### Using a Vault Password File (Optional)

To avoid being prompted for the vault password on every deploy, create a `.vault_pass` file:

```bash
# Create the password file (replace with your actual vault password)
echo "your-vault-password" > .vault_pass

# Secure the file permissions
chmod 600 .vault_pass
```

The `ansible.cfg` is already configured to use this file. Once created:
- `invoke deploy` won't prompt for the vault password
- `ansible-vault view/edit` commands work without `--vault-password-file`

**Security notes:**
- `.vault_pass` is in `.gitignore` and will never be committed
- Use `chmod 600` to ensure only you can read it
- Store your vault password in a password manager as backup

---

## 🎉 Setup Complete!

Your Nexus homelab is now running. Access your services at:
- **Dashboard**: `https://hub.yourdomain.com`
- **Auth Portal**: `https://auth.yourdomain.com`

Continue to [Advanced Features](#advanced-features) for optional enhancements.

---

# How It Works

## Deployment Architecture

1. **Terraform** manages Cloudflare Tunnel and DNS records
2. **Ansible** generates the root `docker-compose.yml` by:
   - Reading the inventory file (`ansible/inventory/hosts.yml`) to determine deployment targets
   - Reading the service preset
   - Combining individual `services/<name>/docker-compose.yml` files
   - Injecting secrets from `vault.yml`
   - Running `docker compose up -d`

The generated `docker-compose.yml` is not committed (it contains secrets).

**Inventory file:** `ansible/inventory/hosts.yml` defines where services are deployed. By default, it's set to `localhost` for local deployments. To deploy to remote servers, add them under `[remote_servers]` in this file.

## Authentication Architecture (SSO-First)

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
sure_openai_access_token: "<openai_api_key_here>"
sure_openai_model: "gpt-4"

# Or use OpenRouter for multiple providers
sure_openai_access_token: "<openrouter_api_key_here>"
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
