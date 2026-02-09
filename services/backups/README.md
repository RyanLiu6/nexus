# Backups - Backrest

Automated backup system using [Backrest](https://github.com/garethgeorge/backrest) as a web UI and orchestrator for [restic](https://restic.net/).

## Overview

Backrest provides:
- **Web UI** for managing backups at `backups.<domain>` (Tailscale access only)
- **Automated scheduling** via built-in cron (daily backups at 2 AM local, 3 AM for R2)
- **Dual repositories**: Local backups (3-day retention) + optional Cloudflare R2 (1-day retention)
- **restic backend**: Fast, deduplicated, encrypted backups with rclone integration

## Configuration

### Repositories

Two backup repositories are configured:

1. **local** (`/repos` in container → `${NEXUS_DATA_DIRECTORY}/Backups` on host)
   - 3 daily snapshots retained
   - Fast local recovery
   - Automatic pruning
   - Auto-initializes on first container start (`autoInitialize: true`)

2. **r2** (optional, Cloudflare R2 via rclone)
   - 1 daily snapshot retained
   - Off-site disaster recovery
   - Only active if `backups_r2_access_key` is configured
   - Auto-initializes on first container start (`autoInitialize: true`)

### Backup Plans

- **daily-local**: Runs at 2:00 AM, backs up `/userdata` (container path for `Config/`)
- **daily-r2**: Runs at 3:00 AM, backs up `/userdata` to R2 (if R2 is enabled)

### Encryption

All repositories use the `restic_password` from Ansible vault. **Store this securely** - backups are unrecoverable without it.

## Web UI Access

Navigate to `backups.<domain>` (e.g., `backups.example.com`). Access is restricted to the `admins` Tailscale group.

**Authentication:** Backrest's built-in auth is disabled. Access control is handled entirely by Tailscale ACLs.

From the UI you can:
- View backup history and snapshots
- Manually trigger backups
- Browse and restore individual files
- Monitor backup status and storage usage

## CLI Operations

All restic commands run inside the `backrest` container.

### List Snapshots

```bash
docker exec backrest restic -r /repos snapshots
```

### Verify Repository Integrity

```bash
docker exec backrest restic -r /repos check
```

### Restore Specific Service

```bash
docker exec backrest restic -r /repos restore <snapshot_id> \
  --target /tmp/restore \
  --include /userdata/<service_name>
```

Example - restore Jellyfin config:

```bash
docker exec backrest restic -r /repos restore abc123 \
  --target /tmp/restore \
  --include /userdata/jellyfin
```

### Restore Entire Backup

```bash
docker exec backrest restic -r /repos restore latest \
  --target /tmp/restore
```

Restored files appear in the container at `/tmp/restore/userdata/`. Copy them to the host:

```bash
docker cp backrest:/tmp/restore/userdata/<service> \
  ${NEXUS_DATA_DIRECTORY}/Config/<service>
```

### Check R2 Connectivity

```bash
docker exec backrest rclone ls r2:<bucket_name>
```

### Manual Backup

Trigger via Web UI or use restic directly:

```bash
docker exec backrest restic -r /repos backup /userdata
```

## Python CLI Integration

The `nexus restore` command provides a higher-level interface:

```bash
# List available snapshots
nexus restore --list

# Restore a specific snapshot (extracts to /tmp/restore, requires manual docker cp)
nexus restore --snapshot abc123

# Restore specific service
nexus restore --snapshot abc123 --service jellyfin

# Restore database from backup
nexus restore --snapshot abc123 --db /path/to/dump.sql --service <service_name>

# Verify backup integrity
nexus restore --verify

# Dry run (preview only)
nexus restore --snapshot abc123 --dry-run
```

**Note:** The `nexus restore` command extracts files to `/tmp/restore` inside the container. You must manually copy them to the host using `docker cp` (see Recovery Scenarios below).

## Troubleshooting

### Backrest Won't Start

Check if repos need initialization:

```bash
docker logs backrest
```

If you see "repository does not exist" errors, Backrest should auto-initialize on first run (`autoInitialize: true` is enabled). If auto-initialization fails:

```bash
docker exec backrest restic -r /repos init
```

### R2 Connection Fails

Verify rclone config is mounted and valid:

```bash
docker exec backrest rclone config show
docker exec backrest rclone ls r2:
```

Check that Terraform provisioned R2 credentials correctly in `ansible/vars/vault.yml`.

### Backups Not Running

Check the schedule in the Web UI under Plans → Edit. Ensure the cron expression is valid and not disabled.

View logs:

```bash
docker logs backrest
```

### Out of Space

Local backups retain 3 days; R2 retains 1 day. Pruning happens automatically after each backup. To manually prune:

```bash
docker exec backrest restic -r /repos forget --keep-last 3 --prune
```

## Recovery Scenarios

### Restore Single File

1. List snapshots: `docker exec backrest restic -r /repos snapshots`
2. Restore to temp location:
   ```bash
   docker exec backrest restic -r /repos restore <snapshot_id> \
     --target /tmp/restore \
     --include /userdata/<service>/<filename>
   ```
3. Copy to host: `docker cp backrest:/tmp/restore/userdata/<service>/<filename> ...`

### Full Service Restore

```bash
# Stop service
docker compose stop <service>

# Restore from backup
nexus restore --snapshot <id> --service <service>

# Copy restored files
docker cp backrest:/tmp/restore/userdata/<service> \
  ${NEXUS_DATA_DIRECTORY}/Config/

# Start service
docker compose up -d <service>
```

### Disaster Recovery (from R2)

1. Re-deploy Nexus infrastructure
2. Set `restic_password` in vault to original value
3. Configure R2 credentials (Terraform outputs)
4. List R2 snapshots:
   ```bash
   docker exec backrest restic -r rclone:r2:<bucket> snapshots
   ```
5. Restore latest:
   ```bash
   docker exec backrest restic -r rclone:r2:<bucket> restore latest \
     --target /tmp/restore
   ```

## Maintenance

- **Daily**: Automated backups run at 2 AM (local) and 3 AM (R2)
- **Weekly**: `nexus maintenance weekly` verifies backups exist
- **Monthly**: Rotate `restic_password` if using a password rotation policy
