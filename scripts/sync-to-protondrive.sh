#!/usr/bin/env bash
# =============================================================================
# TEMPORARY WORKAROUND - ProtonDrive Backup via rsync
# =============================================================================
# Rsyncs a local directory to a ProtonDrive-mounted destination.
# Used for both restic backup repos and raw user data (paperless, bookorbit).
# This is a workaround until rclone adds ProtonDrive support.
#
# Migration to rclone (when available):
#   1. Add a ProtonDrive rclone remote: rclone config
#   2. For restic repos: add a third repo in services/backups/config.json.j2
#   3. For raw data: add rclone sync tasks in Ansible
#   4. Clear protondrive_sync_directory in vault — deploy removes the crontabs
#   5. Delete this script
#
# Usage: sync-to-protondrive.sh <source_dir> <dest_dir> [container...]
#   Containers (optional): stopped before sync, restarted after (even on failure).
# Schedule: 30 3 * * * /path/to/nexus/scripts/sync-to-protondrive.sh <src> <dest>
#
# Failures fire a critical alert to Discord via DISCORD_WEBHOOK_URL
# (loaded from environment or repo root .env).
# =============================================================================

set -euo pipefail

# macOS: extend PATH to cover Docker Desktop (/usr/local/bin), Homebrew (/opt/homebrew/bin),
# and OrbStack (~/.orbstack/bin). On Linux, docker is on system PATH via package manager.
if [[ "$(uname)" == "Darwin" ]]; then
    export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.orbstack/bin:$HOME/.local/bin:$PATH"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

SOURCE_DIR="${1:?Usage: sync-to-protondrive.sh <source_dir> <dest_dir> [container...]}"
DEST_DIR="${2:?Usage: sync-to-protondrive.sh <source_dir> <dest_dir> [container...]}"
shift 2
CONTAINERS=("$@")
TAG="$(basename "$SOURCE_DIR")"
if [[ -z "${DISCORD_WEBHOOK_URL:-}" && -f "$ENV_FILE" ]]; then
    DISCORD_WEBHOOK_URL="$(grep -E '^DISCORD_WEBHOOK_URL=' "$ENV_FILE" | head -n1 | cut -d= -f2- || true)"
fi
FAILURE_REASON=""

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$TAG] $*"
}

fire_failed_alert() {
    local reason="$1"
    if [[ -z "${DISCORD_WEBHOOK_URL:-}" ]]; then
        log "WARNING: DISCORD_WEBHOOK_URL not set; skipping Discord alert"
        return 0
    fi

    # Basic JSON escaping: backslashes first, then quotes, then collapse newlines
    local escaped="${reason//\\/\\\\}"
    escaped="${escaped//\"/\\\"}"
    escaped="${escaped//$'\n'/ }"

    curl --silent --max-time 10 \
        --request POST "${DISCORD_WEBHOOK_URL}" \
        --header "Content-Type: application/json" \
        --data "{
            \"username\": \"Nexus Backup Sync\",
            \"embeds\": [{
                \"title\": \"🚨 ProtonDrive sync failed (${TAG})\",
                \"description\": \"${escaped}\",
                \"color\": 15158332
            }]
        }" || log "WARNING: Failed to send Discord webhook alert"
}

on_exit() {
    local exit_code=$?
    set +e
    if [ ${#CONTAINERS[@]} -gt 0 ]; then
        log "Starting containers: ${CONTAINERS[*]}"
        docker start "${CONTAINERS[@]}" || log "WARNING: Some containers failed to start"
    fi
    if [ $exit_code -ne 0 ]; then
        local reason="${FAILURE_REASON:-exited with code $exit_code}"
        log "FAILED: $reason"
        fire_failed_alert "$reason"
    fi
}

trap on_exit EXIT

if [ ! -d "$SOURCE_DIR" ]; then
    FAILURE_REASON="source directory does not exist: $SOURCE_DIR"
    exit 1
fi

if ! mkdir -p "$DEST_DIR"; then
    FAILURE_REASON="could not create destination $DEST_DIR — is Proton Drive Bridge running and mounted?"
    exit 1
fi

if [ ${#CONTAINERS[@]} -gt 0 ]; then
    log "Stopping containers: ${CONTAINERS[*]}"
    docker stop "${CONTAINERS[@]}"
fi

log "Starting rsync: $SOURCE_DIR -> $DEST_DIR"

rsync_out=""
set +e
rsync_out=$(rsync --archive --no-owner --no-group --delete \
    --exclude='locks/**' \
    --exclude='.DS_Store' \
    "$SOURCE_DIR/" "$DEST_DIR/" 2>&1)
rsync_code=$?
set -e

if [ $rsync_code -ne 0 ] && [ $rsync_code -ne 24 ]; then
    FAILURE_REASON="rsync failed (exit $rsync_code): ${rsync_out:-no output}"
    exit "$rsync_code"
fi

if [ $rsync_code -eq 24 ]; then
    log "WARNING: Some source files vanished during sync (code 24), transfer completed successfully"
fi

log "Sync complete"
