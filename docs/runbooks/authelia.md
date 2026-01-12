# Authelia Troubleshooting

## Common Issues

### Login Loop

**Symptoms**: Continuously redirected to login page

**Solutions**:
1. Check `services/auth/configuration.yml` domain settings
2. Verify Redis is running: `docker ps | grep redis`
3. Check session secret is set: `docker logs authelia | grep -i secret`
4. Clear browser cookies

### "User Not Found" Error

**Symptoms**: Login fails with "User not found"

**Solutions**:
1. Check `services/auth/users_database.yml` syntax
2. Verify password hash is correct format
3. Restart Authelia: `docker restart authelia`

### 2FA Not Working

**Symptoms**: Can't receive 2FA codes

**Solutions**:
1. Check Authelia logs: `docker logs authelia`
2. Verify SMTP/email configuration in `configuration.yml`
3. Try with alternative method (TOTP instead of email)
4. Check if Authelia Redis container is running

## Useful Commands

```bash
# View Authelia logs
docker logs authelia -f

# Restart Authelia
docker restart authelia

# Test Authelia configuration
docker run --rm authelia/authelia:latest authelia validate config

# Generate new password hash
docker run authelia/authelia:latest authelia crypto hash generate argon2 --password 'yourpassword'
```

## Configuration Files

- `services/auth/configuration.yml` - Main configuration
- `services/auth/users_database.yml` - User accounts
- `services/auth/.env` - Environment variables

## Testing

```bash
# Test login manually
curl -X POST https://auth.yourdomain.com/api/verify -d "username=admin&password=test"
```

## Access Control Issues

If Tailscale bypass isn't working:

1. Check `configuration.yml` networks block includes Tailscale range
2. Verify source IP: Check Traefik logs for `X-Forwarded-For`
3. Docker Desktop on Mac? May need to adjust network settings
