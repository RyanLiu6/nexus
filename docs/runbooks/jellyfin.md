# Jellyfin Troubleshooting

## Common Issues

### Jellyfin Not Starting

**Symptoms**: Container exits immediately

**Solutions**:
1. Check logs: `docker logs jellyfin`
2. Verify `/Volumes/Data/Media` is mounted correctly
3. Check for port conflicts: `docker ps | grep 8096`

### Can't Stream Video

**Symptoms**: Videos won't play, loading errors

**Solutions**:
1. Check transcoding settings
2. Verify video codec support
3. Enable hardware acceleration if using GPU
4. Check bandwidth requirements

### High Memory Usage

**Symptoms**: Jellyfin consuming excessive RAM

**Solutions**:
1. Limit transcode quality
2. Reduce concurrent stream limit
3. Set memory limits in docker-compose.yml

## Useful Commands

```bash
# View Jellyfin logs
docker logs jellyfin -f

# Restart Jellyfin
docker restart jellyfin

# Access Jellyfin shell
docker exec -it jellyfin sh

# Check container stats
docker stats jellyfin
```

## Configuration Files

- `services/jellyfin/docker-compose.yml` - Container configuration
- `/Volumes/Data/Config/Jellyfin/` - Jellyfin config directory
- `/Volumes/Data/Media/` - Media files

## Performance Tuning

```yaml
# Add to docker-compose.yml if needed
services:
  jellyfin:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Hardware Acceleration

For Mac M4 with hardware acceleration, ensure Jellyfin can access GPU:

```yaml
devices:
  - /dev/dri:/dev/dri
```

## Maintenance

- Regular library scans
- Clean up old metadata
- Monitor storage usage
