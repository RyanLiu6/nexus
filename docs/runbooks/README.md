# Nexus Runbooks

This directory contains operational procedures for Nexus homelab services.

## Quick Commands

### Docker Commands
```bash
# View all containers
docker ps

# View status of all services
docker compose ps

# View logs
docker compose logs <service-name>
docker compose logs -f <service-name>  # Follow logs

# Restart service
docker compose restart <service-name>

# Stop/start services
docker compose stop <service-name>
docker compose start <service-name>

# View resource usage
docker stats
```

### Health Checks
```bash
# Run health check
./scripts/health_check.py --domain yourdomain.com

# Run with alerts
./scripts/health_check.py --domain yourdomain.com --alert-webhook <webhook-url>
```

## Emergency Procedures

### Service Down
1. Check container status: `docker ps`
2. Check logs: `docker compose logs <service>`
3. Restart service: `docker compose restart <service>`
4. If failing, check dependencies (database, network)

### Authelia Issues
1. Verify Redis is running: `docker ps | grep redis`
2. Check logs: `docker compose logs auth`
3. Verify configuration: `services/auth/configuration.yml`
4. Test password hash generation

### SSL Certificate Issues
1. Check Traefik logs: `docker compose logs traefik`
2. Verify DNS records at Cloudflare
3. Check ACME email configuration
4. Clear certificates: `sudo rm -rf services/traefik/letsencrypt/*`

### Backup Failure
1. Check backup service logs: `docker compose logs borgmatic`
2. Verify backup destination (S3, rclone, etc.)
3. Check available disk space: `df -h`
4. Test manual backup: `./scripts/restore.py --list`

## Common Troubleshooting

### High Disk Usage
```bash
# Check disk usage
df -h

# Find large directories
du -sh /Volumes/Data/*

# Clean up Docker
docker system prune -a
docker volume prune
```

### Slow Performance
```bash
# Check container resources
docker stats

# Check CPU/Memory usage
top
htop
```

### Network Issues
```bash
# Check Docker network
docker network ls
docker network inspect proxy

# Test DNS resolution
nslookup yourdomain.com
dig yourdomain.com
```

## All Runbooks

### Core Services
- [Traefik](./traefik.md) - Reverse proxy and SSL issues
- [Authelia](./authelia.md) - Authentication and SSO
- [Dashboard](./dashboard.md) - Homepage dashboard issues
- [Monitoring](./monitoring.md) - Prometheus and Grafana
- [Backups](./backups.md) - Borgmatic backup issues

### Media Services
- [Plex](./plex.md) - Media streaming
- [Jellyfin](./jellyfin.md) - Media server
- [Transmission](./transmission.md) - Torrent client

### Application Services
- [Sure](./sure.md) - Finance and budgeting
- [FoundryVTT](./foundryvtt.md) - Virtual Tabletop
- [Nextcloud](./nextcloud.md) - File storage