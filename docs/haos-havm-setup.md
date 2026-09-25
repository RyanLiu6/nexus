# Home Assistant OS (HAOS) with HAVM on Apple Silicon

Running Home Assistant OS alongside Nexus on Apple Silicon using [HAVM (Home Assistant VM Runner)](https://github.com/IngmarStein/havm).

---

## Overview

Nexus orchestrates containerized services with Docker Compose and Ansible. While core services run cleanly inside Docker, running a full smart home appliance—specifically **Home Assistant OS (HAOS)** with **Supervisor**, **Add-ons**, and **Matter-over-Thread**—faces networking limitations in containerized macOS Docker (due to Docker Desktop's VM network boundary blocking L2 multicast/mDNS and IPv6 Thread routing).

**HAVM** solves this by running HAOS directly on macOS using Apple's native **Virtualization framework** (`VZVirtualMachine`):
- **Zero-config headless CLI:** Auto-downloads, extracts, and provisions the official HAOS ARM64 image.
- **Background service:** Runs natively as a launchd background daemon via git-tracked LaunchAgent plists.
- **Bridged networking:** Directly bridges to `en0` with a stable MAC address, granting HAOS its own LAN IP with full mDNS and Matter/Thread support.
- **Prometheus metrics:** Native Prometheus endpoint on port 9210 for VM lifecycle, disk, and USB monitoring.
- **USB Passthrough (macOS 27+):** Dynamic accessory passthrough for Zigbee/Z-Wave/Thread coordinator dongles.

---

## Integration with Nexus Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        macOS Host (Apple Silicon)                      │
│                                                                        │
│   ┌────────────────────────────┐      ┌────────────────────────────┐   │
│   │ Docker Containers (Nexus)  │      │ HAVM (Native Virtualization)│   │
│   │                            │      │                            │   │
│   │  • Traefik (:80/:443)      │      │  • Home Assistant OS       │   │
│   │  • Prometheus (:9090) ───────Scrapes──> • havm Metrics (:9210)  │   │
│   │  • Grafana (:3000)         │      │  • Supervisor & Add-ons    │   │
│   │  • Homepage (:3000)        │      │                            │   │
│   │  • Backrest (:9898)        │      │                            │   │
│   └─────────────┼──────────────┘      └─────────────┼──────────────┘   │
│                 │                                   │                  │
│       Traefik reverse-proxies                 VirtIO Bridge            │
│       https://homeassistant.<domain>                │                  │
│                 │                                   │                  │
│   ┌─────────────▼───────────────────────────────────▼──────────────┐   │
│   │                 Physical Network Interface (en0)               │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
└────────────────────────────────────┼───────────────────────────────────┘
                                     ▼
                ┌────────────────────────────────────────┐
                │          Local Home LAN / Wi-Fi        │
                │  - Apple TV 4K / HomePod (Thread TBR)  │
                │  - Matter-over-Thread Smart Devices    │
                │  - mDNS / SSDP / HomeKit Multicast     │
                └────────────────────────────────────────┘
```

---

## Persistent Storage Layout

Like all Nexus containers whose state is stored in `${NEXUS_DATA_DIRECTORY}/Config/<service>`, HAVM's persistent virtio disk, configuration, and synced backups reside in `${NEXUS_DATA_DIRECTORY}/Config/homeassistant`:

```text
${NEXUS_DATA_DIRECTORY}/Config/homeassistant/
├── config.yml                   # HAVM VM configuration
├── backups/                     # Synced HAOS .tar backups (backed up by Backrest)
└── vm/                          # Excluded from Backrest backups (raw 32GB disk)
    ├── haos.img                 # Persistent raw disk image (VirtIO)
    ├── config.img               # Cloud-init FAT config disk (SSH keys, hostname)
    ├── NVRAM                    # EFI NVRAM variable store
    ├── MachineIdentifier        # Persisted hardware UUID
    └── havm.pid                 # Runtime PID
```

---

## Installation & Setup

### 1. Install HAVM via Homebrew

```bash
brew install ingmarstein/havm/havm
```

### 2. Configure HAVM

Create `${NEXUS_DATA_DIRECTORY}/Config/homeassistant/config.yml` (and track in `services/homeassistant/config.yml`):

```yaml
vm:
  cpu_count: 4
  memory_size: "4 GiB"
  disk_size: "32 GiB"

network:
  type: bridge
  interface: "en0"
  mac: "02:00:00:00:00:01"  # Fixed MAC for deterministic router DHCP reservations
  hostname: "homeassistant.local"

ssh:
  authorized_keys: "~/.ssh/ha_key.pub"  # Injected into HAOS for root debug SSH & backup sync on port 22222

metrics:
  enabled: true
  type: prometheus
  prometheus:
    port: 9210
    host: ["::"]  # Listen on all interfaces so Prometheus in Docker can scrape

logging:
  format: text
  level: info

shutdown:
  timeout_seconds: 90
```

### 3. Manage HAVM with Launchd

Nexus provides a git-tracked LaunchAgent in `services/homeassistant/com.nexus.havm.plist`:

```bash
# Link and activate the LaunchAgent
ln -sf ~/dev/nexus/services/homeassistant/com.nexus.havm.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.nexus.havm.plist
```

On first run, HAVM automatically downloads the latest stable HAOS `aarch64` release, decompresses the image into `${NEXUS_DATA_DIRECTORY}/Config/homeassistant/vm/haos.img`, and boots the VM.

---

## Backup Strategy

To prevent bloating your daily Backrest and Cloudflare R2 snapshots with a 32GB raw VM disk (`haos.img`), Nexus uses a dual-layer strategy:

1. **VM Disk Excluded from Backrest:**
   Backrest's plans (`daily-local` and `daily-r2`) explicitly exclude `/base_data/homeassistant/vm`.
2. **Automated Backup Sync (`sync-backups.sh`):**
   A script periodically pulls compact `.tar` backups from HAOS (`/mnt/data/supervisor/backup/`) over SSH port 22222 into `/Volumes/Data/Config/homeassistant/backups/`.
3. **Automated via LaunchAgent:**
   Managed by `services/homeassistant/com.nexus.havm-backup-sync.plist` running every 6 hours.

```bash
# Enable the backup sync LaunchAgent
ln -sf ~/dev/nexus/services/homeassistant/com.nexus.havm-backup-sync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.nexus.havm-backup-sync.plist
```

---

## Nexus Integrations

### 1. Traefik Reverse Proxy & SSL

Home Assistant is routed through Traefik using dynamic file configuration in `services/traefik/rules/homeassistant.yml`:

```yaml
http:
  routers:
    homeassistant:
      rule: "Host(`homeassistant.{{ env `NEXUS_DOMAIN` }}`)"
      entryPoints:
        - "https"
      middlewares:
        - "tailscale-chain@file"
      service: "homeassistant"
      tls:
        certResolver: "certchallenge"

    homeassistant-http:
      rule: "Host(`homeassistant.{{ env `NEXUS_DOMAIN` }}`)"
      entryPoints:
        - "http"
      middlewares:
        - "redirect-to-https@file"
      service: "homeassistant"

  services:
    homeassistant:
      loadBalancer:
        servers:
          - url: "http://192.168.50.161:80"
        passHostHeader: true
```

> [!NOTE]
> - HAOS with Supervisor serves the HTTP frontend on port `80` by default.
> - The router uses Go template backticks (`` `NEXUS_DOMAIN` ``) so the host domain dynamically expands at runtime without committing private domains to source control.

**Home Assistant Reverse Proxy Configuration:**
In modern Home Assistant (2026+), reverse proxy settings are managed under **Settings > System > Network > Reverse Proxies** (persisted in `.storage/http`). Ensure `use_x_forwarded_for: true` is enabled with trusted proxies:
- `192.168.0.0/16` (Host LAN)
- `172.16.0.0/12` (Docker networks)
- `100.64.0.0/10` (Tailscale VPN)
- `127.0.0.1`

### 2. Prometheus & Grafana Monitoring

1. **Prometheus Scrape Config:** Added to `services/monitoring/prometheus.yml`:
   ```yaml
   # HAVM (Home Assistant VM runner)
   - job_name: 'havm'
     static_configs:
       - targets: ['host.docker.internal:9210']
   ```
2. **Grafana Dashboard:** Automated provisioning via `services/monitoring/grafana/dashboards/havm.json` displaying:
   - VM State (running, stopped, starting)
   - Disk usage (logical vs APFS allocated)
   - USB accessories attached
   - Scrape health (`up`)

### 3. Nexus Homepage

Home Assistant is displayed under the **Core** services category on Homepage:
- Accessible directly via `https://homeassistant.<domain>` over Tailscale.
- Configured in `${NEXUS_DATA_DIRECTORY}/Config/homepage/services.yaml`:
  ```yaml
  - Core:
    - homeassistant:
        href: https://homeassistant.<domain>
        description: Home automation platform
        icon: si-homeassistant
  ```

---

## Useful Commands

| Task | Command |
|------|---------|
| Check HAVM service status | `launchctl list \| grep havm` |
| View HAVM VM logs | `tail -f /opt/homebrew/var/log/havm.log` |
| View Backup Sync logs | `tail -f /opt/homebrew/var/log/havm-backup-sync.log` |
| Manually trigger backup sync | `/Users/ryanliu6/dev/nexus/services/homeassistant/sync-backups.sh` |
| Check Prometheus metrics | `curl -s http://localhost:9210/metrics` |
| Check VM health | `curl -s http://localhost:9210/health` |
| Restart VM cleanly | `launchctl unload ~/Library/LaunchAgents/com.nexus.havm.plist && launchctl load ~/Library/LaunchAgents/com.nexus.havm.plist` |
| Clean cached image archives | `havm cleanup` |
