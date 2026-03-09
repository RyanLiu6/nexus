#!/bin/bash
# =============================================================================
# TEMPORARY WORKAROUND - ProtonDrive Backup via rsync
# =============================================================================
# Syncs the local restic backup repository to a ProtonDrive-mounted directory.
# This is a workaround until rclone adds ProtonDrive support.
#
# Migration to rclone (when available):
#   1. Add a ProtonDrive rclone remote: rclone config
#   2. Add a third repo in services/backups/config.json.j2
#   3. Remove protondrive_sync_directory from vault.yml
#   4. Run deploy to remove the crontab automatically
#   5. Delete this script
#
# Usage: sync-to-protondrive.sh <source_dir> <dest_dir>
# Crontab: 0 4 * * * /path/to/nexus/scripts/sync-to-protondrive.sh <src> <dest>
# =============================================================================

set -euo pipefail

SOURCE_DIR="${1:?Usage: sync-to-protondrive.sh <source_dir> <dest_dir>}"
DEST_DIR="${2:?Usage: sync-to-protondrive.sh <source_dir> <dest_dir>}"
LOG_FILE="/tmp/protondrive-sync.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Validate paths
if [ ! -d "$SOURCE_DIR" ]; then
    log "ERROR: Source directory does not exist: $SOURCE_DIR"
    exit 1
fi

if [ ! -d "$DEST_DIR" ]; then
    log "ERROR: Destination directory does not exist: $DEST_DIR"
    log "Is Proton Drive Bridge running and mounted?"
    exit 1
fi

log "Starting rsync: $SOURCE_DIR -> $DEST_DIR"

rsync --archive --delete --quiet "$SOURCE_DIR/" "$DEST_DIR/"

log "Sync complete"
