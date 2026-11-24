# Cloudflare DDNS Service

Automated Dynamic DNS (DDNS) updater using [`favonia/cloudflare-ddns`](https://github.com/favonia/cloudflare-ddns).

## Overview
Monitors the host's public WAN IPv4 address and automatically keeps Cloudflare DNS records synchronized whenever the ISP assigns a new IP address.

## Managed Subdomains
- `headscale.${NEXUS_DOMAIN}` (Direct / Grey cloud / `proxied = false` for WireGuard/STUN)
- `auth.${NEXUS_DOMAIN}` (Proxied / Orange cloud / `proxied = true`)
- `foundry.${NEXUS_DOMAIN}` (Proxied / Orange cloud / `proxied = true`)
- `headplane.${NEXUS_DOMAIN}` (Proxied / Orange cloud / `proxied = true`)

## Configuration
- `UPDATE_CRON`: `@every 5m` (checks every 5 minutes)
- `IP6_PROVIDER`: `none` (IPv4 only)
- `CLOUDFLARE_API_TOKEN`: Inherited from `CLOUDFLARE_DNS_API_TOKEN` in `.env`
