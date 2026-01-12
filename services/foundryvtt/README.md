# FoundryVTT <img src="https://foundryvtt.com/static/assets/icons/fvtt.png" width="24">

[FoundryVTT](https://foundryvtt.com/) is a powerful software to play role-playing tabletop games online.

Docker Image is from felddy, found [here](https://hub.docker.com/r/felddy/foundryvtt).

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

## Backups

```bash
# Weekly backup
0 0 * * 4 tar -cf $DATA_DIRECTORY/Backups/Foundry/$(date +%F).tar $DATA_DIRECTORY/Foundry/data
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

## Player Access

### Public Access (Recommended for Games)

Remove Authelia middleware to allow players direct access:
```yaml
labels:
  # No authelia middleware
  - "traefik.http.routers.foundryvtt.middlewares=security-headers@docker"
```

Players use Foundry's built-in authentication.

### Protected Access

Keep Authelia middleware for extra security:
```yaml
labels:
  - "traefik.http.routers.foundryvtt.middlewares=authelia@docker"
```

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

## Backup & Restore

```bash
# Backup
cp -r $DATA_DIRECTORY/Foundry/data $BACKUP_DIR/foundry-$(date +%Y%m%d)

# Restore
docker stop foundryvtt
cp -r $BACKUP_DIR/foundry-20250111/* $DATA_DIRECTORY/Foundry/data/
docker start foundryvtt
```
