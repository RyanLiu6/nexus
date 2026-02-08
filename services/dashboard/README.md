# Dashboard (Homepage) <img src="https://gethomepage.dev/images/icon.png" width="24">

A modern, fully static, fast, secure, fully proxied, highly customizable application dashboard using [Homepage](https://gethomepage.dev/).

## Features

- **Centralized Hub** - Access all your self-hosted services
- **Live Widgets** - Real-time status for Docker, Traefik, Jellyfin, and more
- **Fast & Static** - No database, pure YAML configuration
- **Secure** - Full integration with Tailscale authentication
- **Customizable** - Themes, layouts, and custom CSS/JS

## Setup

1. **Create `.env`** from sample.
2. **Edit configuration files** in `config/`:
   - `services.yaml` - Service definitions
   - `bookmarks.yaml` - Quick links
   - `settings.yaml` - Theme and layout
   - `widgets.yaml` - Status widgets
3. **Run:**
   ```bash
   docker compose up -d
   ```

## Access

- **URL:** `https://dashboard.${NEXUS_DOMAIN}` (or just `https://${NEXUS_DOMAIN}`)
- **Auth:** Tailscale + tailscale-access

## Data Storage

Dashboard configuration relies on YAML files in `${NEXUS_DATA_DIRECTORY}/Dashboard`:

| Path | Contents |
|------|----------|
| `config/services.yaml` | Service cards with icons and links |
| `config/bookmarks.yaml` | Quick link bookmarks |
| `config/settings.yaml` | Theme, title, background |
| `config/widgets.yaml` | Status and info widgets |
| `config/icons/` | Custom icons |
| `images/` | Background images |

## Backups

Back up the `config/` directory to save your layout and settings.

```bash
tar -czf dashboard-backup-$(date +%F).tar.gz -C ${NEXUS_DATA_DIRECTORY}/Dashboard config
```

## Configuration

### Services Example

```yaml
# config/services.yaml
- Media:
    - Jellyfin:
        href: https://jellyfin.yourdomain.com
        description: Media server
        icon: jellyfin.png
    - Plex:
        href: https://plex.yourdomain.com
        icon: plex.png

- Admin:
    - Grafana:
        href: https://grafana.yourdomain.com
        icon: grafana.png
```

### Settings Example

```yaml
# config/settings.yaml
title: My Homelab
background: images/background.jpg
layout:
  style: columns
  columns: 3
```

## Troubleshooting

### Widget Not Loading

**Symptoms:** Widget shows loading spinner or error

**Solutions:**
1. Check dashboard container logs: `docker logs dashboard`
2. Verify service URL in `services.yaml` is reachable from inside the container
3. Check browser console for JavaScript errors

### Service Icons Missing

**Symptoms:** Generic icon displayed

**Solutions:**
1. Check icon files exist in `config/icons/`
2. Verify icon filename in `services.yaml` matches exactly
3. Use built-in icons from [Dashboard Icons](https://github.com/walkxcode/dashboard-icons)

### Configuration Not Updating

**Symptoms:** Changes not reflected

**Solutions:**
1. Restart dashboard: `docker compose restart dashboard`
2. Clear browser cache
3. Verify YAML syntax

## Resources

- [Official Documentation](https://gethomepage.dev/)
- [Icon Repository](https://github.com/walkxcode/dashboard-icons)
- [Widget List](https://gethomepage.dev/latest/widgets/)
