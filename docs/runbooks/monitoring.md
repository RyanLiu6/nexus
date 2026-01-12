# Monitoring Runbook

## Overview

Nexus uses Prometheus + Grafana + Alertmanager for monitoring, with Discord for alerts.

```
Services → Prometheus (scrape) → Grafana (visualize)
                ↓
         Alert Rules → Alertmanager → Discord Bot → Discord Channel
```

---

## Discord Alerting Setup

### 1. Create Discord Webhook

1. Open Discord server settings
2. Integrations → Webhooks → New Webhook
3. Name it "Nexus Alerts", select channel
4. Copy webhook URL

### 2. Configure vault.yml

```yaml
discord_webhook_url: "https://discord.com/api/webhooks/..."
```

### 3. Configure Alertmanager

Edit `services/monitoring/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  receiver: 'discord'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: 'discord'
    webhook_configs:
      - url: 'http://host.docker.internal:8080/webhook'
        send_resolved: true
```

### 4. Run Alert Bot

```bash
# Start the bot
uv run nexus-alert-bot --port 8080

# Or via invoke
invoke alert-bot
```

### 5. Test Alert

```bash
# Stop a service to trigger alert
docker stop traefik

# Wait 5 minutes, check Discord
# Then restore
docker start traefik
```

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
