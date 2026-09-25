#!/usr/bin/env bash
# sync-backups.sh — Sync Home Assistant backups from HAOS VM to host disk.
#
# Pulls .tar backup files from the HAOS VM via SCP and stores them in
# /Volumes/Data/Config/homeassistant/backups/ so they are included in
# Backrest's daily snapshots.
#
# Usage: Intended to be run periodically via launchd (com.nexus.havm-backup-sync.plist).

set -euo pipefail

HAOS_HOST="192.168.50.161"
HAOS_PORT="22222"
HAOS_USER="root"
HAOS_BACKUP_DIR="/mnt/data/supervisor/backup"
LOCAL_BACKUP_DIR="/Volumes/Data/Config/homeassistant/backups"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10"
MAX_LOCAL_BACKUPS=5

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') [ha-backup-sync] $*"; }

# Ensure local backup directory exists
mkdir -p "$LOCAL_BACKUP_DIR"

# Check if HAOS VM is reachable
if ! ssh $SSH_OPTS -p "$HAOS_PORT" "$HAOS_USER@$HAOS_HOST" "true" 2>/dev/null; then
    log "ERROR: Cannot reach HAOS VM at $HAOS_HOST:$HAOS_PORT — skipping sync"
    exit 1
fi

# List remote backups
remote_files=$(ssh $SSH_OPTS -p "$HAOS_PORT" "$HAOS_USER@$HAOS_HOST" \
    "ls -1 $HAOS_BACKUP_DIR/*.tar 2>/dev/null" || true)

if [[ -z "$remote_files" ]]; then
    log "No backups found on HAOS VM — nothing to sync"
    exit 0
fi

# Sync each backup that doesn't already exist locally
# Uses scp -O (legacy SCP protocol) because HAOS lacks sftp-server
synced=0
while IFS= read -r remote_path; do
    filename=$(basename "$remote_path")
    local_path="$LOCAL_BACKUP_DIR/$filename"

    if [[ -f "$local_path" ]]; then
        continue
    fi

    log "Syncing: $filename"
    scp -O $SSH_OPTS -P "$HAOS_PORT" \
        "$HAOS_USER@$HAOS_HOST:$remote_path" "$local_path"
    ((synced++)) || true
done <<< "$remote_files"

log "Synced $synced new backup(s)"

# Prune old local backups, keeping only the newest MAX_LOCAL_BACKUPS
local_count=$(find "$LOCAL_BACKUP_DIR" -name "*.tar" -type f | wc -l | tr -d ' ')
if (( local_count > MAX_LOCAL_BACKUPS )); then
    pruned=0
    while IFS= read -r old_file; do
        log "Pruning old backup: $(basename "$old_file")"
        rm -f "$old_file"
        ((pruned++)) || true
    done < <(ls -1t "$LOCAL_BACKUP_DIR"/*.tar | tail -n +"$((MAX_LOCAL_BACKUPS + 1))")
    log "Pruned $pruned old backup(s)"
fi

log "Done"
