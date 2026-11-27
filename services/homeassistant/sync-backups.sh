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
SSH_KEY="$HOME/.ssh/ha_key"
SSH_OPTS="-i $SSH_KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10"
MAX_LOCAL_BACKUPS=3

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') [ha-backup-sync] $*"; }

# Ensure local backup directory exists
mkdir -p "$LOCAL_BACKUP_DIR"

# Check if HAOS VM is reachable
if ! ssh $SSH_OPTS -p "$HAOS_PORT" "$HAOS_USER@$HAOS_HOST" "true" 2>/dev/null; then
    log "ERROR: Cannot reach HAOS VM at $HAOS_HOST:$HAOS_PORT — skipping sync"
    exit 1
fi

# List newest MAX_LOCAL_BACKUPS remote backups (sorted newest-first by remote mtime)
remote_files=$(ssh $SSH_OPTS -p "$HAOS_PORT" "$HAOS_USER@$HAOS_HOST" \
    "ls -1t $HAOS_BACKUP_DIR/*.tar 2>/dev/null | head -n $MAX_LOCAL_BACKUPS" || true)

if [[ -z "$remote_files" ]]; then
    log "No backups found on HAOS VM — nothing to sync"
    exit 0
fi

# Sync each of the newest backups that doesn't already exist locally.
# Uses scp -O (legacy SCP protocol) because HAOS lacks sftp-server, and -p to preserve remote mtime.
synced=0
while IFS= read -r remote_path; do
    filename=$(basename "$remote_path")
    local_path="$LOCAL_BACKUP_DIR/$filename"

    if [[ -f "$local_path" ]]; then
        continue
    fi

    log "Syncing: $filename"
    scp -O -p $SSH_OPTS -P "$HAOS_PORT" \
        "$HAOS_USER@$HAOS_HOST:$remote_path" "$local_path"
    ((synced++)) || true
done <<< "$remote_files"

log "Synced $synced new backup(s)"

# Prune local backups that are no longer in the newest MAX_LOCAL_BACKUPS remote set
pruned=0
while IFS= read -r local_file; do
    [[ -z "$local_file" ]] && continue
    local_name=$(basename "$local_file")
    keep=false
    while IFS= read -r remote_path; do
        if [[ "$(basename "$remote_path")" == "$local_name" ]]; then
            keep=true
            break
        fi
    done <<< "$remote_files"
    if [[ "$keep" == false ]]; then
        log "Pruning old backup: $local_name"
        rm -f "$local_file"
        ((pruned++)) || true
    fi
done < <(find "$LOCAL_BACKUP_DIR" -maxdepth 1 -name "*.tar" -type f)
if (( pruned > 0 )); then
    log "Pruned $pruned old backup(s)"
fi

log "Done"
