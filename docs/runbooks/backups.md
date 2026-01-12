# Backups Troubleshooting

## Common Issues

### Backup Jobs Not Running

**Symptoms**: No automatic backups happening

**Solutions**:
1. Check borgmatic container is running: `docker ps | grep borgmatic`
2. Check borgmatic logs: `docker logs borgmatic`
3. Verify crontab configuration in `services/backups/config/config.yml`
4. Ensure backup repository is accessible

### Backup Failing - Permission Denied

**Symptoms**: `Permission denied` errors in logs

**Solutions**:
1. Check SSH keys are mounted correctly
2. Verify backup directory permissions: `ls -la $NEXUS_BACKUP_DIRECTORY`
3. Fix permissions:
   ```bash
   chmod 700 $NEXUS_BACKUP_DIRECTORY
   chown $USER:$USER $NEXUS_BACKUP_DIRECTORY
   ```

### Backup Repository Corrupted

**Symptoms**: Cannot access or prune backups

**Solutions**:
1. Check repository integrity:
   ```bash
   docker exec -it borgmatic borg check --repair
   ```

2. If corrupted, create new repository and re-initialize

### Large Backup Sizes

**Symptoms**: Backups taking too much space

**Solutions**:
1. Exclude unnecessary directories from backup
2. Configure compression in borgmatic config
3. Prune old backups:
   ```bash
   docker exec -it borgmatic borg prune --keep-daily=7 --keep-weekly=4 --keep-monthly=6
   ```

## Useful Commands

```bash
# View backup logs
docker logs borgmatic -f

# Check backup status
docker exec borgmatic borgmatic list

# Manual backup
docker exec borgmatic borgmatic create

# List backups
docker exec borgmatic borg list

# Prune old backups
docker exec borgmatic borgmatic prune

# Extract specific backup
docker exec borgmatic borg extract --list ::archive-name
```

## Configuration Files

- `services/backups/config/config.yml` - Borgmatic configuration
- `services/backups/config/exclude.txt` - Files/directories to exclude
- `$NEXUS_BACKUP_DIRECTORY` - Backup repository location

## Setting Up Automated Backups

Edit `services/backups/config/config.yml` to set backup schedule:

```yaml
# Daily backups at 2 AM
hourly: []
daily:
  - 02:00
weekly: []
monthly: []
```

## Backup Destinations

### Local Storage
```yaml
location:
  - path: /mnt/repo
```

### S3 Compatible (Wasabi, Backblaze B2, Cloudflare R2)
```yaml
location:
  - rclone:
      type: s3
      endpoint: https://s3.wasabisys.com
      bucket: your-bucket-name
      access_key_id: YOUR_ACCESS_KEY
      secret_access_key: YOUR_SECRET_KEY
```

### SSH/SCP
```yaml
location:
  - scp:
      user: backup-user
      hostname: backup-server.com
      port: 22
      path: /backups/nexus
```

## Monitoring Backup Health

Set up Grafana alert for:
- Borgmatic container not running
- Backup job failure (check logs)
- Backup repository disk space low

## Recovery Testing

Regularly test your backups:

```bash
# 1. List backups
docker exec borgmatic borg list

# 2. Extract to test directory
docker exec borgmatic borg extract --dry-run ::latest

# 3. Full restore test
./scripts/restore.py --verify --backup nexus-backup.tar.gz
```

## Security

1. **Encrypt backups**: Borg uses encryption by default
2. **Store passphrase securely**: Use ansible-vault
3. **Test restore regularly**: Verify backup integrity
4. **Offsite storage**: Use cloud storage, not just local
5. **Access controls**: Restrict SSH keys to backup server only

## Troubleshooting Borgmatic

### Check Configuration
```bash
docker exec borgmatic borgmatic validate-config
```

### List What Will Be Backed Up
```bash
docker exec borgmatic borgmatic create --dry-run --list --stats
```

### Debug Mode
```bash
docker exec -it borgmatic borgmatic create --verbosity 2
```
