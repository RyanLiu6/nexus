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
```

### 2. Add Tailscale OAuth Credentials

**Required** for ACL and DNS management:

1. Go to [Tailscale Admin → Settings → Trust credentials](https://login.tailscale.com/admin/settings/trust-credentials)
2. Click **"Add a credential..."**, choose **Custom scopes**
3. Enable: **DNS** (Read + Write), **Policy File** (Read + Write)
4. Add to vault.yml: `tailscale_oauth_client_id` and `tailscale_oauth_client_secret`

### 3. Deploy

```bash
invoke deploy --preset home
```

### 4. Tag Your Server & Enable Tailscale SSH (one-time)

```bash
sudo tailscale up --advertise-tags=tag:nexus-server --ssh
```

> `--ssh` is required — SSH is authenticated by **Tailscale SSH** (tailnet
> identity + the ACL `ssh` block), not the host `sshd`. See
> [SSH Access](#ssh-access) for details and troubleshooting.

---

## Service Access Matrix

| Service | admins | members | Public |
|---------|--------|---------|--------|
| Traefik | ✅ | ❌ | ❌ |
| Grafana | ✅ | ❌ | ❌ |
| Prometheus | ✅ | ❌ | ❌ |
| Alertmanager | ✅ | ❌ | ❌ |
| Transmission | ✅ | ❌ | ❌ |
| Jellyfin | ✅ | ❌ | ❌ |
| Plex | ✅ | ❌ | ❌ |
| Sure | ✅ | ❌ | ❌ |
| Paperless | ✅ | ❌ | ❌ |
| Grimmory | ✅ | ❌ | ❌ |
| Homepage | ✅ | ✅ | ❌ |
| FoundryVTT | ✅ | ✅ | ✅ |

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
    groups: [admins]
  homepage:
    groups: [admins, members]
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

### How SSH auth actually works

Authentication is handled by **Tailscale SSH**, not the host's `sshd`:

- `tailscaled` intercepts port 22 on the Tailscale (`100.x`) interface and
  authenticates you against your tailnet identity plus the `ssh` block in the
  ACL policy (`terraform/tailscale.tf` → `local.ssh_rules`).
- This requires the server to run with Tailscale SSH enabled (`RunSSH: true`),
  set via `--ssh` on `tailscale up` (or `tailscale set --ssh`).
- The host `~/.ssh/authorized_keys` and its SSH keys are **not** used for
  Tailscale connections. They only matter for direct (non-Tailscale) SSH.

### Troubleshooting: `Permission denied (publickey)` over Tailscale

This almost always means **Tailscale SSH got disabled** and the connection fell
through to the host `sshd`, which then rejects the key.

Root cause: `tailscale up` resets any pref not passed on the command line.
Re-running the tag command **without** `--ssh` (e.g. after a reinstall,
restart, or `up` re-run) silently flips `RunSSH` back to `false`.

Diagnose and fix on the server (needs an existing session — direct/local SSH,
or physical access):

```bash
# 1. Confirm the cause — should print "true"; if "false", that's the bug
tailscale debug prefs | grep RunSSH

# 2. Re-enable Tailscale SSH without disturbing other prefs
sudo tailscale set --ssh

# 3. Confirm the node is still tagged and the ACL allows you
tailscale status --json | grep -A2 '"Tags"'   # expect tag:nexus-server
```

Because the ACL rule uses `action = "accept"` (not `"check"`), reconnecting
works immediately — no re-auth prompt.

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
| SSH `Permission denied (publickey)` over Tailscale | Tailscale SSH is off — `tailscale debug prefs \| grep RunSSH`, fix with `sudo tailscale set --ssh` (see [SSH Access](#ssh-access)) |

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
