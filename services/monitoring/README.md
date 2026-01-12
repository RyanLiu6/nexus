# Monitoring Stack

Nexus uses Prometheus + Grafana + Alertmanager for monitoring, with Discord for alerts.

```
Services → Prometheus (scrape) → Grafana (visualize)
                ↓
         Alert Rules → Alertmanager → Discord Bot → Discord Channel
```

## Components

| Component | Purpose | Port |
|-----------|---------|------|
| Prometheus | Metrics collection and storage | 9090 |
| Grafana | Dashboards and visualization | 3000 |
| Alertmanager | Alert routing and deduplication | 9093 |
| Node Exporter | System metrics | 9100 |

## Setup

1. Create `.env` from sample.
2. Run: `docker compose up -d`
3. Access Grafana at `https://grafana.yourdomain.com`
4. (Optional) Set up Discord alerts - see below

---

## Discord Alerting Setup

### Prerequisites

- A Discord server where you have "Manage Webhooks" permission
- Nexus monitoring stack deployed

### Step-by-Step Setup

#### 1. Create Discord Webhook

1. Open your Discord server
2. Navigate to **Server Settings** → **Integrations**
3. Click **Webhooks** → **New Webhook**
4. Configure:
   - **Name**: "Nexus Alerts"
   - **Channel**: Select your alerts channel
5. Click **Copy Webhook URL**

#### 2. Configure vault.yml

```bash
ansible-vault edit ansible/vars/vault.yml
```

Add:
```yaml
discord_webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
discord_channel_id: "1234567890"  # Optional
alert_provider: "discord"
```

#### 3. Set Environment Variable

```bash
# Add to ~/.zshrc or ~/.bashrc
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
source ~/.zshrc
```

#### 4. Run Alert Bot

```bash
# Using invoke
invoke alert-bot

# Or directly
uv run nexus-alert-bot --port 8080

# Run in background
nohup uv run nexus-alert-bot --port 8080 > /tmp/alert-bot.log 2>&1 &
```

#### 5. Verify Alertmanager Config

Check `services/monitoring/alertmanager.yml`:

```yaml
route:
  receiver: 'discord'
receivers:
  - name: 'discord'
    webhook_configs:
      - url: 'http://host.docker.internal:8080/webhook'
        send_resolved: true
```

#### 6. Test the Setup

```bash
# Send test alert
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"status": "firing", "alertname": "TestAlert", "labels": {"severity": "warning"}}'
```

You should see a test alert in your Discord channel.

### Example Alerts

**Firing:**
```
🚨 FIRING: traefik is down
Instance: traefik
Severity: critical
Description: traefik has been down for > 5 minutes
```

**Resolved:**
```
✅ RESOLVED: traefik is down
Instance: traefik
Duration: 7 minutes
```

---

## Running Bot as a Service

### systemd (Linux)

```bash
sudo nano /etc/systemd/system/nexus-alert-bot.service
```

```ini
[Unit]
Description=Nexus Discord Alert Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/nexus
Environment="DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/..."
ExecStart=/usr/local/bin/uv run nexus-alert-bot --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable nexus-alert-bot
sudo systemctl start nexus-alert-bot
```

### launchd (macOS)

```bash
nano ~/Library/LaunchAgents/com.nexus.alert-bot.plist
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nexus.alert-bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/uv</string>
        <string>run</string>
        <string>nexus-alert-bot</string>
        <string>--port</string>
        <string>8080</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/dev/nexus</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>DISCORD_WEBHOOK_URL</key>
        <string>https://discord.com/api/webhooks/...</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.nexus.alert-bot.plist
```

---

## Troubleshooting

### Bot Not Receiving Alerts

1. **Check bot is running:**
   ```bash
   ps aux | grep nexus-alert-bot
   curl http://localhost:8080/webhook
   ```

2. **Check Alertmanager can reach bot:**
   ```bash
   docker logs alertmanager --tail=50
   ```

3. **Verify webhook URL** in `alertmanager.yml`

### Discord Webhook Errors

| Error | Solution |
|-------|----------|
| 401 Unauthorized | Webhook URL invalid - regenerate in Discord |
| 404 Not Found | Webhook was deleted - create new one |
| Rate Limited | Too many messages (30/min limit) |

### No Alerts Firing

1. **Check Prometheus targets:** http://localhost:9090/targets
2. **Check alert rules:** http://localhost:9090/alerts
3. **Check Alertmanager:** http://localhost:9093

### Grafana Issues

**No data in dashboards:**
1. Check Prometheus datasource: Grafana → Configuration → Data Sources
2. Verify URL is `http://prometheus:9090`
3. Click "Test"

**Reset admin password:**
```bash
docker compose exec grafana grafana-cli admin reset-admin-password <new-password>
```

---

## Adding Custom Alerts

Edit `services/monitoring/alerts.yml`:

```yaml
groups:
  - name: nexus
    rules:
      - alert: ServiceDown
        expr: up{job="docker"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "{{ $labels.instance }} is down"

      - alert: HighCPU
        expr: rate(container_cpu_usage_seconds_total[5m]) > 0.8
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.name }}"

      - alert: LowDisk
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Disk usage > 90%"
```

After editing, restart Prometheus:
```bash
docker compose restart prometheus
```

---

## Useful Prometheus Queries

```promql
# Container up/down
up{job="docker"}

# Container CPU usage
rate(container_cpu_usage_seconds_total[5m])

# Container memory usage
container_memory_usage_bytes

# Disk usage
node_filesystem_avail_bytes{mountpoint="/"}

# Network traffic
rate(container_network_receive_bytes_total[5m])
```
