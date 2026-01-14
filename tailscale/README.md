# Tailscale Configuration

Configuration templates for Tailscale access control.

## Files

| File | Purpose | Where Used |
|------|---------|------------|
| `acl-policy.jsonc` | Network-level ACLs | Upload to Tailscale admin console |
| `access-rules.yml` | Per-service access rules | Used by `tailscale-access` middleware |

## Quick Setup

### 1. Edit Configuration Files

**acl-policy.jsonc** - Replace placeholder emails:
```jsonc
"groups": {
  "group:admins": ["your-email@gmail.com"],
  "group:members": ["friend1@gmail.com"],
  "group:finance": ["accountant@gmail.com"]
}
```

**access-rules.yml** - Same emails in groups section:
```yaml
groups:
  admins:
    - your-email@gmail.com
  members:
    - friend1@gmail.com
  finance:
    - accountant@gmail.com
```

### 2. Upload ACL Policy

1. Copy contents of `acl-policy.jsonc`
2. Go to [Tailscale Admin → Access Controls](https://login.tailscale.com/admin/acls)
3. Paste and save

### 3. Tag Your Server

```bash
sudo tailscale up --advertise-tags=tag:nexus-server
```

## Access Levels

| Group | Services | SSH |
|-------|----------|-----|
| `admins` | Everything | Yes |
| `members` | FoundryVTT, Homepage | No |
| `finance` | Sure, Homepage | No |

## How It Works

```
                    ┌──────────────────────┐
                    │   Tailscale ACLs     │
                    │  (acl-policy.jsonc)  │
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

1. Add email to appropriate group in **both** files:
   - `acl-policy.jsonc` (Tailscale ACL)
   - `access-rules.yml` (middleware config)

2. Upload updated ACL policy to Tailscale admin console

3. Invite user to your tailnet

## Adding a New Group

1. **acl-policy.jsonc**:
   ```jsonc
   "group:newgroup": ["user@gmail.com"]
   ```
   Add ACL rule:
   ```jsonc
   {
     "action": "accept",
     "src": ["group:newgroup"],
     "dst": ["tag:nexus-server:80", "tag:nexus-server:443"]
   }
   ```

2. **access-rules.yml**:
   ```yaml
   groups:
     newgroup:
       - user@gmail.com

   services:
     some-service:
       groups: [admins, newgroup]
   ```

3. Upload ACL policy and redeploy

## Important Notes

- **Keep groups in sync**: Group memberships must match in both files
- **Default deny**: Services not listed in `access-rules.yml` are denied
- **SSH is admin-only**: Only `admins` group can SSH (per ACL policy)
