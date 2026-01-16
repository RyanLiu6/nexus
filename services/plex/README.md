# Plex <img src="https://www.plex.tv/wp-content/themes/plex/assets/img/plex-logo.svg" width="32">

[Plex](https://www.plex.tv/) is a media server for streaming your content anywhere.

Docker Image is from Linuxserver, found [here](https://hub.docker.com/r/linuxserver/plex).

## Setup

1. **Create an `.env` file:**
   ```ini
   DATA_DIRECTORY=/path/to/your/data
   ```

2. **Run:**
   ```bash
   docker compose up -d
   ```

3. **Configure media directories** in `docker-compose.yml`:
   ```yaml
   volumes:
     - ${DATA_DIRECTORY}/Media/anime:/anime
     - ${DATA_DIRECTORY}/Media/movies:/movies
   ```

4. **Claim your server** at `http://your-ip:32400/web` - sign in with Plex account.

## Backup

Config is stored at `$DATA_DIRECTORY/Config/plex`. Media files are your source of truth.

---

## Troubleshooting

### Plex Not Accessible

**Symptoms:** Can't access Plex web UI

**Solutions:**
1. Check Traefik labels in `docker-compose.yml`
2. Verify port 32400 is not blocked
3. Check container: `docker ps | grep plex`
4. View logs: `docker logs plex`

### Can't Find Media

**Symptoms:** Empty libraries, "No media found"

**Solutions:**
1. Verify volume mounts in docker-compose.yml
2. Check permissions: `ls -la $DATA_DIRECTORY/Media`
3. Ensure Plex user has access to media directories
4. Scan library manually in Plex settings

### High CPU Usage

**Symptoms:** Plex consuming excessive CPU

**Solutions:**
1. Disable software transcoding or use hardware acceleration
2. Set video quality limits for remote streams
3. Pre-transcode content with Tautulli/Optimized Versions
4. Check for background scanning tasks

---

## Hardware Acceleration

**Intel QuickSync (Linux):**
```yaml
devices:
  - /dev/dri:/dev/dri
```

**NVIDIA (Linux):**
Requires Plex Pass and NVIDIA runtime.

---

## Useful Commands

```bash
# View logs
docker logs plex -f

# Restart
docker restart plex

# Access shell
docker exec -it plex bash

# Check container status
docker inspect plex
```

---

## Maintenance

- Regularly update Plex: `docker compose pull plex && docker compose up -d plex`
- Optimize database periodically (Plex settings > Troubleshooting)
- Clean up unused metadata
