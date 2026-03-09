# Backups - Backrest

Automated backup system using [Backrest](https://github.com/garethgeorge/backrest) as a web UI for [restic](https://restic.net/).

## Overview

- **Web UI** at `backups.<domain>` (Tailscale access only, auth disabled)
- **Dual repositories**: Local (3-day retention) + optional Cloudflare R2 (1-day retention)
- **Two data sources**: `/base_data` (service configs) and `/user_data` (large user data)
- **R2 cost control**: R2 only backs up `/base_data` (configs). Large user data (paperless documents, booklore books, foundryvtt worlds, sure data) stays local-only via `/user_data`

## Configuration

### Repositories

| Repo | Storage | Retention | Purpose |
|------|---------|-----------|---------|
| **local** | `/repos` → `${NEXUS_DATA_DIRECTORY}/Backups` | 3 daily | Fast local recovery |
| **r2** | Cloudflare R2 via rclone | 1 daily | Off-site disaster recovery |

R2 is optional — only active when `backups_r2_access_key` is configured. Both repos auto-initialize on first start.

### Backup Plans

| Plan | Schedule | Repo | Paths | Purpose |
|------|----------|------|-------|---------|
| **daily-local** | 2:00 AM | local | `/base_data`, `/user_data` | Full backup of everything |
| **daily-r2** | 3:00 AM | r2 | `/base_data` only | Off-site configs only |

### Volume Mounts

| Container Path | Host Path | Description |
|----------------|-----------|-------------|
| `/base_data` (ro) | `Config/` | Service configurations and databases |
| `/user_data` (ro) | `$NEXUS_USERDATA_DIRECTORY` | Large user data (documents, books, etc.) |
| `/repos` | `Backups/` | Restic repository storage |

### Encryption

All repositories use `restic_password` from Ansible vault. **Store this securely** — backups are unrecoverable without it.

## CLI Operations

All commands run inside the `backrest` container:

```bash
# List snapshots
docker exec backrest restic -r /repos snapshots

# Verify integrity
docker exec backrest restic -r /repos check

# Restore specific service
docker exec backrest restic -r /repos restore <snapshot_id> \
  --target /tmp/restore \
  --include /base_data/<service_name>

# Manual backup
docker exec backrest restic -r /repos backup /base_data /user_data

# Check R2 connectivity
docker exec backrest rclone ls r2:<bucket_name>

# Manual prune
docker exec backrest restic -r /repos forget --keep-last 3 --prune
```

The `nexus restore` CLI provides a higher-level interface — run `nexus restore --help` for options.

## Recovery

### Single Service

```bash
docker compose stop <service>
docker exec backrest restic -r /repos restore <snapshot_id> \
  --target /tmp/restore --include /base_data/<service>
docker cp backrest:/tmp/restore/base_data/<service> ${NEXUS_DATA_DIRECTORY}/Config/
docker compose up -d <service>
```

### Disaster Recovery (from R2)

1. Re-deploy Nexus infrastructure
2. Set `restic_password` in vault to original value
3. Configure R2 credentials (Terraform outputs)
4. Restore: `docker exec backrest restic -r rclone:r2:<bucket> restore latest --target /tmp/restore`

> **Note:** R2 backups only contain service configs (`/base_data`), not user data. Large data (documents, books, worlds) must be restored from local backups or original sources.

## ProtonDrive Sync (Temporary)

> **Workaround** until [rclone adds ProtonDrive support](https://github.com/rclone/rclone/issues/5804). Once available, replace with a third rclone remote in `config.json.j2`.

Rsyncs the entire restic repo to a ProtonDrive-mounted directory daily at 4 AM. Uses `--delete` so ProtonDrive always has exactly one copy mirroring the local repo.

**Enable:** Set `protondrive_sync_directory` in vault (e.g., `/Volumes/ProtonDrive/nexus-backups`). The crontab is installed/removed automatically on deploy.

**Migrate to rclone:**
1. Add a ProtonDrive rclone remote (`rclone config`)
2. Add a third repo in `config.json.j2` pointing to the rclone remote
3. Clear `protondrive_sync_directory` in vault — deploy removes the crontab
4. Delete `scripts/sync-to-protondrive.sh`

## Maintenance

- **Daily**: Automated backups at 2 AM (local), 3 AM (R2), 4 AM (ProtonDrive rsync if enabled)
- **Weekly**: `nexus maintenance weekly` verifies backups exist
