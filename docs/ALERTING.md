# Nexus Alerting Setup

This guide covers setting up alerting for your Nexus homelab using Grafana alerts and a Discord bot.

## Overview

Nexus uses the following alerting stack:
- **Prometheus**: Metrics collection
- **Grafana**: Alert rules and dashboard
- **Alertmanager**: Alert routing
- **Discord Bot**: Receives alerts and posts to Discord

## Architecture

```
Service (Down/High CPU) → Prometheus → Grafana Alert → Alertmanager → Discord Bot → Discord Channel
```

## Prerequisites

1. Discord account
2. Discord server (optional, can DM to your bot)
3. Nexus services deployed with monitoring enabled

## Step 1: Create Discord Bot

### 1.1 Go to Discord Developer Portal

Visit https://discord.com/developers/applications

### 1.2 Create New Application

1. Click "New Application"
2. Give it a name (e.g., "Nexus Alerts")
3. Click "Create"

### 1.3 Create Bot

1. Go to "Bot" tab in left sidebar
2. Click "Add Bot" → "Yes, do it!"
3. Set a username (e.g., "Nexus Alert Bot")
4. Copy the **Token** (save this!)

### 1.4 Enable Privileged Intents

Scroll down to "Privileged Gateway Intents" and enable:
- **Message Content Intent**
- **Server Members Intent**

Click "Save Changes"

### 1.5 Get Webhook URL (Option A - Webhook)

**For webhook-only bot:**

1. Go to your Discord server
2. Server Settings → Integrations → Webhooks
3. Click "New Webhook"
4. Name it "Nexus Alerts"
5. Copy the **Webhook URL**

### 1.6 Invite Bot to Server (Option B - Bot User)

**For full bot functionality:**

1. Go back to Developer Portal → Your Application
2. Go to "OAuth2" → "URL Generator"
3. Under "Scopes", select:
   - `bot`
4. Under "Bot Permissions", select:
   - `Send Messages`
   - `Embed Links`
   - `Attach Files`
5. Copy the generated URL and open in browser
6. Select your server and authorize

### 1.7 Get Channel ID

If using bot user (not webhook):

1. Enable Developer Mode in Discord (User Settings → Advanced)
2. Right-click the channel where alerts should go
3. Select "Copy ID"

## Step 2: Configure Alert Bot

### 2.1 Create Configuration File

Create `scripts/alert_bot_config.yml`:

```yaml
discord_token: "YOUR_BOT_TOKEN_HERE"
discord_channel_id: "YOUR_CHANNEL_ID_HERE"
discord_webhook_url: "YOUR_WEBHOOK_URL_HERE"
alert_provider: discord
log_level: INFO
```

**Important:**
- Use **webhook_url** if you created a webhook (simpler)
- Use **token + channel_id** if you invited the bot (more features)

### 2.2 Configure Environment Variables (Alternative)

Or set environment variables:

```bash
export DISCORD_BOT_TOKEN="your-bot-token"
export DISCORD_CHANNEL_ID="your-channel-id"
export DISCORD_WEBHOOK_URL="your-webhook-url"
export ALERT_PROVIDER="discord"
```

## Step 3: Configure Alertmanager

Create or update `services/monitoring/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  receiver: 'discord-notifications'
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
  - name: 'discord-notifications'
    webhook_configs:
      - url: 'http://localhost:8080/webhook'
        send_resolved: true
```

## Step 4: Configure Grafana Alerts

### 4.1 Add Alert Rules

Go to Grafana → Alerting → New Alert Rule

Example: Service Down Alert

1. **Name**: `{{ $labels.instance }} is down`
2. **Query**:
   ```promql
   up{job="docker"} == 0
   ```
3. **Conditions**: When query B is above 0
4. **Evaluation Every**: 1m
5. **For**: 5m
6. **Annotation**:
   ```
   description: "{{ $labels.instance }} has been down for more than 5 minutes."
   ```
7. **Labels**:
   - severity: critical
   - team: ops

### 4.2 Add Notification Policy

Grafana → Alerting → Contact Points → Add contact point

1. **Name**: Discord
2. **Type**: Webhook
3. **URL**: `http://localhost:8080/webhook`
4. **HTTP Method**: POST

### 4.3 Set Up Notification Policy

Grafana → Alerting → Notification Policies

1. Click "New specific policy"
2. **Label matcher**: `severity = critical`
3. **Contact point**: Discord
4. **Override routing**: ✓ (checked)
5. **Group by**: `alertname`
6. **Wait**: 30s
7. **Repeat interval**: 4h

## Step 5: Deploy Alerting

```bash
# Deploy with alerting enabled
./scripts/deploy.py -p home --enable-alerting
```

Or manually start the bot:

```bash
# Install dependencies
uv pip install discord.py aiohttp pyyaml click

# Run the bot
python3 scripts/alert_bot.py --port 8080
```

## Step 6: Test Alert

### 6.1 Stop a Container

```bash
docker stop traefik
```

### 6.2 Wait for Alert

Within 5-10 minutes, you should see an alert in Discord.

### 6.3 Restore Service

```bash
docker start traefik
```

You should receive a "resolved" alert.

## Alert Examples

### Service Down
```
🚨 Firing: traefik is down
Description: traefik container has been down for > 5 minutes

Labels:
  instance: traefik
  severity: critical

View in Grafana: https://grafana.yourdomain.com
```

### High CPU Usage
```
⚠️ Firing: High CPU usage
Description: CPU usage on nexus-server is > 80% for > 15 minutes

Labels:
  instance: nexus-server
  severity: warning
```

### Disk Space Low
```
📉 Firing: Low disk space
Description: Disk usage is > 90%

Labels:
  instance: nexus-server
  severity: warning
```

## Troubleshooting

### Bot Not Starting

**Problem**: `discord.py` import error

**Solution**:
```bash
uv pip install discord.py aiohttp pyyaml click
```

**Problem**: Invalid token

**Solution**: Ensure you copied the **Token** from the Bot tab, not the Client Secret.

### Alerts Not Reaching Discord

**Problem**: No alerts in Discord

**Solutions**:
1. Check Alertmanager is running: `docker ps | grep alertmanager`
2. Check alertmanager logs: `docker logs alertmanager`
3. Verify webhook URL: Test it with curl
4. Check Discord bot logs for errors

### Too Many Alerts

**Problem**: Getting spammed with alerts

**Solution**:
1. Adjust `repeat_interval` in Alertmanager config
2. Adjust evaluation timing in Grafana
3. Add alert grouping rules

### Bot Not Receiving Webhooks

**Problem**: Alertmanager can't reach bot

**Solution**:
1. Ensure bot is running on port 8080
2. Check firewall settings
3. Verify `alertmanager.yml` webhook URL is correct

## Advanced Configuration

### Multiple Alert Channels

To send alerts to multiple Discord channels:

1. Create multiple Discord bots/webhooks
2. Update Alertmanager config:
   ```yaml
   route:
     receiver: 'critical-alerts'

     routes:
       - match:
           severity: critical
         receiver: 'critical-alerts'

       - match:
           severity: warning
         receiver: 'warning-alerts'

   receivers:
     - name: 'critical-alerts'
       webhook_configs:
         - url: 'http://localhost:8080/critical'

     - name: 'warning-alerts'
       webhook_configs:
         - url: 'http://localhost:8080/warning'
   ```

### Slack Integration

To use Slack instead of Discord:

1. Create Slack incoming webhook
2. Update `alert_provider: slack` in config
3. Update Alertmanager webhook URL to Slack webhook
4. Modify bot to handle Slack payloads

## Security Best Practices

1. **Never commit bot tokens** to git
2. Use environment variables or ansible-vault for secrets
3. Limit bot permissions (only what's needed)
4. Use webhook-based auth if possible (simpler than bot user)
5. Rotate tokens regularly
6. Monitor for unauthorized bot usage

## Resources

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/)

## Support

If you encounter issues:

1. Check logs: `docker logs alertmanager`
2. Check bot logs (if running manually)
3. Verify configuration files syntax
4. Test alerts manually using Grafana's "Test Rule" feature
