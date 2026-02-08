# Jotty <img src="https://github.com/fccview/jotty/raw/main/public/app-icons/logos/logo-animated.svg" width="24">

[Jotty](https://github.com/fccview/jotty) is a lightweight, self-hosted app for managing personal checklists and notes. All data is stored in simple Markdown and JSON files - no database required.

## Features

- **Checklists** - Task lists with drag & drop, progress bars, and Kanban boards
- **Rich Text Notes** - WYSIWYG editor with Markdown support
- **File-Based Storage** - Everything stored in plain files for easy backup
- **User Management** - Admin panel for creating and managing accounts
- **Encryption** - Optional PGP encryption for sensitive notes
- **Themes** - 14 built-in themes plus custom theme support

## Setup

### First Run

1. **Deploy the service:**
   ```bash
   invoke deploy
   ```

2. **Create initial admin user:**
   Navigate to `https://jotty.yourdomain.com/auth/setup` on first visit to create the admin account.

3. **Data directories are created automatically** at:
   - `${NEXUS_DATA_DIRECTORY}/jotty/data/` - Notes, checklists, users
   - `${NEXUS_DATA_DIRECTORY}/jotty/config/` - App configuration
   - `${NEXUS_DATA_DIRECTORY}/jotty/cache/` - Next.js cache

### Access

- **URL:** `https://jotty.${NEXUS_DOMAIN}`
- **Auth:** Tailscale + tailscale-access (admins group)

## Data Storage

Jotty stores all data in the `data/` directory:

| Path | Contents |
|------|----------|
| `data/checklists/` | Checklists as `.md` files |
| `data/notes/` | Notes as `.md` files |
| `data/users/` | User accounts and sessions |
| `data/sharing/` | Shared items |
| `data/encryption/` | PGP keys (if encryption enabled) |

## Backups

Since Jotty uses file-based storage, backups are simple:

```bash
# Backup all Jotty data
tar -czf jotty-backup-$(date +%Y%m%d).tar.gz -C ${NEXUS_DATA_DIRECTORY}/jotty .

# Restore from backup
tar -xzf jotty-backup-YYYYMMDD.tar.gz -C ${NEXUS_DATA_DIRECTORY}/jotty
```

Or use the built-in `backups` service which will include the Jotty data directory automatically.

## Configuration

Most configuration is done through the web UI. For advanced options, see the [official documentation](https://github.com/fccview/jotty/tree/main/howto).

### Environment Variables

Jotty supports additional environment variables for SSO, though the defaults work fine for most use cases:

- `NODE_ENV=production` - Already set
- `TZ` - Timezone (inherited from Nexus config)

For OIDC/SAML configuration, refer to the [Jotty SSO documentation](https://github.com/fccview/jotty/blob/main/howto/SSO.md).

## Troubleshooting

### Container won't start

Check permissions on data directories:
```bash
ls -la ${NEXUS_DATA_DIRECTORY}/jotty/
# Should be owned by 1000:1000
```

### Data not persisting

Ensure the volumes are mounted correctly:
```bash
docker inspect jotty | grep -A 10 '"Mounts"'
```

### View logs

```bash
docker logs jotty -f
```

## Resources

- [GitHub Repository](https://github.com/fccview/jotty)
- [Official Website](https://jotty.page)
- [Documentation](https://github.com/fccview/jotty/tree/main/howto)
