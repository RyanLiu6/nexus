# Nexus Documentation

## Quick Start

1. **[Deployment Guide](DEPLOYMENT.md)** - Follow steps 1-8 to deploy

## Reference

- **[Architecture](ARCHITECTURE.md)** - System design and tech stack
- **[Access Control](ACCESS_CONTROL.md)** - Tailscale, SSH
- **[DNS Filtering](DNS_FILTERING.md)** - Ad-blocking and malware protection via Cloudflare Gateway

## Service Documentation

Each service has its own README in `services/<name>/README.md`:

| Service | Purpose |
|---------|---------|
| traefik | Reverse proxy |
| tailscale-access | Auth middleware |
| dashboard | Homepage |
| monitoring | Prometheus + Grafana |
| sure | Finance tracking |
| jellyfin | Media server |
| foundryvtt | Virtual tabletop (public) |

## Troubleshooting

Check service READMEs in `services/<name>/README.md` for troubleshooting guides.
