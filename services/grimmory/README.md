# Grimmory

Grimmory is a self-hosted book library manager for organizing and reading your ebook collection. It supports metadata fetching, reading progress tracking, device sync (Kobo, OPDS), and a bookdrop directory for importing new books. Grimmory is an independent community fork of Booklore.

## Features

- **Book Cataloguing** - Organize books by author, series, genre, and custom metadata
- **Metadata Fetching** - Automatically fetch covers, descriptions, and details from online sources
- **Reading Progress** - Track reading progress across your library
- **Bookdrop** - Drop ebooks into a folder for automatic import into the library
- **Multi-format Support** - EPUB, PDF, CBZ, CBR, audiobooks (M4B, MP3), and more

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
# Grimmory
grimmory_mysql_user: grimmory
grimmory_mysql_password: "<mysql-password>"
grimmory_mysql_root_password: "<mysql-root-password>"
```

### 3. Deploy

```bash
nexus deploy grimmory
# or
nexus deploy home
```

### Access

- **URL:** `https://grimmory.${NEXUS_DOMAIN}`
- **Auth:** Tailscale + tailscale-access (admins)

## Data Storage

Grimmory stores data under `${NEXUS_DATA_DIRECTORY}/Config/grimmory/`:

| Path | Contents |
|------|----------|
| `data/` | Application data and configuration |
| `books/` | Ebook library files |
| `bookdrop/` | Import directory (drop ebooks here for auto-import) |
| `mariadb/` | MariaDB database files |

## Backups

The built-in backup service covers the data directories. For a manual database backup:

```bash
docker exec grimmory-db mysqldump -u root -p${GRIMMORY_MYSQL_ROOT_PASSWORD} grimmory > grimmory-backup.sql
```

## Resources

- [GitHub Repository](https://github.com/grimmory-tools/grimmory)
