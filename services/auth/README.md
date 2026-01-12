# Authentication (Authelia) <img src="https://www.authelia.com/images/branding/logo-cropped.png" width="24">

[Authelia](https://www.authelia.com/) is an open-source authentication and authorization server providing two-factor authentication and single sign-on (SSO).

## Setup

1. **Create `.env` from sample.**

2. **Copy the sample config files** to your `DATA_DIRECTORY/config/authelia/`:
   ```bash
   mkdir -p $DATA_DIRECTORY/config/authelia
   cp configuration.yml.sample $DATA_DIRECTORY/config/authelia/configuration.yml
   cp users_database.yml.sample $DATA_DIRECTORY/config/authelia/users_database.yml
   ```

3. **Generate a password hash** for your user:
   ```bash
   docker run authelia/authelia:latest authelia crypto hash generate argon2 --password 'yourpassword'
   ```
   Update `users_database.yml` with this hash.

4. **Edit `configuration.yml`** with your domain and settings.

5. **Run it:**
   ```bash
   docker compose up -d
   ```

## Configuration Files

| File | Purpose |
|------|---------|
| `configuration.yml` | Main Authelia configuration (domain, session, access rules) |
| `users_database.yml` | User accounts and password hashes |

## Adding Users

```bash
# Generate password hash
docker run authelia/authelia:latest authelia crypto hash generate argon2 --password 'newpassword'

# Add to users_database.yml
# Then restart Authelia
docker restart authelia
```

---

## Troubleshooting

### Login Loop

**Symptoms:** Continuously redirected to login page

**Solutions:**
1. Check `configuration.yml` domain settings match your actual domain
2. Verify Redis is running: `docker ps | grep redis`
3. Check session secret is set: `docker logs authelia | grep -i secret`
4. Clear browser cookies

### "User Not Found" Error

**Symptoms:** Login fails with "User not found"

**Solutions:**
1. Check `users_database.yml` YAML syntax
2. Verify password hash is correct format (should start with `$argon2id$`)
3. Restart Authelia: `docker restart authelia`

### 2FA Not Working

**Symptoms:** Can't receive 2FA codes

**Solutions:**
1. Check Authelia logs: `docker logs authelia`
2. Verify SMTP/email configuration in `configuration.yml`
3. Try TOTP instead of email
4. Check Redis container is running

### Tailscale Bypass Not Working

If Tailscale network bypass isn't working:

1. **Check `configuration.yml`** includes Tailscale network:
   ```yaml
   networks:
     - name: tailscale
       networks: [100.64.0.0/10]
   ```

2. **Verify source IP** in Traefik logs for `X-Forwarded-For`

3. **Docker Desktop on Mac?** May need to adjust network settings - Docker Desktop uses NAT

---

## Useful Commands

```bash
# View Authelia logs
docker logs authelia -f

# Restart Authelia
docker restart authelia

# Validate configuration (doesn't work in all versions)
docker run --rm authelia/authelia:latest authelia validate config

# Generate new password hash
docker run authelia/authelia:latest authelia crypto hash generate argon2 --password 'yourpassword'

# Test login API
curl -X POST https://auth.yourdomain.com/api/verify -d "username=admin&password=test"
```

---

## Access Control Issues

If users are seeing "Access Denied" unexpectedly:

1. **Check rule order** in `configuration.yml` - first match wins
2. **Verify user's groups** in `users_database.yml`
3. **Check logs** for which rule matched: `docker logs authelia | grep access`

Example access control configuration:

```yaml
access_control:
  default_policy: deny

  rules:
    # Tailscale bypass (put first)
    - domain: "*.yourdomain.com"
      networks: [tailscale]
      policy: bypass

    # Admin services require 2FA
    - domain: ["traefik.yourdomain.com", "grafana.yourdomain.com"]
      policy: two_factor
      subject: "group:admin"

    # Family access
    - domain: ["jellyfin.yourdomain.com"]
      policy: one_factor
      subject: "group:family"
```
