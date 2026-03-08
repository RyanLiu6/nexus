# Proton Drive Sync

Off-site backup replication to ProtonDrive. Push-only - no restore capability from ProtonDrive.

## What it syncs

- `/data/paperless-documents` → Paperless documents (`${PAPERLESS_DOCUMENTS_DIRECTORY}`)
- `/data/backups` → Backrest local restic repos (`${NEXUS_DATA_DIRECTORY}/Backups`)

Both directories are mounted read-only.

## Setup

### 1. Configure vault.yml

```yaml
proton_drive_keyring_password: "your-generated-password"  # openssl rand -base64 32
```

### 2. Deploy the service

```bash
nexus deploy proton-drive-sync
```

### 3. Authenticate with Proton

```bash
docker exec -it proton-drive-sync proton-drive-sync auth
```

Follow the prompts to log in with your Proton account.

### 4. Configure sync mappings

Access the dashboard at `https://protondrive.<domain>` (Tailscale required) to configure
which local directories map to which ProtonDrive folders.

Recommended mappings:
- `/data/paperless-documents` → `Backups/paperless-documents`
- `/data/backups` → `Backups/nexus-backups`

## Notes

- This is a secondary off-site backup alongside Cloudflare R2
- ProtonDrive sync is push-only; restores should use Backrest from R2
- Dashboard is admin-only via Tailscale auth
