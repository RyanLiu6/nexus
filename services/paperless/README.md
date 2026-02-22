# Paperless-ngx

Paperless-ngx is a document management system for scanning, indexing, and archiving physical documents. It provides OCR, full-text search, and automatic tagging to make your document archive searchable and organized.

## Features

- **OCR** - Automatically extract text from scanned documents
- **Full-text Search** - Search across all document content, not just filenames
- **Auto Tagging** - Automatic and manual tags, document types, and correspondents
- **Consumption Directory** - Drop files into a folder for automatic import and processing
- **Bulk Operations** - Merge, split, and manage documents in batch
- **REST API** - Full API for automation and integrations

## Setup

### 1. Generate Secrets

```bash
# PostgreSQL password
openssl rand -base64 32

# Django secret key
openssl rand -base64 50

# Admin password
openssl rand -base64 16
```

### 2. Configure Vault Variables

Edit the Ansible vault file:

```bash
ansible-vault edit ansible/vars/vault.yml
```

Add the secrets:

```yaml
# Paperless
paperless_postgres_user: paperless
paperless_postgres_password: "<postgres-password>"
paperless_postgres_db: paperless
paperless_secret_key: "<secret-key>"
paperless_admin_user: admin
paperless_admin_password: "<admin-password>"
```

### 3. Deploy

```bash
nexus deploy paperless
# or
nexus deploy home
```

### Access

- **URL:** `https://paperless.${NEXUS_DOMAIN}`
- **Auth:** Tailscale + tailscale-access (admins)

## Data Storage

Paperless stores data under `${NEXUS_DATA_DIRECTORY}/paperless/`:

| Path | Contents |
|------|----------|
| `data/` | Application data and classifier models |
| `media/` | Stored document files |
| `export/` | Document exports |
| `consume/` | Consumption directory (drop files here for auto-import) |
| `postgres/` | PostgreSQL database files |
| `redis/` | Redis cache data |

## Backups

The built-in backup service covers the data directories. For a manual database backup:

```bash
docker exec paperless-db pg_dump -U ${PAPERLESS_POSTGRES_USER} ${PAPERLESS_POSTGRES_DB} > paperless-backup.sql
```

## Resources

- [GitHub Repository](https://github.com/paperless-ngx/paperless-ngx)
- [Documentation](https://docs.paperless-ngx.com)
