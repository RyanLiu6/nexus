# Traefik <img src="https://upload.wikimedia.org/wikipedia/commons/1/1b/Traefik.logo.png" width="24">

[Traefik](https://doc.traefik.io/traefik/) is an open-source reverse proxy and load balancer that automatically discovers services, handles SSL certificates via Let's Encrypt DNS challenges, and terminates HTTPS traffic.

Docker Image is from Traefik, found [here](https://hub.docker.com/r/traefik/traefik).

## Architecture

- **Entrypoints:**
  - `http` (:80) — Permanently redirects (301) all traffic to `https` (:443)
  - `https` (:443) — TLS termination with Let's Encrypt certificates
  - `traefik` (:8080) — Internal dashboard and Prometheus metrics endpoint
- **Providers:**
  - **Docker Provider:** Automatically discovers containers attached to the `nexus` network with `traefik.enable=true` labels
  - **File Provider:** Loads dynamic router/service definitions from `/rules` (`services/traefik/rules/`), including middlewares, TLS configuration, and external VMs like Home Assistant (`services/traefik/rules/homeassistant.yml`)
- **Certificates:** Automated wildcard/subdomain DNS-01 challenges via Cloudflare (`certchallenge` resolver)
- **Authentication & Security:** Standard requests route through `tailscale-chain@file` (combines IP allowlists, `tailscale-access` ForwardAuth middleware, and security headers)

## Setup

1. **Environment variables** (provided by Ansible from `vault.yml`):
   - `NEXUS_DOMAIN` — Your base domain (e.g., `example.com`)
   - `ACME_EMAIL` — Email for Let's Encrypt certificates
   - `CLOUDFLARE_DNS_API_TOKEN` — Cloudflare API token for DNS challenges

2. **Deploy via Invoke:**
   ```bash
   inv deploy --services traefik
   ```

## Backups

N/A — Traefik configuration is version controlled. Let's Encrypt certificates are stored in `/letsencrypt/acme.json` and regenerated automatically.

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
   docker logs traefik --tail=100
   ```

2. **Verify DNS records:**
   ```bash
   dig @1.1.1.1 sub.yourdomain.com
   ```

3. **Check ACME configuration:**
   - Verify email address is correct
   - Check Cloudflare API token is valid with Zone:DNS edit permissions

4. **Clear certificates and restart:**
   ```bash
   rm -rf services/traefik/letsencrypt/acme.json
   docker restart traefik
   ```

---

### Routing Problems

#### Symptoms
- Service shows 404 error
- Wrong service loads for URL
- Redirect loops

#### Solutions

1. **Check Traefik dashboard:**
   - Visit `https://traefik.<domain>/dashboard/`
   - Review routers, middlewares, and services configuration

2. **Verify service labels (Docker containers):**
   ```yaml
   labels:
     - "traefik.enable=true"
     - "traefik.docker.network=nexus"
     - "traefik.http.routers.myapp.rule=Host(`myapp.${NEXUS_DOMAIN}`)"
     - "traefik.http.routers.myapp.entrypoints=https"
     - "traefik.http.routers.myapp.middlewares=tailscale-chain@file"
     - "traefik.http.routers.myapp.tls=true"
     - "traefik.http.routers.myapp.tls.certresolver=certchallenge"
     - "traefik.http.services.myapp.loadbalancer.server.port=8080"
   ```

3. **Verify File Provider rules (for non-Docker VMs/services):**
   - Check files in `services/traefik/rules/*.yml`
   - Use dynamic Go template syntax `rule: "Host(`app.{{ env `NEXUS_DOMAIN` }}`)"` to prevent committing domains to Git

4. **Check Docker network:**
   ```bash
   docker network inspect nexus
   ```
   Verify service container is connected to the `nexus` network.

---

### Tailscale Access Integration

#### Symptoms
- 403 Forbidden errors (Access Denied)
- ForwardAuth loop

#### Solutions

1. **Check tailscale-access logs:**
   ```bash
   docker logs tailscale-access
   ```

2. **Verify middleware configuration:**
   - Services should reference `tailscale-chain@file`

3. **Check Access Rules:**
   - Review `tailscale/access-rules.yml`
   - Ensure your service is listed under `services:` with appropriate `groups` (e.g. `admins`, `members`)
