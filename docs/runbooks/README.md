# Runbooks

Troubleshooting guides for Nexus services.

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

| Service | Common Issues |
|---------|--------------|
| [traefik](./traefik.md) | SSL, routing, 404s |
| [authelia](./authelia.md) | Login, 2FA, access denied |
| [dashboard](./dashboard.md) | Layout, icons |
| [monitoring](./monitoring.md) | Prometheus, Grafana, alerts |
| [backups](./backups.md) | Backup failures, restore |
| [jellyfin](./jellyfin.md) | Transcoding, library |
| [plex](./plex.md) | Media scanning, streaming |
| [transmission](./transmission.md) | Downloads, VPN |
| [foundryvtt](./foundryvtt.md) | Game data, modules |
| [sure](./sure.md) | Database, sync |

## Maintenance Schedule

| Frequency | Tasks |
|-----------|-------|
| Daily (auto) | Container health, disk monitoring |
| Weekly | `invoke ops --weekly` - backup check, cleanup |
| Monthly | `invoke pull && invoke up` - updates |
