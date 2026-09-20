# BookOrbit

BookOrbit is an open-source, self-hosted library and reading platform designed for managing and reading ebooks, audiobooks, and comics. It features reading progress tracking, two-way sync with Kobo and KOReader, OPDS catalog support, multi-user support with OIDC/SSO, reading statistics, and automatic metadata fetching.

## Features

- **Multi-Format Support** - EPUB, MOBI, AZW3, comics (CBZ, CBR, CB7), audiobooks (M4B, MP3), and more
- **Metadata Fetching** - Automatically fetch book covers, descriptions, and details
- **Reading Progress & Sync** - Two-way progress sync with Kobo and KOReader
- **OPDS Catalog** - Private OPDS feed for e-readers and mobile reading apps
- **Multi-User & Security** - Isolated user reading progress and statistics
- **Staging & Book Dock** - Built-in staging area for importing books

## Setup

### 1. Generate Secrets

```bash
# PostgreSQL user password
openssl rand -base64 32

# JWT secret
openssl rand -base64 32

# Setup bootstrap token (for initial /auth/setup admin creation)
openssl rand -base64 32
```

### 2. Configure Vault Variables

Edit the Ansible vault file:

```bash
ansible-vault edit ansible/vars/vault.yml
```

Add the secrets:

```yaml
# BookOrbit
bookorbit_postgres_user: "bookorbit"
bookorbit_postgres_password: "<postgres-password>"
bookorbit_postgres_db: "bookorbit"
bookorbit_jwt_secret: "<jwt-secret>"
bookorbit_setup_bootstrap_token: "<setup-bootstrap-token>"
```

### 3. Deploy

```bash
nexus deploy bookorbit
# or
nexus deploy home
```

### Access

- **URL:** `https://bookorbit.${NEXUS_DOMAIN}`
- **Auth:** Tailscale + tailscale-access (admins)
- **Initial Setup:** Navigate to `https://bookorbit.${NEXUS_DOMAIN}` to complete the initial admin setup using your `bookorbit_setup_bootstrap_token`.

## Data Storage

BookOrbit stores configuration, app state, and database files under `${NEXUS_DATA_DIRECTORY}/Config/bookorbit/`:

| Path | Contents |
|------|----------|
| `data/` | Application data, cache, and staging book dock |
| `postgres/` | PostgreSQL database files (with pgvector extension) |

Book files are stored at `${BOOKORBIT_BOOKS_DIRECTORY}` (configured via `nexus_userdata_directory/bookorbit` or fallback to `${NEXUS_DATA_DIRECTORY}/Config/bookorbit/books`).

## Backups

The built-in backup service covers the data directories. For a manual database backup:

```bash
docker exec bookorbit-db pg_dump -U ${BOOKORBIT_POSTGRES_USER} ${BOOKORBIT_POSTGRES_DB} > bookorbit-backup.sql
```

## Resources

- [BookOrbit Documentation](https://bookorbit.app)
- [GitHub Repository](https://github.com/bookorbit/bookorbit)
