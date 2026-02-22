# Booklore

Booklore is a self-hosted book library manager for organizing and reading your ebook collection. It supports metadata fetching, reading progress tracking, and a bookdrop directory for importing new books.

## Features

- **Book Cataloguing** - Organize books by author, series, genre, and custom metadata
- **Metadata Fetching** - Automatically fetch covers, descriptions, and details from online sources
- **Reading Progress** - Track reading progress across your library
- **Bookdrop** - Drop ebooks into a folder for automatic import into the library
- **Multi-format Support** - EPUB, PDF, and other common ebook formats

## Setup

### 1. Generate Secrets

```bash
# MySQL user password
openssl rand -base64 32

# MySQL root password
openssl rand -base64 32
```

### 2. Configure Vault Variables

Edit the Ansible vault file:

```bash
ansible-vault edit ansible/vars/vault.yml
```

Add the secrets:

```yaml
# Booklore
booklore_mysql_user: booklore
booklore_mysql_password: "<mysql-password>"
booklore_mysql_root_password: "<mysql-root-password>"
```

### 3. Deploy

```bash
nexus deploy booklore
# or
nexus deploy home
```

### Access

- **URL:** `https://booklore.${NEXUS_DOMAIN}`
- **Auth:** Tailscale + tailscale-access (admins)

## Data Storage

Booklore stores data under `${NEXUS_DATA_DIRECTORY}/booklore/`:

| Path | Contents |
|------|----------|
| `data/` | Application data and configuration |
| `books/` | Ebook library files |
| `bookdrop/` | Import directory (drop ebooks here for auto-import) |
| `mariadb/` | MariaDB database files |

## Backups

The built-in backup service covers the data directories. For a manual database backup:

```bash
docker exec booklore-db mysqldump -u root -p${BOOKLORE_MYSQL_ROOT_PASSWORD} booklore > booklore-backup.sql
```

## Resources

- [GitHub Repository](https://github.com/booklore-app/booklore)
