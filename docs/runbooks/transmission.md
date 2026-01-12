# Transmission Troubleshooting

## Common Issues

### Can't Download

**Symptoms**: Torrents stuck at 0%

**Solutions**:
1. Check port forwarding (9091, 51413)
2. Verify download directory exists: `ls -la /Volumes/Data/Downloads`
3. Check disk space: `df -h /Volumes/Data`
4. Verify torrent tracker status

### Slow Download Speeds

**Symptoms**: Downloads slower than expected

**Solutions**:
1. Check ISP throttling
2. Adjust port forwarding settings
3. Increase peer connections
4. Check torrent seeders/leechers ratio

### Transmission Web UI Not Accessible

**Symptoms**: Can't access transmission web interface

**Solutions**:
1. Check Traefik labels in docker-compose.yml
2. Verify container is running: `docker ps | grep transmission`
3. Check port 9091
4. Verify Authelia middleware isn't blocking (if used)

## Useful Commands

```bash
# View Transmission logs
docker logs transmission -f

# Restart Transmission
docker restart transmission

# Check active torrents
docker exec transmission transmission-remote -l

# Add torrent via CLI
docker exec transmission transmission-remote -a "magnet:?xt=..."

# Remove all torrents
docker exec transmission transmission-remote -t all -r
```

## Configuration Files

- `services/transmission/docker-compose.yml` - Container configuration
- `/Volumes/Data/Config/Transmission/` - Transmission config
- `/Volumes/Data/Downloads/` - Download directory

## Security

Transmission should always be behind Authelia:

```yaml
labels:
  - "traefik.http.routers.transmission.middlewares=authelia@docker"
```

## Port Forwarding

Ensure these ports are forwarded:
- **9091**: Web UI
- **51413**: BitTorrent
- **51413/udp**: BitTorrent UDP

## Maintenance

- Regularly clean up completed torrents
- Monitor disk space
- Review download directories
