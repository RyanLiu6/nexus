# Home Assistant (HAVM)

Home Assistant OS running on Apple Silicon via [HAVM](https://github.com/IngmarStein/havm) (native Apple Virtualization framework).

## Architecture

- **Runtime:** Native macOS Virtualization framework (`VZVirtualMachine`) managed via HAVM.
- **Service Management:** LaunchAgent `com.nexus.havm` (`services/homeassistant/com.nexus.havm.plist` symlinked to `~/Library/LaunchAgents/com.nexus.havm.plist`).
- **VM Storage:** Stored in `${NEXUS_DATA_DIRECTORY}/Config/homeassistant/vm/haos.img` (excluded from Backrest).
- **Config:** `${NEXUS_DATA_DIRECTORY}/Config/homeassistant/config.yml`.
- **Reverse Proxy:** Traefik dynamic file rules in `services/traefik/rules/homeassistant.yml` (`Host(`homeassistant.{{ env `NEXUS_DOMAIN` }}`)`).
- **Monitoring:** Prometheus scrapes `host.docker.internal:9210`, visualized in Grafana (`services/monitoring/grafana/dashboards/havm.json`).
- **Backup Sync:** Periodic SCP sync (`services/homeassistant/sync-backups.sh`) via LaunchAgent `com.nexus.havm-backup-sync` pulls `.tar` backups to `${NEXUS_DATA_DIRECTORY}/Config/homeassistant/backups/`, which Backrest includes in daily snapshots.

## Service Management

### HAVM Virtual Machine

```bash
# Link and activate VM service
ln -sf ~/dev/nexus/services/homeassistant/com.nexus.havm.plist ~/Library/LaunchAgents/
launchctl load -w ~/Library/LaunchAgents/com.nexus.havm.plist

# Stop VM service
launchctl unload -w ~/Library/LaunchAgents/com.nexus.havm.plist

# View VM logs
tail -f /opt/homebrew/var/log/havm.log
```

### Automated Backup Sync

```bash
# Link and activate backup sync LaunchAgent (runs every 6 hours)
ln -sf ~/dev/nexus/services/homeassistant/com.nexus.havm-backup-sync.plist ~/Library/LaunchAgents/
launchctl load -w ~/Library/LaunchAgents/com.nexus.havm-backup-sync.plist

# Manually trigger a backup sync
./sync-backups.sh

# View backup sync logs
tail -f /opt/homebrew/var/log/havm-backup-sync.log
```

## Backup & Recovery

1. **HAOS Native Backups:** Home Assistant creates automated application-consistent `.tar` backups (managed via **Settings > System > Backups**).
2. **Local Sync:** `sync-backups.sh` pulls new `.tar` files from `/mnt/data/supervisor/backup/` on the VM to `/Volumes/Data/Config/homeassistant/backups/` and retains the newest 5 archives.
3. **Offsite & Local Protection:** Backrest includes `/base_data/homeassistant/backups/` in both `daily-local` and `daily-r2` plans, while explicitly excluding the 32GB raw VM image (`/base_data/homeassistant/vm`).
