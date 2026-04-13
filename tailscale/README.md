# Tailscale Configuration

Tailscale ACL and DNS are managed automatically via Terraform.

## Files

| File | Purpose | Managed By |
|------|---------|------------|
| `access-rules.yml` | Per-service access rules | Ansible (from vault.yml) |
| ACL Policy | Network-level ACLs | Terraform (from vault.yml) |
| DNS Nameservers | Cloudflare Gateway | Terraform |

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

### 2. Add Tailscale OAuth Credentials

**Required** for ACL and DNS management:

1. Go to [Tailscale Admin → Settings → Trust credentials](https://login.tailscale.com/admin/settings/trust-credentials)
2. Click **"Add a credential..."**, choose **Custom scopes**
3. Enable: **DNS** (Read + Write), **Policy File** (Read + Write)
4. Add to vault.yml:

```yaml
tailscale_oauth_client_id: "<client_id>"
tailscale_oauth_client_secret: "<client_secret>"
```

### 3. Deploy

```bash
inv deploy
```

Terraform will automatically:
- Apply ACL policy (groups, access rules, SSH)
- Configure DNS nameservers (Cloudflare Gateway)
- Enable MagicDNS

### 4. Tag Your Server (one-time)

```bash
sudo tailscale up --advertise-tags=tag:nexus-server
```

## Access Levels

| Group | Network Access | SSH | Per-Service |
|-------|---------------|-----|-------------|
| `admins` | All ports | Yes | Configured in `access-rules.yml` |
| Other groups | Ports 80, 443 only | No | Configured in `access-rules.yml` |

## How It Works

```
                    ┌──────────────────────┐
                    │   Tailscale ACLs     │
                    │   (via Terraform)    │
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
- **OAuth credentials**: Do not expire (unlike API keys) — no rotation needed
- **Default deny**: Services not listed in `access-rules.yml` are denied
- **SSH is admin-only**: Only `admins` group can SSH
