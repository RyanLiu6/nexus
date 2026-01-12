# FoundryVTT Troubleshooting

## Common Issues

### Foundry Not Starting

**Symptoms**: Container exits immediately

**Solutions**:
1. Check logs: `docker logs foundryvtt`
2. Verify license key is valid
3. Check data directory permissions: `ls -la $NEXUS_ROOT_DIRECTORY/Foundry/data`
4. Ensure port 30000 is available

### License Issues

**Symptoms**: Invalid license or license expired

**Solutions**:
1. Update license key in `.env`
2. Restart container: `docker restart foundryvtt`
3. Check Foundry account status

### Cannot Access From Internet

**Symptoms**: Foundry works locally but not via domain

**Solutions**:
1. Verify Traefik labels in docker-compose.yml
2. Check Cloudflare DNS: `dig foundry.yourdomain.com`
3. Ensure port forwarding is configured
4. Check firewall rules

### Performance Issues - Slow Loading

**Symptoms**: High latency, slow asset loading

**Solutions**:
1. Enable hardware acceleration (if using GPU)
2. Check disk I/O: `iostat -x 1`
3. Limit active users/connections
4. Optimize images in Foundry

## Useful Commands

```bash
# View Foundry logs
docker logs foundryvtt -f

# Restart Foundry
docker restart foundryvtt

# Access Foundry console
docker exec -it foundryvtt sh

# Check container status
docker stats foundryvtt
```

## Configuration Files

- `services/foundryvtt/docker-compose.yml` - Container configuration
- `$NEXUS_ROOT_DIRECTORY/Foundry/data/` - Game data and worlds
- `.env` - License key and credentials

## Player Access

### Public Access (No Authelia)
To allow public access to Foundry (recommended for games):

```yaml
labels:
  # Remove authelia middleware
  # No authelia middleware applied
```

Players will access via:
- URL: `https://foundry.yourdomain.com`
- Use Foundry's built-in user authentication

### Authelia Protected Access
To require Authelia before Foundry:

```yaml
labels:
  - "traefik.http.routers.foundryvtt.middlewares=authelia@docker,security-headers@docker"
```

Players must:
1. Log in to Authelia
2. Access Foundry
3. Log in to Foundry with game credentials

## S3 / Cloud Storage

Foundry can use S3-compatible storage (Cloudflare R2, Wasabi, etc):

### Configure S3 in Foundry
1. Go to Foundry Admin → Configuration → Data
2. Configure S3 endpoint, bucket, and credentials
3. Create `s3.json` config file in data directory

### Example S3 Configuration
```json
{
  "accessKeyId": "your-access-key",
  "secretAccessKey": "your-secret-key",
  "endpoint": "https://s3.wasabisys.com",
  "bucket": "foundry-backups"
}
```

## Module Management

### Installing Modules
1. Access Foundry as admin
2. Navigate to Add-on Modules
3. Upload or install from library

### Troubleshooting Modules
- Clear Foundry cache
- Disable conflicting modules
- Check module compatibility with Foundry version

## Backup & Restore

### Backup Worlds
```bash
# Copy entire Foundry data directory
cp -r $NEXUS_ROOT_DIRECTORY/Foundry/data $NEXUS_BACKUP_DIRECTORY/foundry-$(date +%Y%m%d)
```

### Restore Worlds
```bash
# Stop container
docker stop foundryvtt

# Restore from backup
cp -r $NEXUS_BACKUP_DIRECTORY/foundry-20250111/* $NEXUS_ROOT_DIRECTORY/Foundry/data/

# Start container
docker start foundryvtt
```

## Performance Tuning

### Increase Memory Limit
```yaml
# In docker-compose.yml
services:
  foundryvtt:
    deploy:
      resources:
        limits:
          memory: 4G
```

### Enable Compression
Foundry Admin → Configuration → General:
- Enable: "Asset Caching"
- Enable: "Compress WebSockets"

## Security

1. **Use strong passwords**: For all user accounts
2. **Regular updates**: Keep Foundry updated
3. **Limit admin access**: Only give admin rights to trusted users
4. **Monitor logs**: Check for suspicious activity
5. **Backup regularly**: Back up worlds and modules

## Integration with Authelia Groups

### Gaming Group Access
Configure Authelia with `gaming` group:

```yaml
# services/auth/configuration.yml
access_control:
  rules:
    - domain: "foundry.yourdomain.com"
      policy: one_factor
      subject: "group:gaming"
```

### Player Management
Create Foundry users for your players:
1. Access Foundry as admin
2. Users & Access Management → Create User
3. Assign appropriate permissions per game

## Troubleshooting Common Errors

### "Connection Refused"
- Check port 30000
- Verify network configuration
- Check firewall rules

### "License Key Invalid"
- Verify key in `.env`
- Check Foundry account for subscription status
- Contact Foundry support

### "World Loading Error"
- Check world file permissions
- Verify world format compatibility
- Check available disk space
