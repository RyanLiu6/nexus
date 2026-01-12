# Backups (Borgmatic)

Automated backups using [Borgmatic](https://torsion.org/borgmatic/), a wrapper for the Borg backup tool.

## Setup

1. **Create `.env`** from sample.

2. **Create `config.yaml`** in `backups/config/` (see [Borgmatic docs](https://torsion.org/borgmatic/docs/how-to/set-up-backups/)).

3. **Initialize the repository:**
   ```bash
   docker compose run --rm borgmatic borg init --encryption=repokey
   ```

4. **Run:**
   ```bash
   docker compose up -d
   ```

## Configuration Files

| File | Purpose |
|------|---------|
| `config/config.yml` | Borgmatic configuration (sources, schedule, retention) |
| `config/exclude.txt` | Files/directories to exclude |
| `$NEXUS_BACKUP_DIRECTORY` | Backup repository location |

---

## Backup Destinations

### Local Storage
```yaml
location:
  repositories:
    - /mnt/repo
```

### S3 Compatible (Wasabi, Backblaze B2, Cloudflare R2)
```yaml
location:
  repositories:
    - s3://s3.wasabisys.com/your-bucket-name
```

### SSH/Remote
```yaml
location:
  repositories:
    - ssh://backup-user@backup-server.com/backups/nexus
```

---

## Useful Commands

```bash
# View backup logs
docker logs borgmatic -f

# Check backup status
docker exec borgmatic borgmatic list

# Run manual backup
docker exec borgmatic borgmatic create

# List all backups
docker exec borgmatic borg list

# Prune old backups
docker exec borgmatic borgmatic prune

# Extract specific backup
docker exec borgmatic borg extract --list ::archive-name

# Validate configuration
docker exec borgmatic borgmatic validate-config

# Dry run (show what would be backed up)
docker exec borgmatic borgmatic create --dry-run --list --stats

# Debug mode
docker exec -it borgmatic borgmatic create --verbosity 2
```

---

## Troubleshooting

### Backup Jobs Not Running

**Symptoms:** No automatic backups

**Solutions:**
1. Check borgmatic container: `docker ps | grep borgmatic`
2. Check logs: `docker logs borgmatic`
3. Verify schedule in `config/config.yml`
4. Ensure backup repository is accessible

### Permission Denied

**Symptoms:** `Permission denied` errors in logs

**Solutions:**
1. Check SSH keys are mounted correctly
2. Verify backup directory permissions:
   ```bash
   chmod 700 $NEXUS_BACKUP_DIRECTORY
   chown $USER:$USER $NEXUS_BACKUP_DIRECTORY
   ```

### Repository Corrupted

**Symptoms:** Cannot access or prune backups

**Solutions:**
1. Check repository integrity:
   ```bash
   docker exec -it borgmatic borg check --repair
   ```
2. If severely corrupted, create new repository

### Large Backup Sizes

**Solutions:**
1. Exclude unnecessary directories in `exclude.txt`
2. Configure compression in borgmatic config
3. Prune more aggressively:
   ```bash
   docker exec borgmatic borg prune --keep-daily=7 --keep-weekly=4 --keep-monthly=6
   ```

---

## Backup Schedule

Example schedule in `config/config.yml`:

```yaml
# Daily backups at 2 AM
crontab:
  jobs:
    - name: daily
      schedule: "0 2 * * *"
      command: borgmatic create --stats
```

---

## Recovery Testing

**Regularly test your backups!**

```bash
# 1. List backups
docker exec borgmatic borg list

# 2. Dry run extract
docker exec borgmatic borg extract --dry-run ::latest

# 3. Test restore to temp directory
docker exec borgmatic borg extract --path /tmp/restore ::latest
```

---

## Security

1. **Encrypt backups**: Borg uses encryption by default
2. **Store passphrase securely**: Use ansible-vault for `borg_passphrase`
3. **Test restore regularly**: Verify backup integrity
4. **Offsite storage**: Use cloud storage, not just local
5. **Access controls**: Restrict SSH keys to backup server only
