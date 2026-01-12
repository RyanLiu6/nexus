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

| Secret | Description | How to Generate |
|--------|-------------|-----------------|
| `nexus_domain` | Your domain (e.g., example.com) | - |
| `cloudflare_api_token` | Cloudflare API token | Cloudflare dashboard |
| `cloudflare_zone_id` | Cloudflare Zone ID | Cloudflare dashboard |
| `authelia_jwt_secret` | JWT signing key | `openssl rand -hex 32` |
| `authelia_session_secret` | Session encryption | `openssl rand -hex 32` |
| `authelia_storage_encryption_key` | Storage encryption | `openssl rand -hex 32` |
| `postgres_password` | Database password | `openssl rand -hex 16` |
| `discord_webhook_url` | For alerts | Discord server settings |

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

### Password File (Optional)

For automation, store password in a file:

```bash
echo "your-vault-password" > ~/.vault_pass
chmod 600 ~/.vault_pass

# Use in playbooks
ansible-playbook playbook.yml --vault-password-file ~/.vault_pass
```

**Never commit vault password to git.**

---

## Deploy Services

```bash
# Create Docker network
docker network create proxy

# Deploy using invoke
invoke deploy --preset home

# Or deploy specific services
invoke deploy --services traefik,auth,dashboard
```

### How Deployment Works

1. **Terraform** updates Cloudflare DNS records for each service
2. **Ansible** generates the root `docker-compose.yml` by:
   - Reading the service preset
   - Combining individual `services/<name>/docker-compose.yml` files
   - Injecting secrets from `vault.yml`
   - Running `docker compose up -d`

The generated `docker-compose.yml` is not committed (it contains secrets).

---

## Router Setup

1. Forward ports 80 and 443 to your server's local IP
2. Add Cloudflare DNS records:
   - A record: `@` → your public IP
   - CNAME: `*` → `@`
3. Enable Cloudflare proxy (orange cloud) for DDoS protection

Verify at `https://traefik.yourdomain.com/dashboard`

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

## Cloudflare Tunnel (Alternative to Port Forwarding)

Skip port forwarding by using Cloudflare Tunnel:

```bash
# Install
brew install cloudflare/cloudflare/cloudflared  # macOS
# Or download from GitHub releases for Linux

# Setup
cloudflared tunnel login
cloudflared tunnel create nexus
cloudflared tunnel run nexus
```

This routes traffic through Cloudflare without exposing ports.
