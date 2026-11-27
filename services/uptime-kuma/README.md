# Uptime Kuma

Self-hosted HTTP/HTTPS, TLS certificate, and Docker container uptime monitoring exposed at `https://uptime.<domain>`.

## Architecture

- **uptime-kuma** (`louislam/uptime-kuma:2`): Runs behind Traefik (`internal-chain@file`, Tailscale-only), with SQLite data persisted in `${NEXUS_DATA_DIRECTORY}/Config/uptime-kuma` and `/var/run/docker.sock:ro` mounted for container monitoring.
- Uses `host.docker.internal:9210/health` to monitor HAVM (Home Assistant OS VM).

## Secrets (`config/secrets.enc.yml`)

- `uptime_kuma_admin_user` / `uptime_kuma_admin_password`: Admin login credentials.
- `discord_webhook_url`: Synced automatically on deploy via `scripts/sync-monitoring-webhooks.py`.
