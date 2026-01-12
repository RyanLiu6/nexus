# Access Control

## Overview

Three-tier access model:
1. **Public Internet** - Requires Authelia SSO
2. **Tailscale VPN** - Bypasses Authelia
3. **User Groups** - Scoped access by role

## User Groups

| Group | Members | Services | Auth |
|-------|---------|----------|------|
| `admin` | You | All | 2FA |
| `gaming` | Gaming friends | FoundryVTT | 1FA |
| `wife` | Wife | Plex + Sure | 1FA |

## Traefik Labels

**Private (requires Authelia):**
```yaml
labels:
  - "traefik.http.routers.service-name.middlewares=authelia@docker,security-headers"
```

**Public (no auth):**
```yaml
labels:
  - "traefik.http.routers.service-name.middlewares=security-headers"
```

## Authelia Configuration

**Users (`services/auth/users_database.yml`):**
```yaml
users:
  admin:
    displayname: Ryan
    password: "{{ admin_password_hash }}"
    groups: [admin, gaming, wife]
```

**Access Rules (`services/auth/configuration.yml`):**
```yaml
access_control:
  default_policy: deny
  networks:
    - name: tailscale
      networks: [100.64.0.0/10]
  rules:
    - domain: ["traefik.{{ NEXUS_DOMAIN }}"]
      policy: two_factor
      subject: "group:admin"
    - domain: ["foundry.{{ NEXUS_DOMAIN }}"]
      policy: one_factor
      subject: "group:gaming"
    - domain: ["plex.{{ NEXUS_DOMAIN }}", "sure.{{ NEXUS_DOMAIN }}"]
      policy: one_factor
      subject: "group:wife"
    - domain: "*"
      policy: bypass
      networks: [tailscale]
```

## Tailscale ACLs

```json
{
  "acls": [
    {"action": "accept", "src": ["group:admin"], "dst": ["*:*"]},
    {"action": "accept", "src": ["group:gaming"], "dst": ["foundry.*:30000"]},
    {"action": "accept", "src": ["group:wife"], "dst": ["plex.*:32400", "sure.*:3000"]}
  ],
  "groups": {
    "group:admin": ["user:you@example.com"],
    "group:gaming": ["user:friend@example.com"],
    "group:wife": ["user:wife@example.com"]
  }
}
```

## Adding Users

```bash
# Generate password hash
docker run authelia/authelia:latest authelia crypto hash generate argon2 --password 'password'

# Add to users_database.yml, restart Authelia
docker restart authelia
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Access denied | Check user groups in `users_database.yml` |
| VPN bypass not working | Verify IP in 100.64.0.0/10 range |
| Wrong user can access | Check access rules order in `configuration.yml` |

## Security Checklist

- [ ] All services require Authelia (no unprotected routes)
- [ ] User groups configured
- [ ] Tailscale ACLs match Authelia groups
- [ ] Passwords hashed with argon2
- [ ] Secrets encrypted with ansible-vault
