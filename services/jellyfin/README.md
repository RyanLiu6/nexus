# Jellyfin <img src="https://github.com/jellyfin/jellyfin-ux/blob/master/branding/SVG/icon-solid-black.svg?raw=true" width="24">

[Jellyfin](https://jellyfin.org/) is a free, open-source media server.

Docker Image is from Linuxserver, found [here](https://hub.docker.com/r/linuxserver/jellyfin).

## Setup

1. **Create an `.env` file:**
   ```ini
   JELLYFIN_DOMAIN=jellyfin.yourdomain.com
   DATA_DIRECTORY=/path/to/your/data
   ```

2. **Configure media directories** in `docker-compose.yml`:
   ```yaml
   volumes:
     - ${DATA_DIRECTORY}/Config/jellyfin:/config
     - ${DATA_DIRECTORY}/Media/movies:/data/movies
     - ${DATA_DIRECTORY}/Media/tv:/data/tv
   ```

3. **Run:**
   ```bash
   docker compose up -d
   ```

4. Access the web UI to complete setup.

## Backups

Config can be backed up:
```bash
# Manual backup
tar -czf jellyfin-config.tar.gz $DATA_DIRECTORY/Config/jellyfin

# Cron backup (weekly)
0 0 * * 1 tar -cf $DATA_DIRECTORY/Backups/jellyfin/$(date +%F).tar $DATA_DIRECTORY/Config/jellyfin
```

---

## Troubleshooting

### Jellyfin Not Starting

**Symptoms:** Container exits immediately

**Solutions:**
1. Check logs: `docker logs jellyfin`
2. Verify media directories are mounted correctly
3. Check for port conflicts: `docker ps | grep 8096`
4. Verify permissions on config directory

### Can't Stream Video

**Symptoms:** Videos won't play, loading errors

**Solutions:**
1. Check transcoding settings in Jellyfin admin
2. Verify video codec support
3. Enable hardware acceleration if using GPU
4. Check bandwidth/network settings

### High Memory Usage

**Symptoms:** Jellyfin consuming excessive RAM

**Solutions:**
1. Limit transcode quality in settings
2. Reduce concurrent stream limit
3. Set memory limits in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 4G
   ```

---

## Hardware Acceleration

For better transcoding performance:

**Intel QuickSync (Linux):**
```yaml
devices:
  - /dev/dri:/dev/dri
```

**NVIDIA (Linux):**
```yaml
runtime: nvidia
environment:
  - NVIDIA_VISIBLE_DEVICES=all
```

**Apple Silicon (macOS):**
Hardware transcoding is not currently supported in Docker on Apple Silicon.

---

## Useful Commands

```bash
# View logs
docker logs jellyfin -f

# Restart
docker restart jellyfin

# Access shell
docker exec -it jellyfin sh

# Check stats
docker stats jellyfin
```
