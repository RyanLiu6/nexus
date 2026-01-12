# Monitoring Runbook

## Overview

Nexus uses Prometheus + Grafana + Alertmanager for monitoring, with Discord for alerts.

```
Services → Prometheus (scrape) → Grafana (visualize)
                ↓
         Alert Rules → Alertmanager → Discord Bot → Discord Channel
```

**Supported Alert Integrations:**
- ✅ **Discord** - Fully implemented (see below)
- ❌ **Slack** - Not currently supported

---

## Discord Alerting Setup

### Prerequisites

- A Discord server where you have "Manage Webhooks" permission
- Nexus monitoring stack deployed (Prometheus, Alertmanager, Grafana)

### Step-by-Step Setup

#### 1. Create Discord Webhook

1. Open your Discord server
2. Navigate to **Server Settings** → **Integrations**
3. Click **Webhooks** → **New Webhook**
4. Configure the webhook:
   - **Name**: "Nexus Alerts" (or any name you prefer)
   - **Channel**: Select the channel where alerts should be posted (e.g., #alerts, #monitoring)
   - **Icon**: Optional - you can customize the webhook's avatar
5. Click **Copy Webhook URL** - save this for the next step

**Example Webhook URL format:**
```
https://discord.com/api/webhooks/1234567890/AbCdEfGhIjKlMnOpQrStUvWxYz
```

#### 2. Configure vault.yml

Add the webhook URL to your encrypted vault:

```bash
# Edit vault (will prompt for password)
ansible-vault edit ansible/vars/vault.yml
```

Add or update these lines:
```yaml
# Discord webhook for monitoring alerts
discord_webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"

# Optional: Discord channel ID (for advanced features)
discord_channel_id: "1234567890"

# Alert provider setting
alert_provider: "discord"
```

Save and exit.

#### 3. Set Environment Variable

The Discord bot reads the webhook URL from an environment variable:

```bash
# Option 1: Set in your shell profile (~/.zshrc or ~/.bashrc)
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Option 2: Set temporarily for testing
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..." uv run nexus-alert-bot
```

**For persistent setup**, add to your shell profile:
```bash
echo 'export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."' >> ~/.zshrc
source ~/.zshrc
```

#### 4. Configure Alertmanager

Alertmanager is already configured to forward alerts to the Discord bot webhook.

Verify the configuration in `services/monitoring/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  receiver: 'discord'
  group_by: ['alertname', 'severity']
  group_wait: 30s       # Wait 30s before sending first alert
  group_interval: 5m    # Wait 5m before sending grouped alerts
  repeat_interval: 4h   # Resend unresolved alerts every 4h

receivers:
  - name: 'discord'
    webhook_configs:
      - url: 'http://host.docker.internal:8080/webhook'
        send_resolved: true  # Send notifications when alerts resolve
```

**Note**: The URL `http://host.docker.internal:8080` points to your local machine where the Discord bot runs.

#### 5. Run Alert Bot

The Discord bot acts as a bridge between Alertmanager and Discord.

**Start the bot:**

```bash
# Option 1: Using uv directly
uv run nexus-alert-bot --port 8080

# Option 2: Using invoke task
invoke alert-bot

# Option 3: Run in background
nohup uv run nexus-alert-bot --port 8080 > /tmp/alert-bot.log 2>&1 &
```

**Verify the bot is running:**
```bash
# Check if the webhook server is listening
curl http://localhost:8080/webhook

# Expected output: "Bad Request" (400) - this is normal, it expects POST with JSON
```

**Bot logs are written to:**
- Console output
- `/tmp/nexus-alerts.log` (all alerts logged here)

#### 6. Test the Setup

##### Test 1: Manual Webhook Test
```bash
# Send a test alert directly to the bot
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "status": "firing",
    "alertname": "TestAlert",
    "labels": {"severity": "warning"},
    "annotations": {"description": "This is a test alert"},
    "commonLabels": {"instance": "localhost"}
  }'
```

You should see a test alert appear in your Discord channel.

##### Test 2: Trigger a Real Alert
```bash
# Stop a monitored service (Traefik is a good test)
docker stop traefik

# Wait 5 minutes for alert to fire
# Check your Discord channel for the alert

# Restore the service
docker start traefik

# Wait a few moments for the "RESOLVED" notification
```

**Example Alert Message in Discord:**
```
🚨 FIRING: traefik is down
Instance: traefik
Severity: critical
Description: traefik has been down for > 5 minutes
```

**Example Resolved Message:**
```
✅ RESOLVED: traefik is down
Instance: traefik
Duration: 7 minutes
```

### Troubleshooting Discord Alerts

#### Bot not receiving alerts

1. **Check bot is running:**
   ```bash
   ps aux | grep nexus-alert-bot
   curl http://localhost:8080/webhook
   ```

2. **Check Alertmanager can reach bot:**
   ```bash
   docker logs alertmanager --tail=50
   ```
   Look for errors like "connection refused"

3. **Verify webhook URL in Alertmanager config:**
   ```bash
   cat services/monitoring/alertmanager.yml | grep url
   ```

#### Discord webhook errors

1. **Test webhook directly:**
   ```bash
   curl -X POST "YOUR_DISCORD_WEBHOOK_URL" \
     -H "Content-Type: application/json" \
     -d '{"content": "Test message"}'
   ```

2. **Common errors:**
   - **401 Unauthorized**: Webhook URL is invalid or expired. Regenerate in Discord.
   - **404 Not Found**: Webhook was deleted. Create a new one.
   - **Rate Limited**: Too many messages. Discord has rate limits (30 messages per minute).

#### No alerts firing

1. **Check Prometheus targets:**
   - Visit http://localhost:9090/targets
   - Verify services are being scraped (should show "UP")

2. **Check alert rules:**
   - Visit http://localhost:9090/alerts
   - Verify rules are loaded and firing

3. **Check Alertmanager:**
   - Visit http://localhost:9093
   - Check if alerts are being received

### Advanced Configuration

#### Running Bot as a Service (systemd)

For persistent bot operation, create a systemd service:

```bash
# Create service file
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
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable nexus-alert-bot
sudo systemctl start nexus-alert-bot

# Check status
sudo systemctl status nexus-alert-bot
```

#### Custom Alert Routing

You can route different alerts to different Discord channels:

```yaml
# In alertmanager.yml
route:
  receiver: 'discord-default'
  routes:
    - match:
        severity: critical
      receiver: 'discord-critical'
    - match:
        alertname: BackupFailed
      receiver: 'discord-backups'

receivers:
  - name: 'discord-default'
    webhook_configs:
      - url: 'http://host.docker.internal:8080/webhook'
  - name: 'discord-critical'
    webhook_configs:
      - url: 'http://host.docker.internal:8081/webhook'  # Different bot instance
```

This requires running multiple bot instances on different ports, each configured with different webhook URLs.

---

## Alert Examples

**Service Down:**
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

## Prometheus Not Scraping

### Symptoms
- No data in Grafana dashboards
- Prometheus targets showing "down"

### Troubleshooting

1. **Check Prometheus status**
   ```bash
   docker ps | grep prometheus
   docker compose logs prometheus --tail=50
   ```

2. **Review targets**
   - Visit `http://localhost:9090/targets`
   - Check which targets are up/down

3. **Check network**
   ```bash
   docker network inspect proxy
   ```
   Verify Prometheus is on same network as services.

4. **Test metrics endpoint**
   ```bash
   docker compose exec prometheus wget -qO- http://service:port/metrics
   ```

---

## Grafana Dashboard Issues

### Symptoms
- Panels show "No data"
- Cannot log in

### Troubleshooting

1. **Check Grafana status**
   ```bash
   docker compose logs grafana --tail=50
   ```

2. **Verify Prometheus datasource**
   - Grafana → Configuration → Data Sources
   - Check URL is `http://prometheus:9090`
   - Click "Test"

3. **Reset admin password**
   ```bash
   docker compose exec grafana grafana-cli admin reset-admin-password <new-password>
   ```

---

## Alerts Not Firing

### Symptoms
- Alerts configured but no notifications
- Alertmanager not receiving alerts

### Troubleshooting

1. **Check Alertmanager**
   ```bash
   docker ps | grep alertmanager
   docker compose logs alertmanager --tail=50
   ```

2. **Check alert rules**
   - Visit `http://localhost:9090/rules`
   - Verify rules are loaded

3. **Check webhook**
   ```bash
   # Test webhook directly
   curl -X POST http://localhost:8080/webhook \
     -H "Content-Type: application/json" \
     -d '{"alerts":[{"status":"firing","labels":{"alertname":"test"}}]}'
   ```

4. **Check bot logs**
   - Look for errors in alert bot output
   - Verify Discord webhook URL is correct

---

## High Resource Usage

### Memory

```bash
# Check container stats
docker stats prometheus grafana alertmanager

# Reduce Prometheus retention
# Edit prometheus.yml:
# storage.tsdb.retention.time: 7d  (default is 15d)
```

### Disk

```bash
# Check Prometheus data size
du -sh services/monitoring/data/prometheus

# Clean old data
docker compose exec prometheus rm -rf /prometheus/data/*
docker compose restart prometheus
```

---

## Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| No metrics | Exporter not running | Check service is up |
| Wrong data | Timezone mismatch | Check Grafana timezone |
| Slow dashboards | Too many queries | Use recording rules |
| Alerts not sending | Webhook blocked | Check URL, firewall |
| Container restarts | OOM killed | Increase memory limit |
| Discord 401 | Invalid webhook | Regenerate webhook URL |

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

---

## Adding New Alerts

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
