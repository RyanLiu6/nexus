# Dashboard (Homepage)

A modern, fully static, fast, secure, fully proxied, highly customizable application dashboard using [Homepage](https://gethomepage.dev/).

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

## Configuration Files

| File | Purpose |
|------|---------|
| `config/services.yaml` | Service cards with icons and links |
| `config/bookmarks.yaml` | Quick link bookmarks |
| `config/settings.yaml` | Theme, title, background |
| `config/widgets.yaml` | Status and info widgets |

---

## Troubleshooting

### Widget Not Loading

**Symptoms:** Widget shows loading spinner or error

**Solutions:**
1. Check dashboard container:
   ```bash
   docker ps | grep dashboard
   docker compose logs dashboard --tail=50
   ```

2. Verify service URL in `services.yaml`

3. Test service connectivity:
   ```bash
   curl -k https://service.yourdomain.com
   ```

4. Check browser console for JavaScript errors (F12)

### Service Icons Missing

**Symptoms:** Generic icon displayed

**Solutions:**
1. Check icon files exist:
   ```bash
   ls config/icons/
   ```

2. Verify icon path in `services.yaml`:
   ```yaml
   - Service Name:
       icon: service-name.png  # Must exist in icons folder
   ```

3. Use built-in icons from [Dashboard Icons](https://github.com/walkxcode/dashboard-icons)

### Configuration Not Updating

**Symptoms:** Changes not reflected

**Solutions:**
1. Restart dashboard:
   ```bash
   docker compose restart dashboard
   ```

2. Check file permissions:
   ```bash
   ls -la config/
   ```

3. Clear browser cache (Ctrl+Shift+R / Cmd+Shift+R)

4. Verify YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config/services.yaml'))"
   ```

---

## Customization

### Settings Example

```yaml
# config/settings.yaml
title: My Homelab
background: images/background.jpg
layout:
  style: columns
  columns: 3
```

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
    - Traefik:
        href: https://traefik.yourdomain.com
        icon: traefik.png
```

---

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Widget errors | Service offline | Start service container |
| No icons | Missing files | Add icons to config/icons/ |
| Not updating | Need restart | Restart dashboard container |
| CORS errors | Wrong origin | Check service CORS config |
| Slow loading | Network issue | Check proxy network |
