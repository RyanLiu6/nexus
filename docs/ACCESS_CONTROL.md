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

### 1. Configure Users in vault.yml

Edit `ansible/vars/vault.yml` (the **single source of truth**):

```yaml
tailscale_users:
  admins:
    - your-email@gmail.com
  members:
    - friend1@gmail.com
  finance:
    - accountant@gmail.com
```

### 2. Add Tailscale API Key

**Required** for ACL and DNS management:

1. Go to [Tailscale Admin → Settings → Keys](https://login.tailscale.com/admin/settings/keys)
2. Click **"Generate API key..."** (max 90 days, rotate periodically)
3. Add to vault.yml: `tailscale_api_key: "tskey-api-..."`

### 3. Deploy

```bash
invoke deploy --preset home
```

### 4. Tag Your Server (one-time)

```bash
sudo tailscale up --advertise-tags=tag:nexus-server
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

## Configuration

All access control is configured in `ansible/vars/vault.yml` and applied automatically.

### Tailscale ACL (via Terraform)

Network-level access control applied directly to your tailnet:
- **Groups**: Who belongs to which role
- **ACLs**: Who can reach the server (admins: all ports, others: 80/443)
- **SSH**: Who can SSH into the server (admins only)
- **DNS**: Cloudflare Gateway nameservers

### `tailscale/access-rules.yml` (via Ansible)

Per-service access control. To modify which groups can access which services, edit `ansible/roles/nexus/templates/access-rules.yml.j2`:

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

1. Edit `ansible/vars/vault.yml`:
   ```yaml
   tailscale_users:
     members:
       - friend1@gmail.com
       - newuser@gmail.com  # Add new user
   ```
2. Run `inv deploy` (Terraform updates ACL automatically)
3. Invite user to your tailnet

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
