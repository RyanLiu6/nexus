# Nextcloud <img src="https://upload.wikimedia.org/wikipedia/commons/6/60/Nextcloud_Logo.svg" width="32">

[Nextcloud](https://nextcloud.com/) is an open-source file storage and collaboration platform.

Docker Image is from Linuxserver, found [here](https://hub.docker.com/r/linuxserver/nextcloud).

## Features

- **File Storage** - Sync and share files across devices
- **Collaboration** - Edit documents, manage calendars and contacts
- **Photos** - Automatic photo upload and organization
- **Extensions** - Huge library of apps (Notes, Deck, Talk, etc.)
- **Privacy** - Self-hosted, you own your data

## Setup

1. **Create an `.env` file:**
   ```ini
   CLOUD_DOMAIN=nextcloud.yourdomain.com
   MYSQL_PASSWORD=<secure password>
   MYSQL_DATABASE=nextcloud
   MYSQL_USER=nextcloud
   MYSQL_ROOT_PASSWORD=<secure password>
   ```

2. **Run:**
   ```bash
   docker compose up -d
   ```

3. **Complete the web setup wizard** on first access.

## Access

- **URL:** `https://nextcloud.${NEXUS_DOMAIN}`
- **Auth:** Tailscale + tailscale-access (plus internal Nextcloud auth)

## Data Storage

Nextcloud data is stored in `${NEXUS_DATA_DIRECTORY}/nextcloud`:

| Path | Contents |
|------|----------|
| `config/` | Nextcloud configuration files |
| `data/` | User files and data |
| `db/` | MariaDB database files |

## Backups

Ensure the entire data directory is included in your backup strategy.

```bash
# Backup database
docker exec nextcloud_db mysqldump -u root --password=<root password> nextcloud > backup.sql

# Backup data
tar -czf nextcloud-backup-$(date +%F).tar.gz ${NEXUS_DATA_DIRECTORY}/nextcloud
```

## Troubleshooting

### Cannot Access Nextcloud

**Symptoms:** 404 or connection refused

**Solutions:**
1. Check containers: `docker ps | grep nextcloud`
2. Verify Traefik labels
3. Check database: `docker ps | grep nextcloud_db`
4. View logs: `docker logs nextcloud`

### Database Connection Failed

**Symptoms:** "Database connection failed" error

**Solutions:**
1. Check database logs: `docker logs nextcloud_db`
2. Verify database credentials in `.env`
3. Ensure database container started first
4. Wait for database initialization on first run

### "Trusted Domain" Error

**Symptoms:** Nextcloud won't accept current domain

**Solution:**
```bash
docker exec -it nextcloud php /var/www/html/occ config:system:set trusted_domains 1 --value=nextcloud.yourdomain.com
```

### File Upload Issues

**Solutions:**
1. Check PHP upload limits in Nextcloud config
2. Verify storage permissions
3. Check disk space: `df -h`

## Operations

### Useful OCC Commands

```bash
# Check status
docker exec -it nextcloud php /var/www/html/occ status

# Scan files (re-index)
docker exec -it nextcloud php /var/www/html/occ files:scan --all

# Add missing database indices
docker exec -it nextcloud php /var/www/html/occ db:add-missing-indices

# Upgrade
docker exec -it nextcloud php /var/www/html/occ upgrade

# Cleanup locks
docker exec -it nextcloud php /var/www/html/occ files:cleanup
```

### Performance Tips

1. **Add Redis** for caching (not included by default)
2. **Increase PHP memory** if needed
3. **Set up cron** for background jobs
4. **Add indices**: Run `occ db:add-missing-indices` periodically

## Resources

- [Official Website](https://nextcloud.com/)
- [Admin Manual](https://docs.nextcloud.com/server/latest/admin_manual/)
- [User Manual](https://docs.nextcloud.com/server/latest/user_manual/)
- [Docker Hub](https://hub.docker.com/r/linuxserver/nextcloud)
