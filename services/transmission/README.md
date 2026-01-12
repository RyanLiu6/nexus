# Transmission <img src="https://upload.wikimedia.org/wikipedia/commons/6/6d/Transmission_icon.png" width="24">

[Transmission](https://transmissionbt.com/) is a highly customizable and free BitTorrent client.

Docker Image is from Linuxserver, found [here](https://hub.docker.com/r/linuxserver/transmission).

## Setup

1. **Create an `.env` file:**
   ```ini
   TRANSMISSION_USERNAME=<your_username>
   TRANSMISSION_PASSWORD=<your_password>
   TRANSMISSION_DOMAIN=transmission.yourdomain.com
   DATA_DIRECTORY=/path/to/data
   ```

2. **Open port 51413** for peer connections:

   **ufw (Linux):**
   ```bash
   sudo ufw allow 51413
   ```

   **pf (macOS):** Add to `/etc/pf.conf`:
   ```
   pass in proto tcp from any to any port 51413
   ```
   Then: `sudo pfctl -f /etc/pf.conf && sudo pfctl -e`

3. **Create config directory:**
   ```bash
   mkdir -p $DATA_DIRECTORY/Config/transmission
   cp settings.json $DATA_DIRECTORY/Config/transmission/
   ```

4. **Configure download directories** in `docker-compose.yml`:
   ```yaml
   volumes:
     - ${DATA_DIRECTORY}/Media:/downloads
     - ${DATA_DIRECTORY}/Media/queue:/watch
   ```

5. **Run:**
   ```bash
   docker compose up -d
   ```

## Backups

```bash
# Weekly backup
0 0 * * 4 tar -cf $DATA_DIRECTORY/Backups/transmission/$(date +%F).tar $DATA_DIRECTORY/Config/transmission
```

---

## Troubleshooting

### Can't Download

**Symptoms:** Torrents stuck at 0%

**Solutions:**
1. Check port forwarding (51413)
2. Verify download directory exists
3. Check disk space: `df -h`
4. Check torrent tracker status

### Slow Downloads

**Solutions:**
1. Check ISP throttling
2. Verify port 51413 is open
3. Increase peer connections in settings
4. Check torrent seeders/leechers ratio

### Web UI Not Accessible

1. Check Traefik labels
2. Verify container: `docker ps | grep transmission`
3. Check port 9091
4. Check Authelia middleware

---

## Useful Commands

```bash
# View logs
docker logs transmission -f

# Restart
docker restart transmission

# List active torrents
docker exec transmission transmission-remote -l

# Add torrent via CLI
docker exec transmission transmission-remote -a "magnet:?xt=..."

# Remove all torrents
docker exec transmission transmission-remote -t all -r
```

---

## Security

**Always use Authelia protection:**
```yaml
labels:
  - "traefik.http.routers.transmission.middlewares=authelia@docker"
```

Transmission is a powerful tool - keep it protected!

---

## Port Configuration

| Port | Purpose |
|------|---------|
| 9091 | Web UI |
| 51413 | BitTorrent TCP |
| 51413/udp | BitTorrent UDP |

---

## Maintenance

- Regularly clean up completed torrents
- Monitor disk space
- Review download directories
- Check settings.json for optimal configuration
