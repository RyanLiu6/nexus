# Traefik <img src="https://upload.wikimedia.org/wikipedia/commons/1/1b/Traefik.logo.png" width="24">

[Traefik](https://doc.traefik.io/traefik/) is an open-source reverse proxy and load balancer that automatically discovers services and handles SSL certificates.

Docker Image is from Traefik, found [here](https://hub.docker.com/r/traefik/traefik).

## Setup

1. **Environment variables** (provided by Ansible from vault.yml):
   - `NEXUS_DOMAIN` - Your domain (e.g., example.com)
   - `ACME_EMAIL` - Email for Let's Encrypt certificates
   - `CLOUDFLARE_DNS_API_TOKEN` - Cloudflare API token for DNS challenge

2. **Deploy via Ansible:**
   ```bash
   cd ansible && ansible-playbook playbook.yml -e "services=traefik"
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

### Tailscale Access Integration

#### Symptoms
- Bypassing Auth when not expected
- 403 Forbidden errors (Access Denied)

#### Solutions

1. **Check tailscale-access logs:**
   ```bash
   docker logs tailscale-access
   ```

2. **Verify middleware configuration** - services should have:
   ```yaml
   labels:
     - "traefik.http.routers.service.middlewares=tailscale-access@docker"
   ```

3. **Check Access Rules:**
   - Review `tailscale/access-rules.yml`
   - Ensure your Tailscale user is in the correct group

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
