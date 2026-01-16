# Deployment Guide

Complete setup guide for Nexus homelab. Follow steps 1-8 in order.

## Prerequisites

- Docker 24.0+, Python 3.12+, uv
- Domain with Cloudflare (free tier works)
- No port forwarding needed (uses Cloudflare Tunnels)
- **Tailscale Account** (free tier works)

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

---

## Step 2: Clone & Bootstrap

```bash
git clone <repo-url> ~/dev/nexus
cd ~/dev/nexus
./scripts/bootstrap
```

---

## Step 3: Activate Virtual Environment

**Option A: direnv (recommended)**
```bash
brew install direnv  # or: apt install direnv
echo "layout uv" > .envrc && direnv allow
```

**Option B: Manual**
```bash
source .venv/bin/activate
```

Verify: `invoke --list` should show available tasks.

---

## Step 4: Create Data Directories

The `bootstrap` script automatically creates `~/Data/{Config,Media,Backups}`.

If you want to use a different location, define `NEXUS_DATA_DIRECTORY` **before** running bootstrap or deployment:

```bash
export NEXUS_DATA_DIRECTORY="/path/to/custom/data"
```

Ensure this variable is persistent (add to `.zshrc` or `.envrc`).

---

## Step 5: Initial Setup

```bash
invoke setup
```

This creates the Docker network and copies vault.yml.sample to vault.yml.

---

## Step 6: Configure Secrets

Edit `ansible/vars/vault.yml` with your values:

```bash
nano ansible/vars/vault.yml
```

**Required:**
```yaml
nexus_root_directory: "/Users/yourname/dev/nexus"
nexus_data_directory: "/Users/yourname/Data"
nexus_domain: "yourdomain.com"
tz: "America/Vancouver"

# Cloudflare (from dashboard)
cloudflare_api_token: "your-api-token"
cloudflare_zone_id: "your-zone-id"
cloudflare_account_id: "your-account-id"
tunnel_secret: "run: openssl rand -hex 32"

# Tailscale
tailnet_name: "your-tailnet"
```

**Where to find Cloudflare values:**
- API Token: Cloudflare Dashboard → Profile → API Tokens (needs Zone:DNS:Edit, Account:Tunnel:Edit)
- Zone ID: Domain Overview page
- Account ID: URL bar or Account Settings

---

## Step 7: Configure Services

**This step is critical.**

1. **Tailscale Access Control:**
   *   Edit `tailscale/acl-policy.jsonc` with your user emails and groups.
   *   Edit `tailscale/access-rules.yml` with the **same** user emails.
   *   Upload `acl-policy.jsonc` content to [Tailscale Admin Console](https://login.tailscale.com/admin/acls).

2. **Tag Your Server:**
   ```bash
   sudo tailscale up --advertise-tags=tag:nexus-server
   ```

3. **Configure Split DNS:**
   - Go to [Tailscale DNS Settings](https://login.tailscale.com/admin/dns)
   - Add split DNS: `yourdomain.com` → Your server's Tailscale IP (100.x.x.x)

---

## Step 8: Deploy

```bash
invoke deploy
```

You'll be prompted for a vault password (save it somewhere secure).

**After deployment:**
- Dashboard: `https://hub.yourdomain.com` (Tailscale only)
- FoundryVTT: `https://foundry.yourdomain.com` (**Public** via Cloudflare Tunnel)
- All other services are accessible only via Tailscale.
- Authentication is handled automatically via Tailscale identity.

---

## Common Commands

```bash
invoke deploy              # Full deployment
invoke up                  # Start containers
invoke down                # Stop containers

ansible-vault edit ansible/vars/vault.yml  # Edit secrets
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| 404 on all services | Check traefik.yml and middlewares.yml exist |
| Access Denied (403) | Check `tailscale/access-rules.yml` group membership |
| DNS not resolving | Verify Split DNS setup in Tailscale Admin |

**View logs:**
```bash
docker logs traefik
docker logs tailscale-access
```

---

## Optional: Discord Alerts

1. Create webhook: Discord Server Settings → Integrations → Webhooks
2. Add to vault.yml:
   ```yaml
   discord_webhook_url: "https://discord.com/api/webhooks/..."
   ```
3. Run: `invoke alert-bot`

---

## Optional: Sure AI

**Local (Ollama):**
```bash
brew install ollama
ollama pull qwen2.5:7b
cd services/sure && ollama create ena -f Modelfile
```

Add to vault.yml:
```yaml
sure_openai_access_token: "ollama-local"
sure_openai_uri_base: "http://host.docker.internal:11434/v1"
sure_openai_model: "ena"
```

---

## More Documentation

- [Architecture](ARCHITECTURE.md) - System design
- [Access Control](ACCESS_CONTROL.md) - Tailscale & SSH
- Service READMEs in `services/*/README.md`
