# Monitoring Stack

Prometheus + Grafana + Alertmanager with Discord alerts.

```
Services → Prometheus (scrape) → Grafana (visualize)
                ↓
         Alert Rules → Alertmanager → Discord
```

## Components

| Component | Purpose | Port | Details |
|-----------|---------|------|---------|
| **Prometheus** | Metrics collection | 9090 | The "brain" of monitoring. It scrapes metrics from services at regular intervals and stores them in a time-series database. |
| **Grafana** | Dashboards | 3000 | The "face" of monitoring. Connects to Prometheus to visualize data in beautiful, customizable dashboards. |
| **Alertmanager** | Alert routing | 9093 | Receives alerts from Prometheus (e.g., "CPU > 90%"), groups them, silences them if needed, and routes them to receivers (like Discord). |
| **Node Exporter** | System metrics | 9100 | **Background Worker (No UI).** Runs on the host machine to expose hardware metrics (CPU, RAM, Disk I/O) for Prometheus to scrape. |
| **Alert Bot** | Discord Bridge | 8080 | **Background Worker.** A custom Python service that translates Alertmanager's raw JSON webhooks into formatted Discord messages. |

## Setup

1. Create `.env` from sample
2. Run: `docker compose up -d`
3. Access Grafana at `https://grafana.yourdomain.com`

---

## Grafana Dashboards

Dashboards in `grafana/dashboards/` are auto-loaded on startup.

**Add a dashboard:**
```bash
curl -o grafana/dashboards/my-dashboard.json \
  "https://grafana.com/api/dashboards/1860/revisions/latest/download"
docker restart grafana
```

**Popular IDs:** `1860` (Node Exporter), `893` (Docker), `17346` (Traefik 3)

---

## Alert Rules

Defined in `alerts.yml`, automatically loaded by Prometheus.

**Included alerts:**
- `HighCPUUsage` / `CriticalCPUUsage` - CPU > 80% / 95%
- `HighMemoryUsage` / `CriticalMemoryUsage` - Memory > 80% / 95%
- `DiskSpaceWarning` / `DiskSpaceCritical` - Disk < 20% / 10% free
- `ServiceDown` - Any monitored service unreachable
- `TraefikDown` - Reverse proxy down

**View status:** `https://prometheus.yourdomain.com/alerts`

---

## Discord Alerting

### 1. Create Discord Webhook

Server Settings → Integrations → Webhooks → New Webhook → Copy URL

### 2. Configure vault.yml

```yaml
discord_webhook_url: "https://discord.com/api/webhooks/..."
alert_provider: "discord"
```

### 3. Set Environment Variable

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

### 4. Run Alert Bot

```bash
invoke alert-bot

# Or run in background
nohup uv run nexus-alert-bot --port 8080 > /tmp/alert-bot.log 2>&1 &
```

### 5. Verify Alertmanager Config

Check `alertmanager.yml`:
```yaml
route:
  receiver: 'discord'
receivers:
  - name: 'discord'
    webhook_configs:
      - url: 'http://host.docker.internal:8080/webhook'
        send_resolved: true
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No alerts firing | Check targets: `http://localhost:9090/targets` |
| Bot not receiving | Check bot running: `curl http://localhost:8080/webhook` |
| No data in Grafana | Verify datasource URL: `http://prometheus:9090` |
| Webhook errors | Regenerate Discord webhook |

**Reset Grafana admin password:**
```bash
docker compose exec grafana grafana-cli admin reset-admin-password <new-password>
```

---

## Useful Queries

```promql
up{job="docker"}                              # Container status
rate(container_cpu_usage_seconds_total[5m])   # CPU usage
container_memory_usage_bytes                   # Memory usage
node_filesystem_avail_bytes{mountpoint="/"}   # Disk available
```
