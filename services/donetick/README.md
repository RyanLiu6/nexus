# Donetick

Donetick is a collaborative task and chore management app with support for recurring schedules, subtasks, assignees, and gamification.

## Access

- URL: `https://donetick.example.com` (via Tailscale)

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

## Configuration

- **User Creation**: Enabled by default. After creating your account(s), set `is_user_creation_disabled: true` in `config/selfhosted.yaml` and restart the container.
- **JWT Session**: Tokens valid for 7 days (168h), refreshable up to 60 days (1440h).
- **Rate Limiting**: 300 requests per 60 seconds.
- **Real-time Updates**: SSE-based real-time sync enabled by default.

## Mobile Apps

The official Donetick apps (Android APK from GitHub releases, iOS from App Store) support self-hosted servers. On first launch, enter your server URL (`https://donetick.example.com`) in the app settings. HTTPS is required — self-signed certificates won't work.

Tailscale must be active on your phone to reach the server.

## Backup

Donetick data is stored in `${NEXUS_DATA_DIRECTORY}/Config/donetick/data`. This includes:
- SQLite database (`donetick.db`)

Ensure this directory is included in your backup strategy.
