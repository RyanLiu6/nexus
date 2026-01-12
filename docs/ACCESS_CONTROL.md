# Access Control

## Overview

Nexus uses a three-tier access model:

| Level | Method | Behavior |
|-------|--------|----------|
| **Public Internet** | Authelia SSO | Login required (1FA or 2FA) |
| **Tailscale VPN** | IP whitelist | Bypasses Authelia for admin |
| **User Groups** | Authelia rules | Scoped access by role |

## User Groups

| Group | Members | Services | Auth |
|-------|---------|----------|------|
| `admin` | You | All services | 2FA |
| `gaming` | D&D friends | FoundryVTT | 1FA |
| `wife` | Wife | Plex, Sure | 1FA |

---

## Tailscale Integration

[Tailscale](https://tailscale.com) provides secure VPN access without exposing ports to the public internet.

### Setup

**On the server:**
```bash
# macOS
brew install --cask tailscale

# Ubuntu
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

**On client devices:** Install Tailscale app and sign in with same account.

### How Bypass Works

Authelia trusts the Tailscale IP range (`100.64.0.0/10`):

- **Public access:** `https://plex.domain.com` → Authelia login → Service
- **Tailscale access:** `https://plex.domain.com` → Bypasses Authelia → Service

**Note:** Bypass means Authelia gets out of the way. Apps with their own login (Sure, Nextcloud) still show their login screen.

### Docker Desktop on macOS

Docker Desktop runs in a VM with NAT, so Traefik may see `192.168.65.1` instead of the Tailscale IP. If bypass doesn't work, just use normal Authelia login.

---

## SSH Access

### Option 1: Tailscale SSH (Recommended)

No SSH keys needed - Tailscale handles authentication.

**Enable on server:**
```bash
sudo tailscale up --ssh
```

**Connect from any Tailscale device:**
```bash
ssh username@server-name.tailnet-name.ts.net
# Or use Tailscale IP
ssh username@100.x.y.z
```

**Mobile:** Use Termius or built-in Tailscale app terminal.

### Option 2: Traditional SSH Keys

```bash
# Generate key
ssh-keygen -t ed25519 -C "your_email" -f ~/.ssh/nexus_key

# Copy to server
ssh-copy-id -i ~/.ssh/nexus_key.pub user@server

# Add to ~/.ssh/config
Host nexus
    HostName server-ip
    User username
    IdentityFile ~/.ssh/nexus_key
```

### Server Hardening (optional)

Edit `/etc/ssh/sshd_config`:
```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

---

## Authelia Configuration

### Users (`services/auth/users_database.yml`)

```yaml
users:
  admin:
    displayname: Ryan
    password: "{{ argon2_hash }}"
    groups: [admin, gaming, wife]

  friend:
    displayname: Friend
    password: "{{ argon2_hash }}"
    groups: [gaming]
```

### Access Rules (`services/auth/configuration.yml`)

```yaml
access_control:
  default_policy: deny
  networks:
    - name: tailscale
      networks: [100.64.0.0/10]
  rules:
    # Admin-only services (2FA required)
    - domain: ["traefik.{{ domain }}", "grafana.{{ domain }}"]
      policy: two_factor
      subject: "group:admin"

    # Gaming (1FA)
    - domain: ["foundry.{{ domain }}"]
      policy: one_factor
      subject: "group:gaming"

    # Wife (1FA)
    - domain: ["plex.{{ domain }}", "sure.{{ domain }}"]
      policy: one_factor
      subject: "group:wife"

    # Tailscale bypass for admin
    - domain: "*"
      policy: bypass
      networks: [tailscale]
```

### Traefik Middleware Labels

**Protected service (requires Authelia):**
```yaml
labels:
  - "traefik.http.routers.service.middlewares=authelia@docker"
```

**Public service (no auth):**
```yaml
labels:
  - "traefik.http.routers.service.middlewares=security-headers"
```

---

## Adding Users

```bash
# Generate password hash
docker run authelia/authelia:latest authelia crypto hash generate argon2 --password 'password'

# Add to users_database.yml, then restart
docker restart authelia
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Access denied | Check user groups in `users_database.yml` |
| VPN bypass not working | Verify IP in 100.64.0.0/10 range; check Docker NAT on macOS |
| Wrong user can access | Check access rules order in `configuration.yml` |
| Login loop | Verify Redis is running, check domain in config |
| SSH permission denied | Check `~/.ssh/authorized_keys` permissions (600) |
| Tailscale SSH not working | Run `tailscale status --json | grep ssh` |
