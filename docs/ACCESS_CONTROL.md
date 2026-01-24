# Access Control

## Overview

Nexus uses a **Tailscale-first security model** with role-based access control.

| Layer | Purpose | Configuration |
|-------|---------|---------------|
| **Tailscale ACLs** | Network access (who can reach server) | `tailscale/acl-policy.jsonc` |
| **tailscale-access** | Service access (who can use which service) | `tailscale/access-rules.yml` |
| **Header Auth** | Identity propagation (auto-login) | Traefik + Middleware |

## Access Levels

| Group | Services | SSH |
|-------|----------|-----|
| `admins` | Everything | Yes |
| `members` | FoundryVTT, Homepage | No |
| `finance` | Sure, Homepage | No |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Cloudflare Tunnel                             │
│              (Only FoundryVTT - public access)                   │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                     Tailscale Users                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Tailscale ACLs                                │
│           (Network-level: can user reach server?)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Traefik                                    │
│                    Middlewares:                                  │
│     1. tailscale-only (IP whitelist)                            │
│     2. tailscale-access (group-based access)                    │
│     3. security-headers                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│  Authorized (200 OK)    │     │  Unauthorized (403)     │
│  + Headers:             │     │  Nice error page        │
│  Remote-User: ryan@...  │     └─────────────────────────┘
│  Remote-Groups: admins  │
│         ↓               │
│      Service            │
└─────────────────────────┘
```

---

## Quick Setup

### 1. Configure Tailscale ACLs

Edit `tailscale/acl-policy.jsonc` with your users:

```jsonc
"groups": {
  "group:admins": ["your-email@gmail.com"],
  "group:members": ["friend1@gmail.com"],
  "group:finance": ["accountant@gmail.com"]
}
```

Upload to [Tailscale Admin Console → Access Controls](https://login.tailscale.com/admin/acls).

### 2. Tag Your Server

```bash
sudo tailscale up --advertise-tags=tag:nexus-server
```

### 3. Configure Split DNS

1. Go to [Tailscale DNS Settings](https://login.tailscale.com/admin/dns)
2. Add split DNS: `yourdomain.com` → Server's Tailscale IP

### 4. Deploy

```bash
invoke deploy --preset home
```

---

## Service Access Matrix

| Service | admins | members | finance | Public |
|---------|--------|---------|---------|--------|
| Traefik | ✅ | ❌ | ❌ | ❌ |
| Grafana | ✅ | ❌ | ❌ | ❌ |
| Prometheus | ✅ | ❌ | ❌ | ❌ |
| Alertmanager | ✅ | ❌ | ❌ | ❌ |
| Transmission | ✅ | ❌ | ❌ | ❌ |
| Jellyfin | ✅ | ❌ | ❌ | ❌ |
| Plex | ✅ | ❌ | ❌ | ❌ |
| Nextcloud | ✅ | ❌ | ❌ | ❌ |
| Sure | ✅ | ❌ | ✅ | ❌ |
| Homepage | ✅ | ✅ | ✅ | ❌ |
| FoundryVTT | ✅ | ✅ | ✅ | ✅ |

---

## Configuration Files

### `tailscale/acl-policy.jsonc`

Tailscale network-level access control. Defines:
- **Groups**: Who belongs to which role
- **Tag Owners**: Who can tag devices
- **ACLs**: Who can reach the server
- **SSH**: Who can SSH into the server

### `tailscale/access-rules.yml`

Per-service access control. Defines which groups can access which services.

```yaml
services:
  grafana:
    groups: [admins]
  sure:
    groups: [admins, finance]
  homepage:
    groups: [admins, members, finance]
```

---

## Authentication Strategies

Since we removed OAuth (tsidp), authentication falls into two categories:

### 1. Header Authentication (Proxy Auth)
For services that support it, `tailscale-access` passes the user's identity via HTTP headers (`Remote-User`, `Remote-Groups`). The service trusts these headers and logs the user in automatically.

*   **Grafana**: Fully configured. Admins get Admin role; others get Viewer role.

### 2. Manual Login (Gatekeeper Only)
For services that do **not** support header-based auth easily, `tailscale-access` acts as a "Gatekeeper".
*   **Step 1**: Tailscale checks if you are allowed to access the service. (e.g., only `admins` can see Jellyfin).
*   **Step 2**: If allowed, you reach the service's login page.
*   **Step 3**: You log in manually with an account created in that service.

| Service | Strategy | Notes |
|---------|----------|-------|
| Grafana | ✅ Header Auth | Auto-login & Role mapping |
| Jellyfin | 🔒 Gatekeeper | Manual login required |
| Nextcloud | 🔒 Gatekeeper | Manual login required |
| FoundryVTT | 🔒 Gatekeeper | Manual login required |
| Transmission | 🔒 Gatekeeper | No auth (protected by Gatekeeper) |

---

## SSH Access

SSH is only accessible via Tailscale (no port forwarding).

```bash
# Connect via Tailscale
ssh user@server.tailnet-name.ts.net

# Or via Tailscale IP
ssh user@100.x.y.z
```

Only `admins` group has SSH access (configured in ACL policy).

---

## Adding Users

### Add to Existing Group

1. Edit `tailscale/acl-policy.jsonc`:
   ```jsonc
   "group:members": ["friend1@gmail.com", "newuser@gmail.com"]
   ```
2. Upload to Tailscale admin console
3. Invite user to your tailnet
4. Update `ansible/vars/vault.yml` (tailscale_users) and redeploy.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't access any service | Check `tailscale status`, verify you're connected |
| DNS not resolving | Check split DNS in Tailscale admin |
| Legitimate site blocked | Check Cloudflare Gateway allowlist (see [DNS Filtering](DNS_FILTERING.md)) |
| 403 Forbidden | Check your group has access in `access-rules.yml` |
| SSH denied | Verify you're in `admins` group |

### Debug Commands

```bash
# Check Tailscale status
tailscale status

# Check your IP
tailscale ip

# Check if you can reach server
tailscale ping <server-hostname>

# View service logs
docker logs tailscale-access
```
