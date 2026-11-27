#!/usr/bin/env bash
# Rotate /opt/homebrew/var/log/scrypted.log when >= 10 MB (copytruncate, keep 3 gzipped)
set -euo pipefail

LOG="/opt/homebrew/var/log/scrypted.log"
MAX_BYTES=$((10 * 1024 * 1024))
KEEP=3

[[ -f "$LOG" ]] || exit 0
size=$(stat -f%z "$LOG")
if (( size < MAX_BYTES )); then
    exit 0
fi

for (( i = KEEP; i >= 2; i-- )); do
    prev=$((i - 1))
    [[ -f "${LOG}.${prev}.gz" ]] && mv -f "${LOG}.${prev}.gz" "${LOG}.${i}.gz"
done

cp "$LOG" "${LOG}.1"
: > "$LOG"
gzip -f "${LOG}.1"
