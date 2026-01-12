# Monitoring Runbook

## Prometheus Not Scraping

### Symptoms
- No data in Grafana dashboards
- Prometheus targets showing "down"
- Metrics not appearing in queries

### Troubleshooting Steps

1. **Check Prometheus status**
   ```bash
   docker ps | grep prometheus
   docker compose logs prometheus --tail=50
   ```

2. **Review Prometheus targets**
   - Visit `http://localhost:9090/targets`
   - Check which targets are up/down
   - Note error messages

3. **Verify service exporter labels**
   - Check `services/<service>/docker-compose.yml`
   - Look for metrics labels (e.g., `prometheus.io/scrape`)
   - Ensure labels are correctly formatted

4. **Check network connectivity**
   ```bash
   docker network inspect proxy
   ```
   - Verify Prometheus is on the same network as services

5. **Test metrics endpoint**
   ```bash
   curl http://service:metrics-port/metrics
   ```

### Common Configuration Issues

| Issue | Cause | Solution |
|-------|--------|----------|
| Target unreachable | Network isolation | Add service to proxy network |
| Invalid metrics | Wrong port | Verify metrics port in labels |
| No labels | Misconfigured scrape config | Check prometheus.yml configuration |

## Grafana Dashboard Issues

### Symptoms
- Dashboard panels show "No data"
- Cannot log in to Grafana
- Dashboards not loading

### Troubleshooting Steps

1. **Check Grafana status**
   ```bash
   docker ps | grep grafana
   docker compose logs grafana --tail=50
   ```

2. **Verify Prometheus datasource**
   - Log in to Grafana
   - Go to Configuration → Data Sources
   - Check Prometheus URL is correct (usually `http://prometheus:9090`)
   - Test connection

3. **Check dashboard configuration**
   - Review JSON or provisioning config
   - Verify panel queries are valid
   - Check time range settings

4. **Test query in Explore**
   - Go to Explore in Grafana
   - Run Prometheus query manually
   - Verify data is returned

### Grafana Login Issues

1. **Reset admin password**
   ```bash
   docker compose exec grafana grafana-cli admin reset-admin-password <new-password>
   ```

2. **Check environment variables**
   - Verify `GRAFANA_ADMIN_USER` in `.env`
   - Verify `GRAFANA_ADMIN_PASSWORD` in `.env`

## Alert Not Firing

### Symptoms
- Alerts configured but not triggering
- Alertmanager not receiving alerts
- No notifications sent

### Troubleshooting Steps

1. **Check Alertmanager status**
   ```bash
   docker ps | grep alertmanager
   docker compose logs alertmanager --tail=50
   ```

2. **Review alert rules**
   - Check Prometheus rules files
   - Verify rule syntax is correct
   - Check evaluation interval

3. **Test alert manually**
   - Use Prometheus UI to trigger alert
   - Check Alertmanager alerts page
   - Verify webhook is called

4. **Verify webhook configuration**
   - Check `services/monitoring/config/alertmanager.yml`
   - Verify webhook URL is correct
   - Test webhook with curl:
     ```bash
     curl -X POST <webhook-url> -d '{"test": "data"}'
     ```

## High Cardinality Queries

### Symptoms
- Grafana becomes slow
- Prometheus high memory usage
- Query timeouts

### Troubleshooting Steps

1. **Identify high-cardinality metrics**
   ```bash
   curl http://localhost:9090/api/v1/label/__name__/values | jq '.data[]' | head -20
   ```

2. **Review Prometheus configuration**
   - Check retention period in `prometheus.yml`
   - Check scrape intervals

3. **Optimize queries**
   - Use `rate()` instead of raw values
   - Reduce time range for queries
   - Use recording rules for complex queries

### Optimization Tips

- Add metric relabeling to drop unwanted labels
- Increase scrape interval for non-critical services
- Use aggregations in recording rules

## Resource Usage

### High Memory Usage

1. **Check container stats**
   ```bash
   docker stats prometheus grafana alertmanager
   ```

2. **Review memory configuration**
   - Check memory limits in docker-compose.yml
   - Consider increasing limits if needed
   - Review `storage.tsdb.retention.time` in prometheus.yml

### High Disk Usage

1. **Check Prometheus data size**
   ```bash
   du -sh services/monitoring/data/prometheus
   ```

2. **Review retention settings**
   ```yaml
   # In prometheus.yml
   storage:
     tsdb:
       retention.time: 15d  # Reduce from default 15d
   ```

3. **Clean old data**
   ```bash
   docker compose exec prometheus rm -rf /prometheus/data/*
   docker compose restart prometheus
   ```

## Common Issues

| Symptom | Cause | Solution |
|----------|--------|----------|
| No metrics | Exporter not running | Start exporter service |
| Wrong data | Time zone mismatch | Check Grafana timezone setting |
| Slow dashboards | Too many queries | Optimize with recording rules |
| Alerts not sending | Webhook blocked | Check Discord webhook URL |
| Container restarts | OOM killed | Increase memory limit |
