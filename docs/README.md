# Nexus Documentation

Welcome to Nexus documentation! This folder contains guides for deploying, configuring, and operating your homelab.

## Documentation Structure

| Document | Purpose |
|----------|---------|
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Complete setup guide from scratch |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System design and tech stack |
| **[ACCESS_CONTROL.md](ACCESS_CONTROL.md)** | Authelia, Tailscale, SSH, user groups |
| **[runbooks/](runbooks/)** | Troubleshooting guides and known issues |

## Quick Links

### Getting Started

1. [Prerequisites](DEPLOYMENT.md#prerequisites) - What you need before starting
2. [Quick Start](DEPLOYMENT.md#quick-start) - Install dependencies and bootstrap
3. [Secrets Management](DEPLOYMENT.md#secrets-management) - Configure vault.yml
4. [Deploy Services](DEPLOYMENT.md#deploy-services) - Get everything running

### Advanced Features

- [Discord Alerting](DEPLOYMENT.md#advanced-discord-alerting) - Get notified of service issues
- [Sure AI Integration](DEPLOYMENT.md#advanced-sure-ai-integration) - Auto-categorize transactions
- [Tailscale SSH](DEPLOYMENT.md#advanced-tailscale-ssh) - Secure SSH without port forwarding

### Service Documentation

Each service has its own README with setup and troubleshooting:

| Service | Documentation |
|---------|---------------|
| Traefik | [services/traefik/README.md](../services/traefik/README.md) |
| Authelia | [services/auth/README.md](../services/auth/README.md) |
| Monitoring | [services/monitoring/README.md](../services/monitoring/README.md) |
| Sure | [services/sure/README.md](../services/sure/README.md) |
| Jellyfin | [services/jellyfin/README.md](../services/jellyfin/README.md) |
| Plex | [services/plex/README.md](../services/plex/README.md) |
| FoundryVTT | [services/foundryvtt/README.md](../services/foundryvtt/README.md) |
| Nextcloud | [services/nextcloud/README.md](../services/nextcloud/README.md) |
| Transmission | [services/transmission/README.md](../services/transmission/README.md) |
| Backups | [services/backups/README.md](../services/backups/README.md) |
| Dashboard | [services/dashboard/README.md](../services/dashboard/README.md) |

## Troubleshooting

**Having issues?** Check these resources:

1. **Service-specific problems** → Check the service's README (links above)
2. **Known issues & solutions** → [runbooks/](runbooks/) (as they are documented)

## Contributing

When adding new documentation:

1. **Service-specific setup/troubleshooting** → Add to `services/<name>/README.md`
2. **Cross-service issues or known bugs** → Add to `docs/runbooks/`
3. **Major feature or architecture changes** → Update relevant docs in `docs/`
