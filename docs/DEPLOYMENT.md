# Deployment Guide

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
- `discord_webhook_url` - For Discord alerts (leave empty to disable)
- `sure_openai_access_token` - For Sure AI features

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

| Problem | Solution |
|---------|----------|
| Services won't start | `invoke logs --service <name>` |
| SSL issues | Delete `services/traefik/letsencrypt/*`, restart traefik |
| Authelia login loop | Check domain in config, verify Redis is running |
| Permission errors (macOS) | `sudo chown -R $USER:staff /Volumes/Data` |
| Permission errors (Linux) | `sudo chown -R $USER:$USER /data` |
| Vault password wrong | Check password manager, or recreate vault |
| Terraform state lost | Re-import resources or start fresh |

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
