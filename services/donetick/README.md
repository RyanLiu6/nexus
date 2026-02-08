# Donetick

Donetick is a collaborative task and chore management app with support for recurring schedules, subtasks, assignees, and gamification.

## Features

- **Task Management** - Create tasks with subtasks, due dates, and priorities
- **Recurring Chores** - Flexible schedules (daily, weekly, custom)
- ** Collaboration** - Assign tasks to family members
- **Gamification** - Earn points for completing tasks
- **Mobile Apps** - Native iOS and Android apps

## Setup

### 1. Generate JWT Secret

```bash
openssl rand -base64 32
```

### 2. Configure Vault Variables

Edit the Ansible vault file:

```bash
ansible-vault edit ansible/vars/vault.yml
```

Add the JWT secret:

```yaml
# Donetick
donetick_jwt_secret: "<secret-from-above>"
```

### 3. Deploy

```bash
nexus deploy donetick
# or
nexus deploy home
```

### Access

- **URL:** `https://donetick.${NEXUS_DOMAIN}`
- **Auth:** Tailscale + tailscale-access

## Data Storage

Donetick stores data in the `${NEXUS_DATA_DIRECTORY}/Config/donetick` directory:

| Path | Contents |
|------|----------|
| `data/donetick.db` | SQLite database |
| `data/` | App configuration and state |

## Backups

Ensure the data directory is included in your backup strategy.

```bash
# Manual backup
cp ${NEXUS_DATA_DIRECTORY}/Config/donetick/data/donetick.db ${NEXUS_DATA_DIRECTORY}/Backups/donetick.db.bak
```

## Configuration

- **User Creation**: Enabled by default. After creating your account(s), set `is_user_creation_disabled: true` in `config/selfhosted.yaml` and restart the container.
- **JWT Session**: Tokens valid for 7 days (168h), refreshable up to 60 days (1440h).
- **Rate Limiting**: 300 requests per 60 seconds.
- **Real-time Updates**: SSE-based real-time sync enabled by default.

### Mobile Apps

The official Donetick apps (Android APK from GitHub releases, iOS from App Store) support self-hosted servers. On first launch, enter your server URL (`https://donetick.example.com`) in the app settings. HTTPS is required — self-signed certificates won't work.

Tailscale must be active on your phone to reach the server.

## Troubleshooting

### Mobile App Connection Failed

**Symptoms:** App cannot connect to server

**Solutions:**
1. Ensure phone is connected to Tailscale
2. Verify URL is `https://` (not http)
3. Check if certificate is valid (LetsEncrypt via Traefik)

## Resources

- [GitHub Repository](https://github.com/donetick/donetick)
- [Official Website](https://donetick.com)
