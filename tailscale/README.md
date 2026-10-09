# Tailscale Configuration (via Headscale)

Tailscale is hosted locally via **Headscale** running as a core container dependency.
It replaces the commercial Tailnet and coordinates connections on your local machine.

## Files

| File | Purpose | Managed By |
|------|---------|------------|
| `access-rules.yml` | Per-service access rules | Ansible / CLI (from vault.yml) |
| `acl.hujson` | Network-level ACLs (Headscale policy) | Ansible / CLI (from vault.yml) |

## Setup

### 1. Configure Users in vault.yml

Edit `ansible/vars/vault.yml`:

```yaml
tailscale_users:
  admins:
    - your-email@gmail.com
  members:
    - friend1@gmail.com
```

### 2. Deploy

```bash
inv deploy
```

Ansible / CLI will automatically:
- Start Headscale container (`https://headscale.<domain>`)
- Generate `tailscale/acl.hujson` from `tailscale_users`
- Generate `tailscale/access-rules.yml` for `tailscale-access`

### 3. Connect Server to Headscale (one-time)

```bash
sudo tailscale up --login-server https://headscale.<your-domain> --advertise-tags=tag:nexus-server --ssh
```

> **`--ssh` is required.** SSH into the server is handled by **Tailscale SSH**
> (authenticated via the tailnet identity + the `ssh` block in the ACL policy),
> not by the host's `sshd`/`authorized_keys`. Without `--ssh`, the node's
> `RunSSH` pref is `false`, connections fall through to the host `sshd`, and you
> get `Permission denied (publickey)` even though the ACL allows you.
>
> `tailscale up` **resets any pref you don't pass on the command line**, so
> re-running it without `--ssh` silently disables Tailscale SSH. Always include
> `--ssh` when re-running `up`, or change a single pref non-destructively with
> `sudo tailscale set --ssh`. Verify with `tailscale debug prefs | grep RunSSH`
> (should be `true`).

## Access Levels

| Group | Network Access | SSH | Per-Service |
|-------|---------------|-----|-------------|
| `admins` | All ports | Yes | Configured in `access-rules.yml` |
| Other groups | Ports 80, 443 only | No | Configured in `access-rules.yml` |

## How It Works

```
                    ┌──────────────────────┐
                    │   Tailscale ACLs     │
                    │   (via OpenTofu)     │
                    │                      │
                    │  Network-level:      │
                    │  Can user reach      │
                    │  the server?         │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  tailscale-access    │
                    │  (access-rules.yml)  │
                    │                      │
                    │  Service-level:      │
                    │  Can user access     │
                    │  THIS service?       │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
             ┌─────────────┐       ┌─────────────┐
             │  200 OK     │       │  403 Page   │
             │  + headers  │       │  (denied)   │
             └─────────────┘       └─────────────┘
```

## Adding Users

1. Edit `ansible/vars/vault.yml`:
   ```yaml
   tailscale_users:
     members:
       - friend1@gmail.com
       - newuser@gmail.com  # Add new user
   ```
2. Run `inv deploy`
3. Invite user to your tailnet

## Adding a New Group

1. Add group to `vault.yml`:
   ```yaml
   tailscale_users:
     admins:
       - admin@gmail.com
     newgroup:
       - user@gmail.com
   ```

2. Add service access rules to `ansible/roles/nexus/templates/access-rules.yml.j2`:
   ```yaml
   services:
     some-service:
       groups: [admins, newgroup]
   ```

3. Run `inv deploy`

## Important Notes

- **Single source of truth**: Edit users only in `vault.yml`
- **Self-hosted**: Coordinated locally by Headscale without commercial account or OAuth keys
- **Default deny**: Services not listed in `access-rules.yml` are denied
- **SSH is admin-only**: Only `admins` group can SSH
