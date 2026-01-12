# Traefik Runbook

## SSL Certificate Issues

### ACME/Let's Encrypt Problems

#### Symptoms
- Services returning 502/503 errors
- Traefik showing certificate errors in logs
- Browser warnings about expired certificates

#### Troubleshooting Steps

1. **Check Traefik logs**
   ```bash
   docker compose logs traefik --tail=100
   ```

2. **Verify DNS records**
   ```bash
   nslookup yourdomain.com
   dig yourdomain.com
   ```

3. **Check ACME configuration**
   - Review `services/traefik/config/acme.yml`
   - Verify email address is correct
   - Check Cloudflare API token is valid

4. **Clear certificates and restart**
   ```bash
   sudo rm -rf services/traefik/letsencrypt/*
   docker compose restart traefik
   ```

5. **Verify port forwarding**
   - Router: Port 80 and 443 forwarded to server
   - Firewall: Ports 80 and 443 allowed

#### Common Errors

| Error | Cause | Solution |
|--------|--------|----------|
| `acme: error 429` | Rate limited by Let's Encrypt | Wait 1 hour before retrying |
| `acme: error 400` | Invalid DNS record | Fix DNS records at Cloudflare |
| `acme: unable to generate certificate` | DNS propagation delay | Wait 10-15 minutes and retry |

## Routing Problems

### Services Not Accessible

#### Symptoms
- Service shows 404 error
- Wrong service loads for URL
- Redirect loops

#### Troubleshooting Steps

1. **Check Traefik dashboard**
   - Visit `https://traefik.yourdomain.com/dashboard`
   - Review routers and services configuration
   - Verify labels are correct

2. **Verify service labels**
   - Check `services/<service>/docker-compose.yml`
   - Look for `traefik.http.routers.*` labels
   - Ensure `Host(` rule matches your domain)

3. **Test local connectivity**
   ```bash
   docker compose ps
   curl http://<service>:<port>
   ```

4. **Check Docker network**
   ```bash
   docker network inspect proxy
   ```
   - Verify service is on the `proxy` network

5. **Review Traefik configuration**
   ```bash
   docker compose logs traefik | grep router
   ```

#### Label Examples

Correct format for service labels:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`app.yourdomain.com`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls=true"
  - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
```

## Middleware Issues

### Authelia Integration

#### Symptoms
- Bypassing Authelia when not expected
- Authelia login loop
- 401/403 errors

#### Troubleshooting Steps

1. **Check Authelia logs**
   ```bash
   docker compose logs auth
   ```

2. **Verify middleware configuration**
   - Check Traefik labels include auth middleware
   - Ensure `forwardAuth` points to Authelia

3. **Test Authelia directly**
   ```bash
   curl -k https://auth.yourdomain.com/api/verify
   ```

4. **Check user database**
   - Verify `services/auth/users_database.yml` exists
   - Test login at `https://auth.yourdomain.com`

#### Common Auth Issues

| Error | Cause | Solution |
|--------|--------|----------|
| 401 Unauthorized | Invalid credentials | Check password hash in users_database.yml |
| Login loop | Session cookie issue | Clear browser cookies, check session secret |
| Auth not working | Missing middleware label | Add `traefik.http.routers.*.middlewares=auth` |

### Security Headers

#### Verify Headers
```bash
curl -I https://app.yourdomain.com
```

Expected headers:
- `Strict-Transport-Security`
- `X-Frame-Options`
- `X-Content-Type-Options`
- `X-XSS-Protection`
- `Referrer-Policy`

#### Missing Headers
Check `services/traefik/config/middleware.yml` for header configuration.

## Dashboard Access Issues

### Symptoms
- Cannot access Traefik dashboard
- Dashboard shows wrong information
- Dashboard prompts for authentication unexpectedly

#### Troubleshooting Steps

1. **Verify dashboard service**
   ```bash
   docker ps | grep traefik
   ```

2. **Check dashboard configuration**
   - Review `services/traefik/config/dashboard.yml`
   - Verify basic auth credentials

3. **Access via different methods**
   - `https://traefik.yourdomain.com/dashboard`
   - Direct: `http://localhost:8080` (if port exposed)

## Common Error Codes

| Code | Meaning | Action |
|------|----------|--------|
| 502 | Service not responding | Check service is running: `docker ps` |
| 503 | Service unhealthy | Check service logs: `docker compose logs <service>` |
| 504 | Gateway timeout | Increase timeout in Traefik config |
| 404 | Route not found | Check Host(` rule in labels |
| 400 | Bad request | Review Traefik logs for details |
