# Access Control

## Overview

Nexus uses a **tiered access control model** with Tailscale as the foundation:

| Tier | Layer | Method | Purpose |
|------|-------|--------|---------|
| **Tier 0** | Network Access | Tailscale VPN | Secure network connectivity (SSH, admin access) |
| **Tier 1** | Authentication | Authelia SSO | Single sign-on for all web services |
| **Tier 2** | Authorization | Authelia Rules + Groups | Per-service access control by user/group |

### Access Paths

**Via Tailscale (Trusted Network):**
- Access from Tailscale → Bypasses Authelia → Direct service access (SSO via headers)
- SSH access via Tailscale (no port forwarding needed)

**Via Public Internet:**
- Access via Cloudflare Tunnel → Authelia SSO login (1FA or 2FA) → Service access (if authorized)
- **No ports exposed on router** - all HTTP/HTTPS traffic through Cloudflare Tunnel

## User Groups

| Group | Members | Services | Auth |
|-------|---------|----------|------|
| `admin` | You | All services | 2FA |
| `gaming` | D&D friends | FoundryVTT | 1FA |
| `wife` | Wife | Plex, Sure | 1FA |

---

## Tier 0: Tailscale VPN (Network Access)

[Tailscale](https://tailscale.com) is the **foundation of Nexus security**. It provides:

- **Zero Trust Network**: Encrypted mesh VPN (WireGuard) between all your devices
- **No Port Forwarding**: No need to expose SSH or other ports on your router
- **Seamless SSH**: Built-in SSH with ACLs and key management
- **Trusted Network**: Authelia recognizes Tailscale IPs as trusted and bypasses login prompts

### Setup

**On the server:**
```bash
# macOS
brew install --cask tailscale

# Ubuntu
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh  # Enable Tailscale SSH
```

**On client devices:** Install Tailscale app and sign in with same account.

### How Authelia Bypass Works

Authelia trusts the Tailscale IP range (`100.64.0.0/10`) and uses **policy: bypass** for Tailscale traffic:

**From Public Internet:**
```
https://grafana.domain.com
  ↓
Cloudflare Tunnel
  ↓
Traefik → Authelia (requires 2FA login)
  ↓
Grafana (user logged in via SSO headers)
```

**From Tailscale:**
```
https://grafana.domain.com
  ↓
Traefik → Authelia (bypass - trusts Tailscale network)
  ↓
Grafana (user logged in via SSO headers from Authelia)
```

**Key Point:** Services are configured for SSO (single sign-on). Whether you're on Tailscale or public internet, **you never see application login screens** - authentication is handled by Authelia at the proxy layer.

**Exception:** Nextcloud and FoundryVTT have their own user management systems independent of Authelia.

### Docker Desktop on macOS

Docker Desktop runs in a VM with NAT, so Traefik may see `192.168.65.1` instead of the Tailscale IP. If bypass doesn't work:
- Access services via public domain (Authelia will prompt for login)
- Or configure Docker to use host networking (advanced)

---

## SSH Access via Tailscale

**SSH is only accessible via Tailscale** - no ports are exposed on your router.

### Setup Tailscale SSH

Tailscale SSH provides zero-config SSH access with built-in authentication and ACLs.

**Linux:**
```bash
sudo tailscale up --ssh
```

**macOS:**
Tailscale SSH on macOS works differently - you must enable it via the admin console:

1. Go to [Tailscale Admin Console](https://login.tailscale.com/admin/machines)
2. Click on your macOS machine
3. Enable "Tailscale SSH" in the machine settings
4. Configure SSH ACLs in [Access Controls](https://login.tailscale.com/admin/acls)

> **Note:** The `--ssh` flag does not work on macOS. You must use the admin console.

This enables SSH access for all devices on your tailnet without SSH keys.

### Connect from Tailscale Devices

**From desktop/laptop:**
```bash
# Using Tailscale hostname
ssh username@server-name.tailnet-name.ts.net

# Or using Tailscale IP (find with: tailscale status)
ssh username@100.x.y.z
```

**From mobile:**
- iOS/Android: Use Termius app or Tailscale's built-in terminal
- Connect using Tailscale hostname or IP

### Tailscale ACLs (Required for macOS)

Control SSH access with ACLs in the [Tailscale admin console](https://login.tailscale.com/admin/acls).

**Basic SSH access:**
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

**Stricter access with check mode (recommended for root):**
```json
{
  "ssh": [
    {
      "action": "accept",
      "src": ["autogroup:member"],
      "dst": ["autogroup:self"],
      "users": ["autogroup:nonroot"]
    },
    {
      "action": "check",
      "src": ["autogroup:member"],
      "dst": ["tag:prod"],
      "users": ["root"],
      "checkPeriod": "12h"
    }
  ]
}
```

**Check mode** requires re-authentication before SSH access, providing an extra layer of security for sensitive operations.

See [Tailscale SSH Documentation](https://tailscale.com/kb/1193/tailscale-ssh) for more details.

### Traditional SSH Keys (Fallback)

If you prefer traditional SSH keys:

```bash
# Generate key
ssh-keygen -t ed25519 -C "your_email" -f ~/.ssh/nexus_key

# Copy to server (via Tailscale)
ssh-copy-id -i ~/.ssh/nexus_key.pub username@100.x.y.z

# Add to ~/.ssh/config
Host nexus
    HostName 100.x.y.z  # Tailscale IP
    User username
    IdentityFile ~/.ssh/nexus_key
```

### Why No Port Forwarding?

**Security benefits:**
- ✅ SSH traffic encrypted by Tailscale (WireGuard)
- ✅ Only accessible to devices on your tailnet
- ✅ No SSH port exposed to public internet (no brute force attempts)
- ✅ Built-in MFA support via Tailscale identity provider
- ✅ Centralized access management in Tailscale admin console

**No need for port 2222 → 22 forwarding** - remove it from your router if configured.

---

## Tier 1: Authelia SSO (Authentication)

Authelia provides **single sign-on** for all web services. Users authenticate once, then access is granted via headers.

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

---

## Tier 2: Authorization (Per-Service Access Control)

Configure who can access which services in `services/auth/configuration.yml`.

### Access Rules (`services/auth/configuration.yml`)

**Rule order matters** - first match wins. Place specific rules before general ones.

```yaml
access_control:
  default_policy: deny  # Deny all by default
  networks:
    - name: tailscale
      networks: [100.64.0.0/10]

  rules:
    # 1. Tailscale bypass (most permissive - put first)
    - domain: "*.{{ domain }}"
      networks: [tailscale]
      policy: bypass

    # 2. Admin-only services (2FA required from public internet)
    - domain: ["traefik.{{ domain }}", "grafana.{{ domain }}", "prometheus.{{ domain }}"]
      policy: two_factor
      subject: "group:admin"

    # 3. Gaming group (1FA from public internet)
    - domain: ["foundry.{{ domain }}"]
      policy: one_factor
      subject: "group:gaming"

    # 4. Family group (1FA from public internet)
    - domain: ["plex.{{ domain }}", "jellyfin.{{ domain }}", "sure.{{ domain }}"]
      policy: one_factor
      subject: "group:family"

    # 5. Default deny (no match = access denied)
```

**Behavior:**
- **From Tailscale**: Rule 1 matches → `bypass` → user passes through with SSO headers
- **From Internet**: Rules 2-4 match → Authelia login required (1FA or 2FA) → SSO headers set
- **Unauthorized user**: No rule matches → `default_policy: deny` → Access Denied page

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
| **SSH not accessible** | Ensure Tailscale is running (`tailscale status`). Linux: `sudo tailscale up --ssh`. macOS: Enable in admin console. |
| **Tailscale SSH not working** | Check ACLs in Tailscale admin console. Verify user has SSH permissions. For macOS, ensure SSH is enabled per-machine in admin console. |
| **"Permission denied (publickey)"** | On macOS, Tailscale SSH must be enabled in admin console, not via CLI. Check SSH ACLs allow your user. |
| **Access denied to service** | Check user's groups in `users_database.yml`. Verify access rule exists in `configuration.yml`. |
| **Tailscale bypass not working** | Check client IP (`curl https://ifconfig.me`). Should be 100.64.x.x on Tailscale. Docker Desktop on macOS may show NAT IP. |
| **Wrong user can access service** | Check rule order in `configuration.yml` - first match wins. Tailscale bypass rule should be first. |
| **Service shows login screen** | Service not configured for SSO. Check for auth proxy settings (Grafana) or remove USER/PASS env vars (Transmission). |
| **Authelia login loop** | Verify Redis is running: `docker ps | grep redis`. Check domain matches in `configuration.yml`. |
| **Can't remove SSH port forwarding** | Safe to remove port 2222 → 22 from router once Tailscale SSH is working. Test first! |
| **Cloudflare Tunnel not working** | Check `cloudflared` logs: `journalctl -u cloudflared -f` (Linux) or tunnel status in Cloudflare dashboard. |

---

## Network Architecture Summary

### Port Forwarding: NONE Required

Nexus runs with **zero exposed ports** on your router:

- ✅ **HTTP/HTTPS**: Cloudflare Tunnel handles all web traffic
- ✅ **SSH**: Tailscale provides encrypted SSH access
- ❌ **No port 80/443 forwarding**: Cloudflare Tunnel connects outbound
- ❌ **No port 22 forwarding**: Tailscale handles SSH

### Security Layers

```
┌─────────────────────────────────────────────┐
│ Tier 0: Tailscale (Network Access)          │
│ - WireGuard VPN mesh network                 │
│ - SSH access (no port forwarding)            │
│ - Trusted network (bypasses Authelia)        │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ Tier 1: Authelia SSO (Authentication)       │
│ - Single sign-on for all services            │
│ - 1FA or 2FA based on rules                  │
│ - Sets user identity headers                 │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ Tier 2: Service Authorization                │
│ - Per-service access rules                   │
│ - Group-based permissions                    │
│ - Services trust Authelia headers (SSO)      │
└─────────────────────────────────────────────┘
```

### Access Decision Flow

**User attempts to access Grafana:**

1. **Check network**: Is user on Tailscale?
   - ✅ Yes → Policy: `bypass` → Set SSO headers → Grant access
   - ❌ No → Continue to step 2

2. **Check authentication**: Is user authenticated?
   - ❌ No → Redirect to Authelia login
   - ✅ Yes → Continue to step 3

3. **Check authorization**: Does user have access to Grafana?
   - ✅ Yes (user in `group:admin`) → Set SSO headers → Grant access
   - ❌ No → Show "Access Denied" page

4. **Service receives request**: Grafana sees `Remote-User: username` header → Logs user in automatically

### Migration Checklist

If migrating to this architecture:

- [ ] Enable Tailscale SSH: Linux: `sudo tailscale up --ssh` / macOS: Enable in admin console
- [ ] Configure SSH ACLs in Tailscale admin console
- [ ] Test SSH access via Tailscale from all devices
- [ ] Configure Cloudflare Tunnel for HTTP/HTTPS
- [ ] Remove transmission USER/PASS environment variables
- [ ] Configure Grafana with auth proxy mode
- [ ] **Remove SSH port forwarding from router** (port 2222 → 22)
- [ ] Test access from both Tailscale and public internet
- [ ] Verify SSO works (no service login screens)
