# FoundryVTT <img src="https://foundryvtt.com/static/assets/icons/fvtt.png" width="24">

[FoundryVTT](https://foundryvtt.com/) is a powerful software to play role-playing tabletop games online.

Docker Image is from felddy, found [here](https://hub.docker.com/r/felddy/foundryvtt).

## Features

- **Self-Hosted** - You own your data, no subscription fees
- **Modern Web Tech** - HTML5, CSS3, WebGL, and WebSockets
- **System Agnostic** - Support for D&D, Pathfinder, and hundreds more
- **Extensible** - Huge library of community modules and systems
- **Direct Connection** - Players connect directly to your server (via Cloudflare Tunnel)

## Setup

1. **Create an `.env` file:**
   ```ini
   PLAY_DOMAIN=foundry.yourdomain.com
   FOUNDRY_USERNAME=<foundryvtt.com username>
   FOUNDRY_PASSWORD=<foundryvtt.com password>
   FOUNDRY_ADMIN_KEY=<foundry admin key>
   DATA_DIRECTORY=/path/to/data
   ```

2. **Configure data directory** in `docker-compose.yml`:
   ```yaml
   volumes:
     - ${DATA_DIRECTORY}/Foundry/data:/data
   ```

3. **Run:**
   ```bash
   docker compose up -d
   ```

## Optional: AWS S3 Support

1. Create an IAM user with S3 bucket access
2. Create `s3.json`:
   ```json
   {
     "accessKeyId": "<AWS Access ID>",
     "secretAccessKey": "<AWS Secret Key>",
     "region": "<AWS Region>"
   }
   ```
3. Place at `$DATA_DIRECTORY/Foundry/data/Config/s3.json`

## Optional: Native Audio/Video

Edit `${DATA_DIRECTORY}/Foundry/data/Config/options.json`:
```json
"proxySSL": true
```

## Access

FoundryVTT has two access methods:

### Public Access (Players)
- **URL:** `https://${PLAY_DOMAIN}`
- **Auth:** Application-level (Foundry User/Pass)
- **Route:** Cloudflare Tunnel (bypasses Tailscale)

### Private Access (Admin)
- **URL:** `https://${PLAY_DOMAIN}` (via Tailscale subnet or same URL)
- **Auth:** Application-level + Tailscale (if accessed internally)

## Data Storage

FoundryVTT stores data in `${DATA_DIRECTORY}/Foundry`:

| Path | Contents |
|------|----------|
| `data/Data/` | Worlds, systems, modules, and uploaded assets |
| `data/Config/` | Server configuration and options |
| `data/Logs/` | Debug logs |

## Backups

### Automated Backups
The `backups` service (Borgmatic) handles this automatically if configured.

### Manual Backup
```bash
# Backup
docker stop foundryvtt
tar -czf foundry-backup-$(date +%F).tar.gz ${DATA_DIRECTORY}/Foundry/data
docker start foundryvtt
```

### Restore
```bash
docker stop foundryvtt
tar -xzf foundry-backup-YYYY-MM-DD.tar.gz -C /
docker start foundryvtt
```

---

## Troubleshooting

### Foundry Not Starting

1. Check logs: `docker logs foundryvtt`
2. Verify license key is valid
3. Check data directory permissions
4. Ensure port 30000 is available

### License Issues

1. Update license key in `.env`
2. Restart container: `docker restart foundryvtt`
3. Check Foundry account status

### Performance Issues

1. Enable asset caching in Foundry settings
2. Compress WebSockets in settings
3. Limit concurrent connections
4. Optimize images and assets

---



## Useful Commands

```bash
# View logs
docker logs foundryvtt -f

# Restart
docker restart foundryvtt

# Access shell
docker exec -it foundryvtt sh

# Check stats
docker stats foundryvtt
```

---

## Resources

- [Official Website](https://foundryvtt.com/)
- [Knowledge Base](https://foundryvtt.com/kb/)
- [Community Wiki](https://foundryvtt.wiki/)
- [Docker Image Docs](https://hub.docker.com/r/felddy/foundryvtt)
