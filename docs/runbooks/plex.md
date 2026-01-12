# Plex Troubleshooting

## Common Issues

### Plex Not Accessible

**Symptoms**: Can't access Plex at `https://plex.yourdomain.com`

**Solutions**:
1. Check Traefik labels in `services/plex/docker-compose.yml`
2. Verify port 32400 is not blocked
3. Check Plex container is running: `docker ps | grep plex`

### Plex Can't Find Media

**Symptoms**: Empty libraries, "No media found"

**Solutions**:
1. Verify volume mounts in docker-compose.yml
2. Check permissions: `ls -la /Volumes/Data/Media`
3. Ensure `/Volumes/Data` is accessible to the Plex user

### High CPU Usage

**Symptoms**: Plex consuming > 100% CPU

**Solutions**:
1. Disable hardware transcoding if not using GPU
2. Set video quality limits
3. Pre-transcode content
4. Check for background scanning/scraping

## Useful Commands

```bash
# View Plex logs
docker logs plex -f

# Restart Plex
docker restart plex

# Check Plex container status
docker inspect plex

# Access Plex CLI (if available)
docker exec -it plex bash
```

## Configuration Files

- `services/plex/docker-compose.yml` - Container configuration
- `/Volumes/Data/Config/Plex/Library/Application Support/Plex Media Server/` - Plex config
- `services/plex/.env` - Environment variables

## Maintenance

- Regularly update Plex: `docker compose pull plex && docker compose up -d plex`
- Optimize database periodically
- Clean up unused metadata
