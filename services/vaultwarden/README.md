# Vaultwarden

Vaultwarden is a lightweight, self-hosted implementation of the Bitwarden password manager. It's fully compatible with Bitwarden clients (browser extensions, mobile apps, desktop apps).

## Access

- URL: `https://vault.example.com` (via Tailscale)
- Admin Panel: `https://vault.example.com/admin`

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

## Configuration

- **Signups**: Disabled by default for security. Use invitations instead.
- **Invitations**: Enabled by default. Admins can invite users via the admin panel.
- **Admin Token**: Required to access the admin panel at `/admin`.
- **WebSocket**: Enabled for real-time sync across devices.

## Security Requirements

### Two-Factor Authentication (2FA) - MANDATORY

All accounts MUST enable 2FA. Recommended methods in order of preference:

1. **FIDO2/WebAuthn** (Hardware keys like YubiKey) - Most secure
2. **TOTP** (Authenticator apps like Authy, 1Password) - Strongly recommended
3. **Duo** (If already part of your security infrastructure)

**Do not rely solely on master passwords.** Even with a strong master password, 2FA is required for defense in depth.

### Admin Panel Security

The admin token must be strong since it provides full control over the instance. The setup instructions above use `openssl rand -base64 24` which generates a 24-byte random password (~32 characters).

### Defense in Depth

Vaultwarden security operates in multiple layers:

| Layer | Protection | Purpose |
|-------|-----------|---------|
| **Network** | Tailscale-only access | Prevents unauthorized network access |
| **Container** | `no-new-privileges` | Prevents privilege escalation |
| **Application** | Rate limiting | Mitigates brute-force attacks |
| **Application** | Password hints disabled | Prevents information leakage |
| **Authentication** | Master password + 2FA | Multi-factor user authentication |
| **Data** | AES-256 encryption | Protects data at rest |

Each layer provides independent protection. Compromise of one layer doesn't compromise the entire system.

## Admin Panel

Access the admin panel at `https://vault.example.com/admin` using the admin token password (not the Argon2 hash).

From the admin panel you can:
- View registered users
- Delete users
- Invite new users
- Disable user accounts
- View diagnostics and logs

## Backup

Vaultwarden data is stored in `${NEXUS_DATA_DIRECTORY}/Config/vaultwarden`. This includes:
- SQLite database (`db.sqlite3`)
- User attachments
- Icons cache
- Configuration

Ensure this directory is included in your backup strategy.
