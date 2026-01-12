# Runbooks

Troubleshooting and configuration guides for Nexus services.

**Other Documentation:**
- **[Deployment Guide](../DEPLOYMENT.md)** - Initial setup and deployment process
- **[Architecture](../ARCHITECTURE.md)** - System design and tech stack
- **[Main README](../../README.md)** - Project overview

**Use runbooks for:**
- Troubleshooting service-specific issues
- Post-deployment configuration
- Service-specific operational tasks

## Quick Commands

```bash
# Check status
invoke ps                        # Running containers
invoke health --domain example.com

# View logs
invoke logs --service traefik
invoke logs --service auth --follow

# Restart
invoke restart --service auth

# Maintenance
invoke ops --daily               # Container checks, disk, logs
invoke ops --weekly              # Backup verification, cleanup
```

## Emergency: Service Down

1. **Check container**: `docker ps | grep <service>`
2. **View logs**: `invoke logs --service <name>`
3. **Restart**: `docker restart <container>`
4. **Check dependencies**: Is database/Redis running?
5. **Check network**: `docker network inspect proxy`

## Emergency: Complete Outage

1. **Check Docker**: `docker info`
2. **Check disk**: `df -h`
3. **Restart Docker**: Docker Desktop (macOS) or `sudo systemctl restart docker` (Linux)
4. **Bring up services**: `invoke up`

## Common Issues

### SSL Certificate Expired

```bash
docker compose logs traefik        # Check logs
rm -rf services/traefik/letsencrypt/*
docker restart traefik
```

### High Disk Usage

```bash
df -h                              # Check disk
docker system prune -a             # Clean Docker
docker volume prune                # Remove unused volumes
```

### Authentication Loop

1. Check Redis: `docker ps | grep redis`
2. Check Authelia logs: `invoke logs --service auth`
3. Verify domain in `services/auth/configuration.yml`

### Container Won't Start

```bash
invoke logs --service <name>       # Check error
docker inspect <container> --format='{{.State.ExitCode}}'
```

## Service Runbooks

### Core Services

| Service | Common Issues | Setup Notes |
|---------|--------------|-------------|
| [traefik](./traefik.md) | SSL, routing, 404s | Auto-configured, SSL certs automatic |
| [authelia](./authelia.md) | Login, 2FA, access denied | Configure users in configuration.yml |
| [monitoring](./monitoring.md) | Prometheus, Grafana, alerts | **→ Discord bot setup for alerts** |
| [backups](./backups.md) | Backup failures, restore | Verify schedule after deployment |
| [dashboard](./dashboard.md) | Layout, icons | Customize homepage |

### Media Services

| Service | Common Issues | Setup Notes |
|---------|--------------|-------------|
| [jellyfin](./jellyfin.md) | Transcoding, library | Web setup wizard, add libraries |
| [plex](./plex.md) | Media scanning, streaming | Claim server, configure libraries |
| [transmission](./transmission.md) | Downloads, VPN | Configure download directories |

### Application Services

| Service | Common Issues | Setup Notes |
|---------|--------------|-------------|
| [sure](./sure.md) | Database, AI, transactions | **→ Ollama/AI setup for categorization** |
| [nextcloud](./nextcloud.md) | File sync, database | Web setup wizard on first access |
| [foundryvtt](./foundryvtt.md) | Game data, modules | License key required, world setup |

**Key Post-Deployment Tasks:**
- **[Sure AI Setup](../../services/sure/docs/)** - Enable transaction categorization with Ollama or cloud AI
- **[Discord Alerts](./monitoring.md#discord-alerting-setup)** - Get notified of service outages

## Maintenance Schedule

| Frequency | Tasks |
|-----------|-------|
| Daily (auto) | Container health, disk monitoring |
| Weekly | `invoke ops --weekly` - backup check, cleanup |
| Monthly | `invoke pull && invoke up` - updates |
