# Deployment Guide

## Prerequisites

| Category | Requirement |
|----------|-------------|
| CPU | 4+ cores recommended |
| RAM | 16GB+ (8GB minimum) |
| Storage | 500GB+ SSD for OS/apps, separate HDD for media |
| Network | Gigabit ethernet, static local IP, ports 80/443 forwarded |
| Software | Docker 24.0+, Docker Compose 2.20+, Python 3.8+, uv |
| DNS | Domain with Cloudflare DNS |

## Quick Start

### 1. System Setup

**macOS:**
```bash
brew install --cask docker
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Ubuntu:**
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Data Directory

**macOS:**
```bash
sudo mkdir -p /Volumes/Data/{Config,Media,sure,Foundry}
sudo chown -R $USER:$USER /Volumes/Data
echo "export DATA_DIRECTORY=/Volumes/Data" >> ~/.zshrc && source ~/.zshrc
```

**Ubuntu:**
```bash
sudo mkdir -p /data/{Config,Media,sure,Foundry}
sudo chown -R $USER:$USER /data
echo "export DATA_DIRECTORY=/data" >> ~/.bashrc && source ~/.bashrc
```

### 3. Clone and Bootstrap

```bash
git clone <your-repo-url> ~/dev/focus && cd ~/dev/focus
./scripts/bootstrap
```

### 4. Configuration

Nexus uses a "Single Repo" strategy - code is public, configuration is private.

**Files to configure:**

| File | Purpose | Git Status |
|------|---------|------------|
| `.env` | Machine settings (domain, Cloudflare tokens) | Ignored |
| `ansible/vars/vault.yml` | Encrypted secrets | Committed |
| `terraform/terraform.tfstate` | DNS record state | Ignored (backup manually) |

```bash
cp .env.sample .env && nano .env
ansible-vault create ansible/vars/vault.yml
```

### 5. Deploy

```bash
./scripts/deploy.py -p home
./scripts/generate_dashboard.py -p home
docker network create proxy
docker compose up -d
```

### 6. Router Setup

1. Forward ports 80 and 443 to your server's local IP
2. Add Cloudflare DNS: A record `@` → your IP, CNAME `*` → `@`
3. Verify at `https://traefik.yourdomain.com/dashboard`

## Going Online Checklist

- [ ] Server has static local IP
- [ ] Ports 80/443 forwarded to server
- [ ] DNS records configured in Cloudflare
- [ ] Authelia users created with password hashes
- [ ] Dashboard URLs updated for your domain
- [ ] Services accessible via `https://service.yourdomain.com`

## Cloudflare Tunnel (Alternative)

Skip port forwarding by using Cloudflare Tunnel:

```bash
# Install: brew install cloudflare/cloudflare/cloudflared (macOS)
cloudflared tunnel login
cloudflared tunnel create nexus
cloudflared tunnel run nexus
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Services won't start | `docker compose logs -f <service>` |
| SSL issues | Delete `services/traefik/letsencrypt/*`, restart |
| Authelia login loop | Check domain in `configuration.yml`, verify Redis is running |
| Permission errors | `sudo chown -R $USER:$USER /Volumes/Data` |

## Maintenance

```bash
docker compose pull && docker compose up -d  # Update containers
docker image prune -a                         # Clean images
docker volume prune                           # Clean volumes
```

## Backup

```bash
# Config backup
tar -czf nexus-configs-$(date +%Y%m%d).tar.gz services/*/configuration.yml services/*/.env

# Database backup
docker compose exec sure-db pg_dump -U sure_user sure_production > sure-backup.sql
```
