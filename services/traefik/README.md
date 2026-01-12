# Traefik <img src="https://upload.wikimedia.org/wikipedia/commons/1/1b/Traefik.logo.png" width="24">

[Traefik](https://doc.traefik.io/traefik/) is an open-source reverse proxy and load balancer that automatically discovers services and handles SSL certificates.

Docker Image is from Traefik, found [here](https://hub.docker.com/r/traefik/traefik).

## Setup

1. **Generate a dashboard password** (optional):
   ```bash
   ./generate_password.sh
   ```
   > **Note:** To skip this step, edit `docker-compose.yml` and remove the password line.

2. **Create an `.env` file:**
   ```ini
   DOMAIN=traefik.yourdomain.com
   TLD=com
   ACME_EMAIL=your.email@example.com
   TRAEFIK_USER=admin
   TRAEFIK_PASSWORD_HASH=<password from generate_password.sh>
   CLOUDFLARE_DNS_API_TOKEN=<your token>
   ```

3. **Configure DNS provider** in `docker-compose.yml`:
   ```yaml
   environment:
     - CLOUDFLARE_DNS_API_TOKEN=${CLOUDFLARE_DNS_API_TOKEN}
   ```

   Other DNS providers have different configuration. See [Traefik providers](https://doc.traefik.io/traefik/https/acme/#providers).

4. **Run it:**
   ```bash
   docker compose up -d
   ```

## Backups

N/A - Traefik configuration is version controlled. Let's Encrypt certificates are regenerated automatically.

---

## Troubleshooting

### SSL Certificate Issues

#### Symptoms
- Services returning 502/503 errors
- Certificate errors in logs
- Browser warnings about expired certificates

#### Solutions

1. **Check Traefik logs:**
   ```bash
   docker compose logs traefik --tail=100
   ```

2. **Verify DNS records:**
   ```bash
   nslookup yourdomain.com
   dig yourdomain.com
   ```

3. **Check ACME configuration:**
   - Verify email address is correct
   - Check Cloudflare API token is valid

4. **Clear certificates and restart:**
   ```bash
   rm -rf services/traefik/letsencrypt/*
   docker compose restart traefik
   ```

#### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `acme: error 429` | Rate limited by Let's Encrypt | Wait 1 hour before retrying |
| `acme: error 400` | Invalid DNS record | Fix DNS records at Cloudflare |
| `acme: unable to generate certificate` | DNS propagation delay | Wait 10-15 minutes and retry |

---

### Routing Problems

#### Symptoms
- Service shows 404 error
- Wrong service loads for URL
- Redirect loops

#### Solutions

1. **Check Traefik dashboard:**
   - Visit `https://traefik.yourdomain.com/dashboard`
   - Review routers and services configuration

2. **Verify service labels:**
   ```yaml
   labels:
     - "traefik.enable=true"
     - "traefik.http.routers.myapp.rule=Host(`app.yourdomain.com`)"
     - "traefik.http.routers.myapp.entrypoints=websecure"
     - "traefik.http.routers.myapp.tls=true"
     - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
   ```

3. **Check Docker network:**
   ```bash
   docker network inspect proxy
   ```
   Verify service is on the `proxy` network.

---

### Authelia Integration

#### Symptoms
- Bypassing Authelia when not expected
- Authelia login loop
- 401/403 errors

#### Solutions

1. **Check Authelia logs:**
   ```bash
   docker compose logs auth
   ```

2. **Verify middleware configuration** - services should have:
   ```yaml
   labels:
     - "traefik.http.routers.service.middlewares=authelia@docker"
   ```

3. **Test Authelia directly:**
   ```bash
   curl -k https://auth.yourdomain.com/api/verify
   ```

---

### Common Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 502 | Service not responding | Check service is running: `docker ps` |
| 503 | Service unhealthy | Check service logs: `docker compose logs <service>` |
| 504 | Gateway timeout | Increase timeout in Traefik config |
| 404 | Route not found | Check `Host()` rule in labels |
| 400 | Bad request | Review Traefik logs for details |

---

### Dashboard Access Issues

If you can't access the Traefik dashboard:

1. **Verify dashboard is enabled** in `traefik.yml`
2. **Check basic auth credentials** if configured
3. **Access via different methods:**
   - `https://traefik.yourdomain.com/dashboard/` (note trailing slash)
   - Direct: `http://localhost:8080` (if port exposed)
