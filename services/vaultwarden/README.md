# Vaultwarden

Vaultwarden is a lightweight, self-hosted implementation of the Bitwarden password manager. It's fully compatible with Bitwarden clients (browser extensions, mobile apps, desktop apps).

## Features

- **Password Management** - Store logins, credit cards, identities, and secure notes
- **Cross-Platform Access** - Web vault, extensions, mobile apps, and desktop apps
- **Organization Support** - Share items with family or team members
- **Two-Factor Authentication** - TOTP, Duo, YubiKey (FIDO2)
- **Send** - Securely share files and text
- **Lightweight** - Written in Rust, optimized for self-hosting

## Setup

### 1. Generate Admin Token

Generate a random password and hash it with Argon2:

```bash
# Step 1: Generate a random password (save this!)
openssl rand -base64 24

# Step 2: Hash it with Argon2
docker run --rm -it vaultwarden/server /vaultwarden hash
```

Enter the password from Step 1 when prompted.

**Important**: Save both values:
- **Plaintext password**: Store in password manager - you'll use this to log into the admin panel
- **Argon2 hash**: Add to `ansible/vars/vault.yml` as `vaultwarden_admin_token`

### 2. Configure Vault Variables

Edit the Ansible vault file:

```bash
ansible-vault edit ansible/vars/vault.yml
```

Add the admin token:

```yaml
# Vaultwarden
vaultwarden_admin_token: "<argon2-hash-from-above>"
vaultwarden_signups_allowed: "false"
vaultwarden_invitations_allowed: "true"
```

### 3. Deploy

```bash
nexus deploy vaultwarden
# or
nexus deploy core
```

## Access

- **URL:** `https://vault.${NEXUS_DOMAIN}` (via Tailscale)
- **Admin Panel:** `https://vault.${NEXUS_DOMAIN}/admin`
- **Auth:** Tailscale for network access + Bitwarden account

## Data Storage

Vaultwarden stores data in the `${NEXUS_DATA_DIRECTORY}/Config/vaultwarden` directory:

| Path | Contents |
|------|----------|
| `db.sqlite3` | Main database |
| `attachments/` | File attachments |
| `icon_cache/` | Website icons |
| `sends/` | Bitwarden Send files |
| `config.json` | Runtime configuration |

## Backups

Ensure the entire data directory is included in your backup strategy.

```bash
# Manual backup (stops container to ensure DB integrity)
docker stop vaultwarden
cp -r ${NEXUS_DATA_DIRECTORY}/Config/vaultwarden ${NEXUS_DATA_DIRECTORY}/Backups/vaultwarden-$(date +%F)
docker start vaultwarden
```

## Configuration

- **Signups**: Disabled by default for security. Use invitations instead.
- **Invitations**: Enabled by default. Admins can invite users via the admin panel.
- **WebSocket**: Enabled for real-time sync across devices.

### Security Requirements

All accounts **MUST enable 2FA**. Recommended methods:
1. **FIDO2/WebAuthn** (YubiKey) - Most secure
2. **TOTP** (Authenticator apps) - Strongly recommended

**Do not rely solely on master passwords.**

### Admin Panel

Access at `/admin` using the plaintext admin token.
- Manage users and organizations
- View diagnostics
- Configure global settings

## Troubleshooting

### Clients Can't Connect

**Symptoms:** "Connection failure" or sync errors

**Solutions:**
1. Verify SSL certificate is valid (required for crypto operations)
2. Check Websocket connection for live sync
3. Ensure client URL is `https://`

### Admin Panel Locked

**Symptoms:** "Invalid token"

**Solutions:**
1. Verify `vaultwarden_admin_token` in `vault.yml` is the Argon2 hash, not plaintext
2. Check logs: `docker logs vaultwarden`

## Resources

- [GitHub Repository](https://github.com/dani-garcia/vaultwarden)
- [Official Documentation](https://github.com/dani-garcia/vaultwarden/wiki)
- [Bitwarden Help](https://bitwarden.com/help/)
