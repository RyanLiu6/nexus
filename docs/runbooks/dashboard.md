# Dashboard Runbook

## Widget Not Loading

### Symptoms
- Service widget shows loading spinner
- No icons displayed
- Widget returns error message

### Troubleshooting Steps

1. **Check Dashboard service**
   ```bash
   docker ps | grep dashboard
   docker compose logs dashboard --tail=50
   ```

2. **Verify service configuration**
   - Check `services/dashboard/config/services.yaml`
   - Verify service URL is correct
   - Check API key if service requires authentication

3. **Test service connectivity**
   ```bash
   curl -k https://service.yourdomain.com
   curl -k https://service.yourdomain.com/api/status
   ```

4. **Check browser console**
   - Open browser DevTools (F12)
   - Look for JavaScript errors
   - Check for CORS errors

5. **Verify Traefik routing**
   - Visit `https://traefik.yourdomain.com/dashboard`
   - Check if service appears in routers

## Service Icons Missing

### Symptoms
- Generic icon displayed instead of service icon
- Icon shows as broken image

### Troubleshooting Steps

1. **Check icon files**
   ```bash
   ls services/dashboard/public/images/
   ```

2. **Verify icon path in config**
   - Check `services/dashboard/config/services.yaml`
   - Ensure icon filename is correct
   - Icon files should be in `public/images/`

3. **Correct icon format**
   - Icons should be PNG or SVG
   - Recommended size: 64x64 or 128x128 pixels
   - Filename should match service name

### Icon Configuration Example

```yaml
Media:
  - jellyfin:
      href: https://jellyfin.yourdomain.com
      description: Media server
      icon: jellyfin.png  # Must exist in public/images/
```

## Configuration Not Updating

### Symptoms
- Changes to services.yaml not reflected
- Added services don't appear
- Removed services still visible

### Troubleshooting Steps

1. **Regenerate dashboard config**
   ```bash
   ./scripts/generate-dashboard -p home
   ```

2. **Restart dashboard service**
   ```bash
   docker compose restart dashboard
   ```

3. **Check file permissions**
   ```bash
   ls -la services/dashboard/config/
   ```
   - Ensure files are readable
   - Check ownership

4. **Clear browser cache**
   - Hard refresh: Ctrl+Shift+R (Windows/Linux), Cmd+Shift+R (Mac)
   - Clear cache in browser settings

5. **Verify config file syntax**
   ```bash
   python -c "import yaml; yaml.safe_load(open('services/dashboard/config/services.yaml'))"
   ```

## Authentication Issues

### Symptoms
- Dashboard prompts for login unexpectedly
- Cannot log in
- Logout doesn't work

### Troubleshooting Steps

1. **Check Authelia integration**
   - Verify Traefik is routing through Authelia
   - Check if dashboard should bypass auth
   - Review middleware configuration

2. **Clear cookies**
   - Open browser DevTools → Application
   - Delete cookies for dashboard domain
   - Refresh page

3. **Check session timeout**
   - Review `services/dashboard/config/settings.yaml`
   - Verify session duration settings

4. **Test with different browser**
   - Login issues may be browser-specific
   - Try incognito/private mode

## Customization Issues

### Symptoms
- Background image not loading
- Title not updated
- Layout appears broken

### Troubleshooting Steps

1. **Check settings.yaml**
   - Review `services/dashboard/config/settings.yaml`
   - Verify YAML syntax is correct
   - Check paths to background images

2. **Verify bookmark configuration**
   - Check `services/dashboard/config/bookmarks.yaml`
   - Ensure URLs are valid
   - Test bookmarks manually

3. **Restart after changes**
   ```bash
   docker compose restart dashboard
   ```

### Settings Example

```yaml
title: My Homelab
background: images/background.jpg
layout:
  style: columns
  columns: 3
```

## Service Discovery

### Services Not Auto-Discovered

1. **Verify Traefik labels**
   - Service must have `traefik.enable=true` label
   - Must have `traefik.http.routers.*.rule` with `Host()`

2. **Run discovery script**
   ```bash
   ./scripts/generate-dashboard -p home
   ```

3. **Manual configuration**
   - Edit `services/dashboard/config/services.yaml`
   - Add service manually
   - Follow existing format

## Common Issues

| Issue | Cause | Solution |
|-------|--------|----------|
| Widget errors | Service offline | Start service container |
| No icons | Missing files | Add icons to public/images/ |
| Not updating | Need restart | Restart dashboard container |
| CORS errors | Wrong origin | Check service CORS config |
| Slow loading | Network issue | Check proxy network |
