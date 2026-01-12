# Nextcloud Troubleshooting

## Common Issues

### Cannot Access Nextcloud

**Symptoms**: 404 or connection refused

**Solutions**:
1. Check container is running: `docker ps | grep nextcloud`
2. Verify Traefik labels
3. Check database is running: `docker ps | grep nextcloud_db`
4. Review logs: `docker logs nextcloud`

### Database Connection Failed

**Symptoms**: "Database connection failed" error

**Solutions**:
1. Check database logs: `docker logs nextcloud_db`
2. Verify database credentials in `.env`
3. Ensure database container started before Nextcloud
4. Check MariaDB version compatibility

### "Trusted Domain" Error

**Symptoms**: Nextcloud won't accept current domain

**Solutions**:
1. Access Nextcloud container shell:
   ```bash
   docker exec -it nextcloud bash
   ```

2. Edit config:
   ```bash
   /var/www/html/occ config:system:set trusted_domains 1 nextcloud.yourdomain.com
   ```

3. Restart Nextcloud

### File Upload Issues

**Symptoms**: Cannot upload files, uploads fail

**Solutions**:
1. Check PHP upload limits in Nextcloud config
2. Verify storage permissions
3. Check disk space
4. Review upload logs

## Useful Commands

```bash
# View Nextcloud logs
docker logs nextcloud -f

# Restart Nextcloud
docker restart nextcloud

# Access Nextcloud shell
docker exec -it nextcloud bash

# Run Nextcloud occ commands
docker exec -it nextcloud php /var/www/html/occ [command]

# Check database logs
docker logs nextcloud_db
```

## Configuration Files

- `services/nextcloud/docker-compose.yml` - Container configuration
- `$NEXUS_ROOT_DIRECTORY/Data/nextcloud/` - Nextcloud data
- `.env` - Database credentials

## Common OCC Commands

```bash
# Check Nextcloud status
docker exec -it nextcloud php /var/www/html/occ status

# Add trusted domain
docker exec -it nextcloud php /var/www/html/occ config:system:set trusted_domains 1 nextcloud.yourdomain.com

# Scan files for new users
docker exec -it nextcloud php /var/www/html/occ files:scan --all

# Check database integrity
docker exec -it nextcloud php /var/www/html/occ db:add-missing-indices

# Update Nextcloud
docker exec -it nextcloud php /var/www/html/occ upgrade
```

## Performance Optimization

### Enable Caching
```yaml
# In docker-compose.yml - add Redis (not currently included)
environment:
  - REDIS_HOST=redis
  - REDIS_PORT=6379
```

### Increase PHP Memory Limit
```bash
docker exec -it nextcloud php -d memory_limit=512M /var/www/html/occ config:system:set php_memory_limit
```

### Background Jobs
Set up cron for background jobs:

```bash
docker exec -it nextcloud php /var/www/html/occ background:cron
```

## Backup & Restore

### Backup Nextcloud
```bash
# Stop containers
docker stop nextcloud nextcloud_db

# Backup database
docker exec nextcloud_db mysqldump -u root -p nextcloud > nextcloud-db-backup.sql

# Backup data
tar -czf nextcloud-backup.tar.gz $NEXUS_ROOT_DIRECTORY/Data/nextcloud/

# Start containers
docker start nextcloud_db nextcloud
```

### Restore Nextcloud
```bash
# Stop containers
docker stop nextcloud nextcloud_db

# Restore database
cat nextcloud-db-backup.sql | docker exec -i nextcloud_db mysql -u root -p nextcloud

# Restore data
tar -xzf nextcloud-backup.tar.gz -C /

# Start containers
docker start nextcloud_db nextcloud
```

## Storage Configuration

### External Storage (SMB)
1. Access Nextcloud as admin
2. Settings → Administration → External Storage
3. Add SMB/CIFS storage
4. Configure share credentials

### External Storage (S3)
1. Settings → Administration → External Storage
2. Add Amazon S3 or compatible storage
3. Configure bucket, endpoint, credentials
4. Enable for users

## Security

1. **HTTPS only**: Force HTTPS via Traefik
2. **Strong passwords**: Enforce password policies
3. **2FA**: Enable two-factor authentication
4. **Regular updates**: Keep Nextcloud updated
5. **Audit logs**: Review access logs regularly

## Troubleshooting Common Errors

### "Internal Server Error"
- Check database connection
- Review PHP error logs
- Verify file permissions
- Check disk space

### "Login Failed"
- Verify user exists
- Check password
- Clear browser cache
- Check Nextcloud logs

### "File Locked"
- Unlock file via admin panel
- Check for zombie processes
- Clear Nextcloud locks:
  ```bash
  docker exec -it nextcloud php /var/www/html/occ files:cleanup
  ```

## Integration with Authelia

### Wife Group Access
Configure Authelia to allow wife access to Nextcloud:

```yaml
# services/auth/configuration.yml
access_control:
  rules:
    - domain: "nextcloud.yourdomain.com"
      policy: one_factor
      subject: "group:wife"
```

### User Setup
1. Create wife user in Authelia
2. Create corresponding user in Nextcloud
3. Set appropriate permissions in Nextcloud
