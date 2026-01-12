# Homelab Architecture

## Overview

Nexus is a self-hosted homelab using Docker Compose with Traefik (reverse proxy), Authelia (SSO/2FA), and Cloudflare DNS.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Containers | Docker & Docker Compose |
| Proxy | Traefik (SSL termination, routing) |
| Auth | Authelia (SSO, 2FA) |
| DNS | Cloudflare |
| VPN | Tailscale (optional) |

## Services

| Service | Purpose | Access |
|---------|---------|--------|
| Traefik | Reverse proxy | Admin (2FA) |
| Authelia | Authentication | Admin (2FA) |
| Dashboard | Landing page | Admin (2FA) |
| Plex | Media streaming | Admin + Wife |
| Jellyfin | Media server | Admin |
| Transmission | Torrent client | Admin |
| Nextcloud | File storage | Admin |
| FoundryVTT | Virtual Tabletop | Admin + Gaming |
| Sure | Finance tracking | Admin + Wife |

## Traffic Flow

```
Internet → Cloudflare DNS (80/443) → Traefik (SSL) → Authelia → Service
```

## Authentication Levels

| Level | Policy | Use Case |
|-------|--------|----------|
| Admin | 2FA | All services |
| Gaming | 1FA | FoundryVTT only |
| Wife | 1FA | Plex + Sure |
| Tailscale | Bypass | Full access via VPN |

## Directory Structure

```
focus/
├── services/        # Service configs (auth, dashboard, plex, etc.)
├── scripts/         # Deployment and utility scripts
├── src/nexus/       # Python library
├── terraform/       # DNS management
└── ansible/         # Configuration management
```

## Data Storage

All persistent data at `$DATA_DIRECTORY`:
- `Config/*` - Application configs
- `Media/*` - Media files
- `sure/*` - Finance app data
- `Foundry/*` - Game data

## Limitations

- Single machine (no HA)
- Manual initial Authelia/Dashboard setup
- Docker Desktop NAT issues with Tailscale on Mac

## Related Docs

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Setup guide
- [ACCESS_CONTROL.md](./ACCESS_CONTROL.md) - Auth configuration
- [SECRETS.md](./SECRETS.md) - Secrets management
