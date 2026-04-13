#!/usr/bin/env bash
# =============================================================================
# TEMPORARY WORKAROUND - ProtonDrive Backup via rsync
# =============================================================================
# Rsyncs a local directory to a ProtonDrive-mounted destination.
# Used for both restic backup repos and raw user data (paperless, grimmory).
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
# Schedule: 0 4 * * * /path/to/nexus/scripts/sync-to-protondrive.sh <src> <dest>
#
# Failures fire a critical alert to Alertmanager with the failure reason.
# Override the Alertmanager URL via ALERTMANAGER_URL (default: http://localhost:9093).
# =============================================================================

set -euo pipefail

# macOS: extend PATH to cover Docker Desktop (/usr/local/bin), Homebrew (/opt/homebrew/bin),
# and OrbStack (~/.orbstack/bin). On Linux, docker is on system PATH via package manager.
if [[ "$(uname)" == "Darwin" ]]; then
    export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.orbstack/bin:$HOME/.local/bin:$PATH"
fi

SOURCE_DIR="${1:?Usage: sync-to-protondrive.sh <source_dir> <dest_dir> [container...]}"
DEST_DIR="${2:?Usage: sync-to-protondrive.sh <source_dir> <dest_dir> [container...]}"
shift 2
CONTAINERS=("$@")
TAG="$(basename "$SOURCE_DIR")"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
FAILURE_REASON=""

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$TAG] $*"
}

fire_failed_alert() {
    local reason="$1"
    local ends_at
    # Resolve expires 25h from now so the alert auto-clears if the next run succeeds
    ends_at=$(date -u -d '+25 hours' '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null \
        || date -u -v+25H '+%Y-%m-%dT%H:%M:%SZ')

    # Basic JSON escaping: backslashes first, then quotes, then collapse newlines
    local escaped="${reason//\\/\\\\}"
    escaped="${escaped//\"/\\\"}"
    escaped="${escaped//$'\n'/ }"

    curl --silent --max-time 10 \
        --request POST "${ALERTMANAGER_URL}/api/v2/alerts" \
        --header "Content-Type: application/json" \
        --data "[{
            \"labels\": {
                \"alertname\": \"ProtonDriveSyncFailed\",
                \"severity\": \"critical\",
                \"job\": \"${TAG}\"
            },
            \"annotations\": {
                \"summary\": \"ProtonDrive sync failed (${TAG})\",
                \"description\": \"${escaped}\"
            },
            \"endsAt\": \"${ends_at}\"
        }]" || log "WARNING: Failed to reach Alertmanager at ${ALERTMANAGER_URL}"
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
if ! rsync_out=$(rsync --archive --no-owner --no-group --delete "$SOURCE_DIR/" "$DEST_DIR/" 2>&1); then
    FAILURE_REASON="rsync failed: ${rsync_out:-no output}"
    exit 1
fi

log "Sync complete"
